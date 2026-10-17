"""Histórico das lojas (criadores): como os outros limiteds do mesmo criador se comportam na revenda.

Cache em data/criadores.json, renovado a cada `lojas.cache_dias` (7). Para não estourar chamadas,
só buscamos `lojas.max_por_execucao` criadores por execução (os que nunca vimos primeiro).
"""
import json
import logging
import os
import urllib.parse
from datetime import datetime

from . import collect
from .http import ApiError, AuthRequired
from .storage import iso

log = logging.getLogger("radar.lojas")


def cache_path(root):
    return os.path.join(root, "data", "criadores.json")


def load_cache(root):
    try:
        with open(cache_path(root), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_cache(root, cache):
    path = cache_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1, sort_keys=True)


def _median(vals):
    vals = sorted(vals)
    m = len(vals) // 2
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def compute_stats(items):
    """items: collectibles normalizados do criador. Devolve as métricas do contrato."""
    rets = []
    for it in items:
        price, low = it.get("price"), it.get("lowest_resale")
        if price and price > 0 and low:
            rets.append(low / price)
    return {
        "items_seen": len(items),
        "sold_out": sum(1 for it in items if it.get("units_remaining") == 0),
        "with_resale": len(rets),
        "median_retention": round(_median(rets), 3) if rets else None,
        "pct_above_price": round(sum(1 for r in rets if r > 1) / len(rets), 3) if rets else None,
    }


def is_stale(rec, now, days):
    if not rec or not rec.get("updated_at"):
        return True
    try:
        updated = datetime.fromisoformat(rec["updated_at"].replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now - updated).total_seconds() > days * 86400


def fetch_creator(client, cid, ctype, cfg, errors):
    """Busca os collectibles do criador (1-2 páginas, sem MaxPrice). None se a busca falhar."""
    pages = cfg.get("lojas", {}).get("max_paginas", 2)
    found, cursor = {}, ""
    for _ in range(pages):
        params = {"Category": 11, "Subcategory": 19, "SalesTypeFilter": 2, "CreatorTargetId": cid,
                  "CreatorType": ctype or "User", "SortType": 3, "Limit": 30}
        if cursor:
            params["Cursor"] = cursor
        url = collect.CATALOG_SEARCH + "?" + urllib.parse.urlencode(params)
        try:
            resp = client.get_json(url)
        except ApiError as e:
            if isinstance(e, AuthRequired) or not found:
                errors.append(f"loja {cid}: {e.status}")
                return None
            break  # página 2 falhou: usamos o que veio
        for raw in (resp or {}).get("data") or []:
            if raw.get("creatorTargetId") not in (None, cid):
                continue  # a busca ignorou o filtro: não contamos itens de outros criadores
            item = collect.normalize_catalog_item(raw, [], any_collectible=True)
            if item and item["asset_id"]:
                found[item["asset_id"]] = item
        cursor = (resp or {}).get("nextPageCursor")
        if not cursor:
            break
    return list(found.values())


def update(root, client, creators, now, cfg, errors):
    """creators: {creator_id: {"type": "User"|"Group", "name": str}}. Devolve o cache completo (chaves em texto)."""
    lj = cfg.get("lojas", {})
    cache = load_cache(root)
    todo = [(cid, info) for cid, info in creators.items()
            if cid is not None and is_stale(cache.get(str(cid)), now, lj.get("cache_dias", 7))]
    todo.sort(key=lambda x: (str(x[0]) in cache, str(x[0])))  # nunca vistos primeiro
    pend = len(todo)
    todo = todo[:lj.get("max_por_execucao", 15)]
    consecutive = 0
    changed = False
    for cid, info in todo:
        items = fetch_creator(client, cid, info.get("type"), cfg, errors)
        if items is None:
            consecutive += 1
            if consecutive >= 3:
                log.warning("lojas: 3 falhas seguidas, parando por hoje")
                break
            continue
        consecutive = 0
        rec = {"updated_at": iso(now), "name": info.get("name")}
        rec.update(compute_stats(items))
        cache[str(cid)] = rec
        changed = True
    if changed:
        save_cache(root, cache)
    log.info("lojas: %d consultadas de %d pendentes", len(todo), pend)
    return cache
