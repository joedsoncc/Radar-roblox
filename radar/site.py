"""Gera docs/data.json (lido pelo PWA) e data/lista-de-compra.md."""
import json
import os

from .analyze import fmt_eta
from .notify import DISCLAIMER

PUBLIC_FIELDS = [
    "asset_id", "name", "creator_name", "creator_verified", "category", "url", "thumbnail",
    "price", "total_quantity", "units_remaining", "pct_sold", "rap", "lowest_resale",
    "volume_7d", "volume_30d", "last_chart_price", "last_chart_date", "chart_median_14d", "rap_consistent",
    "cost", "net_profit", "net_margin", "velocity_per_hour", "velocity_note", "eta_hours", "score", "class",
    "reasons", "invalidators", "data_quality",
    "creator_track", "retention", "change_7d", "trend", "spark",
]


def build_payload(items, cfg, generated_at, run_status, status_note, snapshots_count):
    p, t = cfg["perfil"], cfg["taxas"]
    return {
        "generated_at": generated_at,
        "run_status": run_status,
        "status_note": status_note,
        "snapshots_count": snapshots_count,
        "disclaimer": DISCLAIMER + " Lucro líquido = RAP × 0,5 − preço × 1,11.",
        "config": {"max_price": p["max_price"], "max_remaining": p["max_remaining"],
                   "fee_multiplier": t["fee_multiplier"], "seller_share": t["seller_share"]},
        "categories": [{"key": c["key"], "label": c["label"], "asset_type_ids": c["asset_type_ids"]}
                       for c in cfg["categorias"]],
        "items": [{k: it.get(k) for k in PUBLIC_FIELDS} for it in items],
    }


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _n(v, fmt="{:.0f}"):
    return "—" if v is None else fmt.format(v)


def buy_list_md(payload):
    lines = [f"# Lista de compra — {payload['generated_at']}", "",
             f"Status da coleta: **{payload['run_status']}**. {payload['status_note'] or ''}".strip(), "",
             f"> {payload['disclaimer']}", ""]
    for cat in payload["categories"]:
        rows = [i for i in payload["items"] if i["category"] == cat["key"]]
        lines.append(f"## {cat['label']} ({len(rows)})")
        lines.append("")
        if not rows:
            lines += ["Nenhum item dentro dos filtros nesta coleta.", ""]
            continue
        lines.append("| Classe | Item | Preço | Restantes | RAP | Lucro líq. | ETA | Motivo | O que invalidaria |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for i in rows:
            name = (i["name"] or "").replace("|", "/")
            lines.append(
                f"| {i['class']} | [{name}]({i['url']}) | {_n(i['price'])} | "
                f"{_n(i['units_remaining'])}/{_n(i['total_quantity'])} | {_n(i['rap'])} | "
                f"{_n(i['net_profit'], '{:+.0f}')} ({_n(i['net_margin'] * 100 if i['net_margin'] is not None else None, '{:+.0f}%')}) | "
                f"{fmt_eta(i['eta_hours']) if i['eta_hours'] is not None else '—'} | "
                f"{' '.join(i['reasons']).replace('|', '/')} | {' '.join(i['invalidators']).replace('|', '/')} |")
        lines.append("")
    return "\n".join(lines)


def write_site(root, payload):
    write_json(os.path.join(root, "docs", "data.json"), payload)
    write_json(os.path.join(root, "data", "latest.json"), payload)
    with open(os.path.join(root, "data", "lista-de-compra.md"), "w", encoding="utf-8") as f:
        f.write(buy_list_md(payload))
