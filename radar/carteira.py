"""Carteira: acompanha os itens que o Jhow comprou (ou quer acompanhar) e gera docs/carteira.json.

Entrada: carteira.json na raiz. Histórico: data/carteira/<asset_id>.jsonl (uma linha por execução).
Nada é inventado: sem RAP (API pediu login, falha) os campos de valor ficam null e o motivo vai em status_note.
"""
import json
import logging
import os
from datetime import date

from . import collect
from .analyze import sale_reference, trend_for, window_change
from .site import write_json
from .storage import iso

log = logging.getLogger("radar.carteira")

TRACKED_MAX = 500  # linhas do histórico próprio enviadas ao site


def carteira_path(root):
    return os.path.join(root, "carteira.json")


def load_carteira(root):
    """Lê carteira.json. Arquivo ausente = carteira vazia; JSON quebrado levanta ValueError."""
    try:
        with open(carteira_path(root), encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"itens": []}
    if not isinstance(data, dict) or not isinstance(data.get("itens", []), list):
        raise ValueError("carteira.json deve ter o formato {\"itens\": [...]}")
    data.setdefault("itens", [])
    return data


def save_carteira(root, data):
    tmp = carteira_path(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, carteira_path(root))


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def group_lots(entries):
    """{asset_id: [lotes]} na ordem do arquivo. Entradas inválidas são ignoradas."""
    out = {}
    for e in entries:
        aid = _int(e.get("asset_id")) if isinstance(e, dict) else None
        if aid is None:
            continue
        paid = e.get("preco_pago")
        qty = _int(e.get("quantidade")) or 1
        out.setdefault(aid, []).append({
            "preco_pago": paid if isinstance(paid, (int, float)) and not isinstance(paid, bool) else None,
            "quantidade": max(qty, 1),
            "comprado_em": e.get("comprado_em"),
            "nota": e.get("nota") or "",
        })
    return out


def _history_path(root, aid):
    return os.path.join(root, "data", "carteira", f"{aid}.jsonl")


