"""Score e classes COMPRAR-AGORA / OBSERVAR / EVITAR.

Contas (UGC Limited):
  valor de venda  = menor entre RAP e média dos 10 anúncios mais baratos (sem anúncio: RAP)
  custo efetivo   = preço × fee_multiplier (1,11)
  valor recebido  = valor de venda × seller_share (0,5)
  lucro líquido   = valor de venda × 0,5 − preço × 1,11
  margem líquida  = lucro líquido / custo efetivo
Exemplo: preço 100, RAP 260, média dos anúncios 300 -> vale 260, recebe 130, custo 111, lucro 19 (+17%).
Com média dos anúncios 230 -> vale 230, recebe 115, lucro 4 (+4%).
"""
from datetime import date, datetime, timedelta

CLASS_RANK = {"EVITAR": 0, "OBSERVAR": 1, "COMPRAR-AGORA": 2}


def economics(price, rap, cfg):
    t = cfg["taxas"]
    if price is None or price <= 0:
        return None, None, None
    cost = round(price * t["fee_multiplier"], 2)
    if rap is None:
        return cost, None, None
    profit = round(rap * t["seller_share"] - cost, 2)
    return cost, profit, round(profit / cost, 4)


def sale_reference(rap, avg_low):
    """Valor de venda usado no lucro: o menor entre RAP e média dos anúncios mais baratos.

    Para vender, é preciso competir com os anúncios: se eles estão abaixo do RAP, o RAP
    é otimista. Sem RAP não estimamos nada (anúncio sem venda não é preço). Devolve (valor, fonte).
    """
    if rap is None:
        return None, None
    if avg_low is not None and avg_low < rap:
        return avg_low, "anuncios"
    return rap, "rap"


def ref_label(item):
    if item.get("sale_ref_source") == "anuncios":
        return f"Média dos {item.get('resale_avg_n')} menores anúncios ({item['sale_ref']:.0f})"
    return f"RAP {item['rap']}"


def rap_consistency(rap, last_price, last_date, now, cfg, median_14d=None, points_14d=None):
    """True/False quando há dado; None quando falta RAP ou gráfico.

    Confere o último preço E a mediana dos últimos 14 dias contra o RAP, para que
    uma única venda alta não faça um RAP inflado parecer coerente.
    """
    c = cfg["classes"]
    ratio = c["rap_consistency_ratio"]
    if rap is None or last_price is None:
        return None
    if last_price < ratio * rap:
        return False
    if median_14d is not None and median_14d < ratio * rap:
        return False
    if last_date:
        try:
            age = (now.date() - date.fromisoformat(last_date)).days
            if age > c["max_chart_age_days"]:
                return False
        except ValueError:
            return None
    if points_14d is not None and points_14d < c.get("min_chart_points", 3):
        return None  # poucos dias com venda: não dá para confirmar
    return True


def velocity(asset_id, history, now, cfg):
    """Unidades vendidas por hora entre snapshots (inclui o atual).

    Devolve (velocidade, nota). Velocidade None = não medida:
    - menos de N snapshots, ou intervalo total menor que min_velocity_span_hours;
    - estoque aumentou (reposição/volta à venda): suspeito, não medimos.
    Se o último intervalo (≥ span mínimo) não teve venda, a velocidade é 0 (parou de vender).
    """
    c = cfg["classes"]
    cut = now - timedelta(hours=c["velocity_window_hours"])
    by_ts = {}
    for r in history:
        if r.get("asset_id") == asset_id and isinstance(r.get("units_remaining"), (int, float)) and r["_ts"] >= cut:
            by_ts[r["_ts"]] = r["units_remaining"]
    pts = sorted(by_ts.items())
    if len(pts) < c["min_snapshots_velocity"]:
        return None, "poucos snapshots"
    min_span = c.get("min_velocity_span_hours", 1.5)
    hours = (pts[-1][0] - pts[0][0]).total_seconds() / 3600
    if hours < min_span:
        return None, "snapshots muito próximos"
    if any(b[1] > a[1] for a, b in zip(pts, pts[1:])):
        return None, "estoque aumentou (reposição ou volta à venda)"
    # Último intervalo com duração mínima: se não vendeu nada, parou.
    last_t, last_u = pts[-1]
    prev = [p for p in pts[:-1] if (last_t - p[0]).total_seconds() / 3600 >= min_span]
    if prev and prev[-1][1] == last_u:
        return 0.0, "sem vendas no último intervalo"
    sold = pts[0][1] - last_u
    if sold < c.get("min_units_sold_velocity", 2):
        return 0.0, "vendas insuficientes para medir"
    return round(sold / hours, 3), None


