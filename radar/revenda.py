"""Compra na revenda: item já esgotado, compra no anúncio mais barato, venda depois da trava de 7 dias.

Contas (mesmas taxas do radar):
  custo          = menor anúncio × 1,11
  venda hoje     = menor entre RAP e média dos 10 anúncios mais baratos
  venda na saída = venda hoje × fator de 7 dias (mudança mediana do preço em 7 dias, da calibração)
  lucro          = venda na saída × 0,5 − custo
Exemplo: anúncio 200, venda hoje 500, fator 0,95 -> 475 × 0,5 = 237 − 222 = +15 (+7%).
Para margem ≥ 30% o anúncio precisa estar abaixo de ~35% do valor de venda, então é raro
(no backtest de 17/10, 2% dos itens). Nunca gera alerta: velocidade não se aplica a esgotados.
"""
import logging
import urllib.parse

from . import collect
from .analyze import calibration_for, calibration_reason, economics, rap_consistency, sale_reference, score
from .http import ApiError

log = logging.getLogger("radar.revenda")

QUERIES = [{"SortType": 2, "SortAggregation": 1}, {"SortType": 2, "SortAggregation": 3}]


def find_sold_out(client, cfg, errors):
    """Acessórios esgotados com anúncio de revenda dentro do limite de preço do perfil."""
    rv = cfg.get("revenda", {})
    found = {}
    for q in QUERIES:
        cursor = ""
        for _ in range(rv.get("max_pages_per_query", 3)):
            params = {"Category": 11, "Subcategory": 19, "SalesTypeFilter": 2,
                      "IncludeNotForSale": "true", "Limit": 120, **q}
            if cursor:
                params["Cursor"] = cursor
            try:
                resp = client.get_json(collect.CATALOG_SEARCH + "?" + urllib.parse.urlencode(params))
            except ApiError as e:
                errors.append(f"revenda: catálogo {e.status}")
                break
            for raw in (resp or {}).get("data") or []:
                it = collect.normalize_catalog_item(raw, cfg["categorias"])
                low = it and it.get("lowest_resale")
                if it and it.get("units_remaining") == 0 and low and low <= cfg["perfil"]["max_price"]:
                    found[it["asset_id"]] = it
            cursor = (resp or {}).get("nextPageCursor")
            if not cursor:
                break
    return sorted(found.values(), key=lambda i: i["lowest_resale"])


def classify(row, cfg):
    ca, ev = cfg["classes"]["comprar_agora"], cfg["classes"]["evitar"]
    m, v7, rc = row["net_margin"], row["volume_7d"], row["rap_consistent"]
    if row["rap"] is None or m is None:
        return "OBSERVAR", ["Sem RAP: não há base para estimar a venda."]
    if rc is False:
        return "EVITAR", [f"RAP não confiável ({row['rap']}): vendas recentes bem abaixo dele."]
    if v7 is not None and v7 < ev["min_volume_7d"]:
        return "EVITAR", [f"Liquidez baixa: {v7} vendas em 7 dias."]
    if m <= ev["max_net_margin"]:
        return "EVITAR", [f"Comprar a {row['price']} e vender por {row['sale_ref']:.0f} depois de 7 dias dá {m:+.0%}."]
    base = (f"Compra na revenda a {row['price']} (menor anúncio); venda esperada {row['sale_ref']:.0f} "
            f"depois da trava de 7 dias: lucro {row['net_profit']:+.0f} ({m:+.0%}).")
    if m >= ca["min_net_margin"] and v7 is not None and v7 >= ca["min_volume_7d"] and rc is True:
        return "COMPRAR-AGORA", [base, f"Liquidez: {v7} vendas em 7 dias."]
    return "OBSERVAR", [base]


def build(item, cfg, now, hold, lifts, avg_low=None):
    """Linha no mesmo formato do analyze, com tipo = "revenda"."""
    price = item["lowest_resale"]
    ref_today, src = sale_reference(item.get("rap"), avg_low if avg_low is not None else item.get("resale_avg_low"))
    ref = round(ref_today * hold, 2) if ref_today is not None else None
    cost, profit, margin = economics(price, ref, cfg)
    rc = rap_consistency(item.get("rap"), item.get("last_chart_price"), item.get("last_chart_date"), now, cfg,
                         item.get("chart_median_14d"), item.get("chart_points_14d"))
    row = dict(item)
    row.update({
        "tipo": "revenda", "price": price, "sale_ref": ref, "sale_ref_source": src, "fator_trava": hold,
        "cost": cost, "net_profit": profit, "net_margin": margin, "rap_consistent": rc,
        "velocity_per_hour": None, "velocity_note": "item esgotado", "eta_hours": None, "pct_sold": 100.0,
        "url": f"https://www.roblox.com/catalog/{item['asset_id']}", "creator_track": None,
        "retention": None, "change_7d": None, "trend": None, "spark": [],
        "calibracao": calibration_for(item, lifts), "break_even": round(cost / cfg["taxas"]["seller_share"]) if cost else None,
        "hold_days": 7,
    })
    cls, reasons = classify(row, cfg)
    cal = calibration_reason(row["calibracao"])
    if cal:
        reasons.append(cal)
    row.update({"class": cls, "reasons": reasons,
                "invalidators": ["Alguém anunciar mais barato, ou o RAP cair, antes de você comprar.",
                                 "Trava de até 7 dias: o preço pode cair até poder revender."],
                "data_quality": "ok" if rc else "rap_incoerente" if rc is False else "sem_rap"})
    row["score"] = score(row, cfg)
    return row


def run(client, cfg, now, hold, lifts, errors, use_listings=True):
    rv = cfg.get("revenda", {})
    if not rv.get("ativo", True):
        return []
    rows = []
    for item in find_sold_out(client, cfg, errors)[: rv.get("max_itens", 30)]:
        summary, st = collect.fetch_resale(client, item, now)
        if st == "auth_required":
            errors.append("revenda: histórico pediu login; parei")
            break
        if not summary:
            continue
        item.update(summary)
        if use_listings:
            lst, lst_st = collect.fetch_listings(client, item, cfg["coleta"].get("anuncios_media", 10))
            if lst:
                item.update(lst)
            use_listings = lst_st != "auth_required"
        if "resale_avg_n" not in item:
            # Sem a lista de anúncios: o menor anúncio vira "média de 1" (conservador: venda ≤ preço de compra).
            item["resale_avg_low"], item["resale_avg_n"] = item["lowest_resale"], 1
        rows.append(build(item, cfg, now, hold, lifts))
    thumbs = collect.fetch_thumbnails(client, [r["asset_id"] for r in rows], errors) if rows else {}
    for r in rows:
        r["thumbnail"] = thumbs.get(r["asset_id"])
    log.info("revenda: %d itens esgotados avaliados", len(rows))
    return rows