def append_history(root, aid, row):
    path = _history_path(root, aid)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_history(root, aid):
    rows = []
    try:
        with open(_history_path(root, aid), encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return rows


def _r(x, nd=2):
    """Arredonda; 195.0 vira 195 para o JSON ficar limpo."""
    if x is None:
        return None
    x = round(x, nd)
    return int(x) if x == int(x) else x


def compute_item(aid, lots, detail, summary, history, thumb, now, cfg):
    """Monta o item do docs/carteira.json. detail/summary podem ser None (campos viram null)."""
    share = cfg["taxas"]["seller_share"]
    detail, summary = detail or {}, summary or {}
    quantity = sum(l["quantidade"] for l in lots)
    priced = [l for l in lots if l["preco_pago"] is not None]
    priced_qty = sum(l["quantidade"] for l in priced)
    paid_sum = sum(l["preco_pago"] * l["quantidade"] for l in priced)
    avg_paid = _r(paid_sum / priced_qty, 2) if priced_qty else None
    rap = summary.get("rap")
    original = detail.get("price")
    if "resale_avg_n" in summary:
        avg_low, avg_n = summary.get("resale_avg_low"), summary["resale_avg_n"]
    else:  # sem a lista de anúncios: o menor anúncio do catálogo vira "média de 1"
        low = detail.get("lowest_resale")
        avg_low, avg_n = (low, 1) if low else (None, 0)
    ref, ref_src = sale_reference(rap, avg_low)

    # Vendendo tudo pelo menor entre RAP e média dos anúncios mais baratos.
    # Com lotes mistos, só os lotes com preço entram na conta.
    held = priced_qty if priced_qty else quantity
    value_now = _r(ref * share * held, 2) if ref is not None else None
    cost_total = _r(paid_sum, 2) if priced_qty else None
    pnl = _r(value_now - cost_total, 2) if value_now is not None and cost_total is not None else None
    pnl_pct = round(pnl / cost_total, 4) if pnl is not None and cost_total else None

    dates = []
    for l in lots:
        try:
            dates.append(date.fromisoformat(l["comprado_em"]))
        except (TypeError, ValueError):
            pass
    days_held = max((now.date() - min(dates)).days, 0) if dates else None

    chart = summary.get("chart_series") or []
    ch7 = window_change(chart, now, 7)
    tracked = [[r.get("ts"), r.get("rap"), r.get("resale_avg_low", r.get("lowest_resale")), r.get("units_remaining")]
               for r in history][-TRACKED_MAX:]
    return {
        "asset_id": aid,
        "name": detail.get("name"), "creator_name": detail.get("creator_name"),
        "category": detail.get("category"),
        "url": f"https://www.roblox.com/catalog/{aid}", "thumbnail": thumb,
        "lots": lots, "quantity": quantity,
        "original_price": original, "avg_paid": avg_paid,
        "units_remaining": detail.get("units_remaining"), "total_quantity": detail.get("total_quantity"),
        "is_off_sale": detail.get("is_off_sale") if detail else None,
        "rap": rap, "volume_7d": summary.get("volume_7d"),
        "resale_avg_low": avg_low, "resale_avg_n": avg_n, "sale_ref": ref, "sale_ref_source": ref_src,
        "value_now": value_now, "cost_total": cost_total, "pnl": pnl, "pnl_pct": pnl_pct,
        "breakeven_rap": _r(avg_paid / share, 2) if avg_paid is not None else None,
        "retention": round(rap / original, 4) if rap and original else None,
        "change_7d": ch7, "change_30d": window_change(chart, now, 30),
        "trend": trend_for(chart, ch7, now), "days_held": days_held,
        "series": {"chart": chart, "tracked": tracked},
    }


def compute_totals(items):
    """Soma só itens com preço pago e RAP conhecido; 'só acompanhar' e itens sem RAP ficam de fora."""
    counted = [i for i in items if i["pnl"] is not None]
    if not counted:
        return {"cost": None, "value_now": None, "pnl": None, "pnl_pct": None, "items_counted": 0}
    cost = _r(sum(i["cost_total"] for i in counted))
    value = _r(sum(i["value_now"] for i in counted))
    pnl = _r(value - cost)
    return {"cost": cost, "value_now": value, "pnl": pnl,
            "pnl_pct": round(pnl / cost, 4) if cost else None, "items_counted": len(counted)}


def run(root, client, now, cfg):
    """Atualiza docs/carteira.json. Devolve {"status", "note", "items"}; status: ok | auth_required | partial."""
    entries = load_carteira(root)["itens"]
    lots_by_id = group_lots(entries)
    errors, notes = [], []
    status = "ok"
    details = collect.fetch_details(client, list(lots_by_id), cfg, errors, any_collectible=True) if lots_by_id else {}
    thumbs = collect.fetch_thumbnails(client, list(lots_by_id), errors) if lots_by_id else {}
    items = []
    auth = False
    failed_resale = 0
    n_listings = cfg["coleta"].get("anuncios_media", 10)
    listings_auth = False
    for aid, lots in lots_by_id.items():
        detail = details.get(aid)
        summary = None
        if auth:
            pass  # a API pediu login: não insistimos nos outros itens
        else:
            summary, st = collect.fetch_resale(client, detail or {"asset_id": aid}, now)
            if st == "auth_required":
                auth = True
            elif st != "ok":
                failed_resale += 1
            elif n_listings and not listings_auth and detail:
                lst, lst_st = collect.fetch_listings(client, detail, n_listings)
                if lst:
                    summary.update(lst)
                listings_auth = lst_st == "auth_required"
        if detail or summary:
            append_history(root, aid, {
                "ts": iso(now), "price": (detail or {}).get("price"),
                "units_remaining": (detail or {}).get("units_remaining"),
                "total_quantity": (detail or {}).get("total_quantity"),
                "rap": (summary or {}).get("rap"), "lowest_resale": (detail or {}).get("lowest_resale"),
                "resale_avg_low": (summary or {}).get("resale_avg_low"),
                "volume_7d": (summary or {}).get("volume_7d"),
                "is_off_sale": (detail or {}).get("is_off_sale"),
            })
        items.append(compute_item(aid, lots, detail, summary, load_history(root, aid),
                                  thumbs.get(aid), now, cfg))
    missing = [str(i["asset_id"]) for i in items if i["name"] is None]
    if auth:
        status = "auth_required"
        notes.append("A API de revenda (resale-data) respondeu 401/403: exige login. RAP, valor e lucro ficam "
                     "vazios até voltar; nada foi estimado.")
    elif failed_resale:
        status = "partial"
        notes.append(f"{failed_resale} item(ns) sem dados de revenda nesta coleta (RAP vazio, nada estimado).")
    if missing:
        status = "partial" if status == "ok" else status
        notes.append("Sem detalhes do catálogo para: " + ", ".join(missing) + " (ID errado ou API fora).")
    elif errors:
        status = "partial" if status == "ok" else status
        notes.append("Erros: " + "; ".join(sorted(set(errors))) + ".")
    if listings_auth:
        notes.append("A lista de anúncios pediu login; o valor usa só o menor anúncio do catálogo.")
    no_price = sum(1 for i in items if i["avg_paid"] is None)
    if no_price:
        notes.append(f"{no_price} item(ns) só acompanhando (sem preço pago): fora dos totais.")
    note = " ".join(notes)
    payload = {"generated_at": iso(now), "status_note": note,
               "totals": compute_totals(items), "items": items}
    write_json(os.path.join(root, "docs", "carteira.json"), payload)
    log.info("carteira: %d itens, status=%s", len(items), status)
    return {"status": status, "note": note, "items": items}


def mark_error(root, note):
    """Falha inesperada: mantém os itens anteriores e só avisa em status_note."""
    path = os.path.join(root, "docs", "carteira.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {"generated_at": None, "totals": compute_totals([]), "items": []}
    data["status_note"] = note
    write_json(path, data)


def summary_line(res, aid):
    """Frase curta sobre um item (usada no comentário da issue)."""
    for i in res["items"]:
        if i["asset_id"] == aid:
            if i["name"] is None:
                return ("Não consegui ler os detalhes deste item no catálogo (ID errado ou API fora do ar); "
                        "o cadastro foi salvo mesmo assim.")
            rap = "sem RAP" if i["rap"] is None else f"RAP {i['rap']:.0f}"
            return f"**{i['name']}** — {rap}, restam {i['units_remaining'] if i['units_remaining'] is not None else '—'}."
    return ""