def score(item, cfg):
    w = cfg["score_pesos"]
    m = item["net_margin"]
    s_margin = 0 if m is None else max(0.0, min(m, 1.0))
    v7 = item["volume_7d"]
    s_liq = 0 if v7 is None else min(v7 / 200, 1.0)
    rc = item["rap_consistent"]
    s_cons = {True: 1.0, None: 0.3, False: 0.0}[rc]
    eta = item["eta_hours"]
    if item["velocity_per_hour"] is None:
        s_vel = 0.0
    elif eta is None:
        s_vel = 0.05
    elif eta <= 24:
        s_vel = 1.0
    elif eta <= 72:
        s_vel = 0.6
    elif eta <= 168:
        s_vel = 0.3
    else:
        s_vel = 0.1
    s_creator = 1.0 if item.get("creator_verified") else 0.4
    total = (w["margem"] * s_margin + w["liquidez"] * s_liq + w["consistencia"] * s_cons
             + w["velocidade"] * s_vel + w["criador"] * s_creator)
    return int(round(total))


def fmt_eta(h):
    if h is None:
        return "sem estimativa"
    return f"~{h:.0f} h" if h < 48 else f"~{h / 24:.1f} d"


def classify(item, cfg):
    ca = cfg["classes"]["comprar_agora"]
    ev = cfg["classes"]["evitar"]
    m, v7, rc = item["net_margin"], item["volume_7d"], item["rap_consistent"]
    vel, eta = item["velocity_per_hour"], item["eta_hours"]
    reasons, inval = [], []

    if item["rap"] is None:
        reasons.append("Sem RAP disponível: a API não devolveu histórico. Nada foi estimado.")
        inval.append("Quando o RAP aparecer, a classe será recalculada.")
        return "OBSERVAR", reasons, inval

    if rc is False:
        reasons.append(f"RAP não confiável: último preço do gráfico ({item['last_chart_price']}) "
                       f"abaixo de {cfg['classes']['rap_consistency_ratio']:.0%} do RAP ({item['rap']}) ou gráfico antigo.")
        inval.append("Vendas recentes perto do RAP tornariam o RAP confiável de novo.")
        return "EVITAR", reasons, inval

    if v7 is not None and v7 < ev["min_volume_7d"]:
        reasons.append(f"Liquidez baixa: só {v7} vendas em 7 dias; difícil revender.")
        inval.append(f"Volume 7d acima de {ev['min_volume_7d']} mudaria a avaliação.")
        return "EVITAR", reasons, inval

    if m is not None and m <= ev["max_net_margin"]:
        be = round(item["cost"] / cfg["taxas"]["seller_share"]) if item["cost"] else None
        reasons.append(f"{ref_label(item)} não cobre o custo: lucro líquido {item['net_profit']:+.0f} "
                       f"({m:+.0%}). Equilíbrio exige RAP e anúncios ≈ {be}.")
        if eta is not None and eta <= 24:
            reasons.append(f"Mas está esgotando rápido ({fmt_eta(eta)}): o RAP pode subir depois, sem garantia.")
            inval.append(f"RAP acima de {be} depois de esgotar viraria oportunidade; RAP parado perto do preço confirma o prejuízo.")
            return "OBSERVAR", reasons, inval
        inval.append(f"RAP e média dos anúncios acima de {be} com vendas consistentes.")
        return "EVITAR", reasons, inval

    ok = (m is not None and m >= ca["min_net_margin"]
          and v7 is not None and v7 >= ca["min_volume_7d"]
          and (rc is True or not ca["require_rap_consistent"])
          and (vel is not None or not ca["require_velocity"])
          and (eta is not None and eta <= ca["max_eta_hours"] if ca["require_velocity"] else True))
    if ok:
        reasons.append(f"Margem líquida {m:+.0%} (lucro ≈ {item['net_profit']:.0f} Robux, base: {ref_label(item)}) "
                       "com RAP coerente com o gráfico.")
        reasons.append(f"Liquidez: {v7} vendas em 7 dias. Esgota em {fmt_eta(eta)}.")
        inval.append(f"RAP ou média dos anúncios cair abaixo de {round(item['cost'] * (1 + ca['min_net_margin']) / cfg['taxas']['seller_share'])} (margem < {ca['min_net_margin']:.0%}).")
        inval.append("Último preço do gráfico cair abaixo de metade do RAP.")
        inval.append("Venda parar (estoque sem mudar entre snapshots) ou trava de 30 dias impedir a revenda a tempo.")
        return "COMPRAR-AGORA", reasons, inval

    if m is not None:
        reasons.append(f"Margem líquida {m:+.0%}, abaixo do critério de compra ({ca['min_net_margin']:.0%}) "
                       if m < ca["min_net_margin"] else f"Margem líquida {m:+.0%}. ")
    if v7 is not None and v7 < ca["min_volume_7d"]:
        reasons.append(f"Volume 7d {v7} abaixo de {ca['min_volume_7d']}.")
    if rc is None:
        reasons.append("Gráfico insuficiente para conferir o RAP (poucos dias com venda).")
    if vel is None:
        reasons.append(f"Velocidade de venda não medida ({item.get('velocity_note') or 'precisa de 2+ snapshots'}).")
    elif vel == 0:
        reasons.append(f"Vendas pararam ou estão lentas demais ({item.get('velocity_note')}).")
    elif eta is not None and eta > ca["max_eta_hours"]:
        reasons.append(f"Esgota devagar ({fmt_eta(eta)}).")
    inval.append("Cumprir todos os critérios de compra o promoveria; RAP caindo o rebaixaria para EVITAR.")
    return "OBSERVAR", [r.strip() for r in reasons if r.strip()], inval


