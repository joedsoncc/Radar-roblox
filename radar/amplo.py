"""Coleta ampla para calibrar o radar (só leitura, sem login).

Cada rodada:
1. Varre o catálogo de acessórios collectible em TODAS as faixas de preço, inclusive esgotados.
2. Grava uma linha por item em data/amplo/AAAA-MM-DD.jsonl (preço, estoque, menor anúncio).
3. Busca o histórico de revenda (resale-data: preço original, RAP, séries de preço e volume)
   dos esgotados e dos quase esgotando, no máximo uma vez por item por dia, em
   data/amplo/revenda/<asset_id>.json. Esse histórico é o que permite o backtest.

401/403 em qualquer histórico = paramos as chamadas de histórico da rodada (sem contorno).
"""
import json
import logging
import os
import time
import urllib.parse

from . import collect
from .http import ApiError, AuthRequired
from .storage import iso

log = logging.getLogger("radar.amplo")

ROW_FIELDS = ["ts", "asset_id", "collectible_item_id", "name", "creator_name", "creator_id",
              "creator_type", "creator_verified", "category", "asset_type_id", "price",
              "total_quantity", "units_remaining", "lowest_resale", "is_off_sale", "favorite_count"]

DEFAULT_QUERIES = [
    {"nome": "mais vendidos do dia", "params": {"SortType": 2, "SortAggregation": 1}},
    {"nome": "mais vendidos da semana", "params": {"SortType": 2, "SortAggregation": 3}},
    {"nome": "mais vendidos de sempre", "params": {"SortType": 2, "SortAggregation": 5}},
    {"nome": "atualizados recentemente", "params": {"SortType": 3}},
    {"nome": "favoritos da semana", "params": {"SortType": 1, "SortAggregation": 3}},
    {"nome": "favoritos de sempre", "params": {"SortType": 1, "SortAggregation": 5}},
    {"nome": "mais baratos", "params": {"SortType": 4}},
    {"nome": "mais caros", "params": {"SortType": 5}},
]


def amplo_cfg(cfg):
    a = dict({"max_pages_per_query": 10, "max_resale_lookups": 300, "resale_time_budget_s": 420,
              "quase_esgotado_un": 100, "quase_esgotado_frac": 0.2, "queries": DEFAULT_QUERIES},
             **(cfg.get("amplo") or {}))
    return a


def search_all(client, cfg, errors):
    """Catálogo amplo: sem limite de preço e incluindo itens fora de venda (esgotados)."""
    a = amplo_cfg(cfg)
    found = {}
    limit = cfg["coleta"]["page_limit"]
    for q in a["queries"]:
        cursor, page = "", 0
        while page < a["max_pages_per_query"]:
            params = {"Category": 11, "Subcategory": 19, "SalesTypeFilter": 2,
                      "IncludeNotForSale": "true", "Limit": limit}
            params.update(q["params"])
            if cursor:
                params["Cursor"] = cursor
            try:
                resp = client.get_json(collect.CATALOG_SEARCH + "?" + urllib.parse.urlencode(params))
            except ApiError as e:
                if e.status == 400 and limit != 30:
                    limit = 30
                    continue
                errors.append(f"catálogo ({q['nome']}): {e.status}")
                break
            for raw in (resp or {}).get("data") or []:
                item = collect.normalize_catalog_item(raw, cfg["categorias"])
                if item and item["asset_id"]:
                    found[item["asset_id"]] = item
            page += 1
            cursor = (resp or {}).get("nextPageCursor")
            if not cursor:
                break
    return found


def wants_history(item, cfg):
    """Esgotados e quase esgotando (poucas unidades ou pouca fração restante)."""
    a = amplo_cfg(cfg)
    rem, total = item.get("units_remaining"), item.get("total_quantity")
    if rem is None:
        return False
    if rem == 0:
        return True
    if rem < a["quase_esgotado_un"]:
        return True
    return bool(total) and rem / total <= a["quase_esgotado_frac"]


def history_priority(item):
    # Esgotados primeiro (têm o desfecho), depois os com menos unidades.
    return (0 if item.get("units_remaining") == 0 else 1, item.get("units_remaining") or 0)


def fetch_raw_resale(client, item):
    """resale-data cru (precisamos de originalPrice e das séries inteiras). (dados, status)."""
    urls = []
    if item.get("collectible_item_id"):
        urls.append(collect.RESALE_NEW.format(cid=item["collectible_item_id"]))
    urls.append(collect.RESALE_OLD.format(aid=item["asset_id"]))
    for url in urls:
        try:
            data = client.get_json(url)
        except AuthRequired:
            return None, "auth_required"
        except ApiError:
            continue
        if isinstance(data, dict) and "recentAveragePrice" in data:
            return data, "ok"
    return None, "error"


def rodada(root, client, now, cfg):
    """Uma rodada de coleta ampla. Devolve um resumo."""
    a = amplo_cfg(cfg)
    errors = []
    base = os.path.join(root, "data", "amplo")
    rev_dir = os.path.join(base, "revenda")
    os.makedirs(rev_dir, exist_ok=True)

    found = search_all(client, cfg, errors)
    ts = iso(now)
    with open(os.path.join(base, now.strftime("%Y-%m-%d") + ".jsonl"), "a", encoding="utf-8") as f:
        for item in found.values():
            row = {k: item.get(k) for k in ROW_FIELDS}
            row["ts"] = ts
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    today = now.strftime("%Y-%m-%d")
    todo = []
    for item in sorted((i for i in found.values() if wants_history(i, cfg)), key=history_priority):
        path = os.path.join(rev_dir, f"{item['asset_id']}.json")
        try:
            with open(path, encoding="utf-8") as fh:
                if json.load(fh).get("fetched_at", "")[:10] == today:
                    continue
        except (OSError, ValueError):
            pass
        todo.append((item, path))

    st = {"ok": 0, "auth_required": 0, "error": 0, "pendentes": 0}
    started = time.monotonic()
    for n, (item, path) in enumerate(todo):
        if n >= a["max_resale_lookups"] or time.monotonic() - started > a["resale_time_budget_s"]:
            st["pendentes"] = len(todo) - n
            break
        data, s = fetch_raw_resale(client, item)
        st[s] += 1
        if s == "auth_required":
            st["pendentes"] = len(todo) - n - 1
            errors.append("histórico pediu login (401/403); parei as chamadas de histórico")
            break
        if data is None:
            continue
        rec = {"fetched_at": ts, "item": {k: item.get(k) for k in ROW_FIELDS if k != "ts"},
               "original_price": collect.num(data.get("originalPrice")),
               "asset_stock": collect.num(data.get("assetStock")),
               "sales": collect.num(data.get("sales")),
               "number_remaining": collect.num(data.get("numberRemaining")),
               "rap": collect.num(data.get("recentAveragePrice")),
               "prices": [[p.get("date"), p.get("value")] for p in data.get("priceDataPoints") or []],
               "volumes": [[p.get("date"), p.get("value")] for p in data.get("volumeDataPoints") or []]}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, separators=(",", ":"))

    summary = {"ts": ts, "catalogo": len(found), "com_historico_alvo": len(todo),
               "historico": st, "erros": sorted(set(errors)), "chamadas": client.calls}
    with open(os.path.join(base, "rodadas.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    log.info("rodada ampla: %s", summary)
    return summary