def analyze(current, history, now, cfg):
    items = []
    for it in current:
        ref, ref_src = sale_reference(it.get("rap"), it.get("resale_avg_low"))
        cost, profit, margin = economics(it.get("price"), ref, cfg)
        vel, vel_note = velocity(it["asset_id"], history, now, cfg)
        rem = it.get("units_remaining")
        eta = round(rem / vel, 1) if vel and rem is not None and vel > 0 else None
        total = it.get("total_quantity")
        pct = round(100 * (1 - rem / total), 1) if total and rem is not None and total > 0 else None
        rc = rap_consistency(it.get("rap"), it.get("last_chart_price"), it.get("last_chart_date"), now, cfg,
                             it.get("chart_median_14d"), it.get("chart_points_14d"))
        row = dict(it)
        row.update({
            "url": f"https://www.roblox.com/catalog/{it['asset_id']}",
            "sale_ref": ref, "sale_ref_source": ref_src,
            "cost": cost, "net_profit": profit, "net_margin": margin,
            "velocity_per_hour": vel, "eta_hours": eta, "pct_sold": pct,
            "rap_consistent": rc, "velocity_note": vel_note,
        })
        cls, reasons, inval = classify(row, cfg)
        row["class"] = cls
        row["reasons"] = reasons
        row["invalidators"] = inval
        row["score"] = score(row, cfg)
        if row.get("rap") is None:
            row["data_quality"] = "sem_rap"
        elif rc is False:
            row["data_quality"] = "rap_incoerente"
        elif vel is None:
            row["data_quality"] = "sem_velocidade"
        else:
            row["data_quality"] = "ok"
        items.append(row)
    items.sort(key=lambda r: (-CLASS_RANK[r["class"]], -r["score"]))
    return items


def alert_eligible(item, cfg):
    a = cfg["alertas"]
    return (item["class"] == "COMPRAR-AGORA"
            and item["units_remaining"] is not None and 0 < item["units_remaining"] < a["max_remaining"]
            and item["net_margin"] is not None and item["net_margin"] >= a["min_net_margin"]
            and item["volume_7d"] is not None and item["volume_7d"] >= a["min_volume_7d"]
            and (item["rap_consistent"] is True or not a["require_rap_consistent"])
            and ((item["velocity_per_hour"] or 0) > 0 or not a["require_velocity"]))
