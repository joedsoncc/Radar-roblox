"""Backtest dos sinais com o histórico de revenda da coleta ampla.

Para cada item com histórico (data/amplo/revenda/*.json):
  compra   = preço original × 1,11 (quem comprou antes de esgotar)
  início   = primeiro dia do gráfico de revenda (≈ quando esgotou e a revenda abriu)
  venda    = mediana do preço nos dias 30 a 37 depois do início (passou a trava de até 30 dias)
  margem   = (venda × 0,5 − compra) / compra ; acerto = margem ≥ 30%
Itens com menos de 37 dias de revenda ainda não têm desfecho e ficam fora do backtest.
Itens cujo gráfico começa no limite de 180 dias da API ficam fora (o início foi cortado).

Para cada sinal (faixa de preço, estoque, categoria, criador verificado, favoritos por unidade,
prêmio e volume da 1ª semana de revenda) o relatório mostra quantos itens, a taxa de acerto,
a margem mediana e o "lift" (taxa da faixa ÷ taxa geral). Lift > 1 = sinal ajudou.
"""
import glob
import json
import os
from datetime import datetime, timedelta, timezone

LOCK_DAYS = 30
WINDOW_DAYS = 7
MAX_CHART_DAYS = 180
TARGET = 0.30

PRICE_BANDS = [(0, 50, "até 50"), (51, 100, "51 a 100"), (101, 250, "101 a 250"),
               (251, 500, "251 a 500"), (501, None, "acima de 500")]
STOCK_BANDS = [(0, 100, "até 100 un."), (101, 500, "101 a 500 un."), (501, 2000, "501 a 2.000 un."),
               (2001, 10000, "2.001 a 10.000 un."), (10001, None, "acima de 10.000 un.")]
PREMIUM_BANDS = [(0, 1.5, "< 1,5x o preço"), (1.5, 2.5, "1,5x a 2,5x"), (2.5, 4, "2,5x a 4x"), (4, None, "4x ou mais")]
VOLUME_BANDS = [(0, 19, "< 20 vendas"), (20, 99, "20 a 99 vendas"), (100, 499, "100 a 499 vendas"),
                (500, None, "500+ vendas")]
FAV_BANDS = [(0, 0.999, "< 1 favorito/un."), (1, 4.999, "1 a 5 favoritos/un."), (5, None, "5+ favoritos/un.")]

SIGNAL_LABELS = {
    "faixa_preco": "Preço original", "estoque": "Estoque total", "categoria": "Categoria",
    "criador_verificado": "Criador verificado", "favoritos_por_un": "Favoritos por unidade",
    "premio_1a_semana": "Preço da 1ª semana de revenda ÷ preço original (sinal pós-esgotar)",
    "volume_1a_semana": "Vendas na 1ª semana de revenda (sinal pós-esgotar)",
}
# Sinais que existem ANTES de comprar no preço original (os que o score pode usar).
PRE_BUY = ["faixa_preco", "estoque", "categoria", "criador_verificado", "favoritos_por_un"]


def band(v, bands):
    if v is None:
        return None
    for lo, hi, label in bands:
        if v >= lo and (hi is None or v <= hi):
            return label
    return None


def _date(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _series(pairs):
    out = []
    for d, v in pairs or []:
        d = _date(d)
        if d is not None and isinstance(v, (int, float)) and not isinstance(v, bool):
            out.append((d, v))
    return sorted(out)


def _median(vals):
    vals = sorted(vals)
    if not vals:
        return None
    m = len(vals) // 2
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def item_features(rec):
    it = rec.get("item") or {}
    stock = rec.get("asset_stock") or it.get("total_quantity")
    fav = it.get("favorite_count")
    return {
        "faixa_preco": band(rec.get("original_price") or it.get("price"), PRICE_BANDS),
        "estoque": band(stock, STOCK_BANDS),
        "categoria": it.get("category"),
        "criador_verificado": "sim" if it.get("creator_verified") else "não",
        "favoritos_por_un": band(fav / stock, FAV_BANDS) if fav is not None and stock else None,
    }


def evaluate(rec, now, cfg):
    """Desfecho de um item. Devolve dict com features e margem, ou None (sem dado/sem desfecho)."""
    t = cfg["taxas"]
    orig = rec.get("original_price") or (rec.get("item") or {}).get("price")
    prices = _series(rec.get("prices"))
    if not orig or orig <= 0 or not prices:
        return None
    start = prices[0][0]
    if start <= now - timedelta(days=MAX_CHART_DAYS - 5):
        return None  # gráfico cortado pela API: não sabemos quando esgotou
    feats = item_features(rec)
    curve = {}
    for label, d0 in (("+1d", 1), ("+7d", 7), ("+30d", 30)):
        if now >= start + timedelta(days=d0 + 3):
            win = [v for d, v in prices if start + timedelta(days=d0) <= d < start + timedelta(days=d0 + 3)]
            if win:
                curve[label] = round(_median(win) / orig, 3)
    w1 = [v for d, v in prices if d < start + timedelta(days=WINDOW_DAYS)]
    vols = _series(rec.get("volumes"))
    v1 = sum(v for d, v in vols if d < start + timedelta(days=WINDOW_DAYS))
    med1 = _median(w1)
    feats["premio_1a_semana"] = band(med1 / orig, PREMIUM_BANDS) if med1 else None
    feats["volume_1a_semana"] = band(v1, VOLUME_BANDS) if vols else None
    out = {"asset_id": (rec.get("item") or {}).get("asset_id"), "name": (rec.get("item") or {}).get("name"),
           "original_price": orig, "features": feats, "dias_revenda": (now - start).days,
           "curva": curve}
    if now < start + timedelta(days=LOCK_DAYS + WINDOW_DAYS):
        out["margem"] = None  # ainda sem desfecho
        return out
    lo, hi = start + timedelta(days=LOCK_DAYS), start + timedelta(days=LOCK_DAYS + WINDOW_DAYS)
    after = [v for d, v in prices if lo <= d < hi]
    if not after:
        # Sem venda na janela: usa o primeiro preço depois dela (venda demorou); sem nada = prejuízo total.
        later = [v for d, v in prices if d >= hi]
        after = later[:1]
    sell = _median(after) if after else 0
    cost = orig * t["fee_multiplier"]
    out["venda_dia30"] = sell
    out["margem"] = round((sell * t["seller_share"] - cost) / cost, 4)
    return out


def post_sellout_curve(results):
    """Preço mediano ÷ preço original em +1d/+7d/+30d da revenda, geral e por faixa de preço e estoque."""
    out = {}
    for key in (None, "faixa_preco", "estoque"):
        groups = {}
        for r in results:
            g = "todos" if key is None else r["features"].get(key)
            if g is None:
                continue
            for label, v in (r.get("curva") or {}).items():
                groups.setdefault(g, {}).setdefault(label, []).append(v)
        out[key or "geral"] = {g: {lab: {"mediana": round(_median(vs), 2), "n": len(vs)} for lab, vs in labs.items()}
                               for g, labs in groups.items()}
    return out


def summarize(results, min_n):
    done = [r for r in results if r.get("margem") is not None]
    hits = sum(1 for r in done if r["margem"] >= TARGET)
    base = hits / len(done) if done else None
    sinais = {}
    for key in SIGNAL_LABELS:
        groups = {}
        for r in done:
            b = r["features"].get(key)
            if b is not None:
                groups.setdefault(b, []).append(r["margem"])
        rows = []
        for b, ms in groups.items():
            rate = sum(1 for m in ms if m >= TARGET) / len(ms)
            rows.append({"faixa": b, "n": len(ms), "taxa": round(rate, 3),
                         "margem_mediana": round(_median(ms), 3),
                         "lift": round(rate / base, 2) if base else None,
                         "confiavel": len(ms) >= min_n})
        rows.sort(key=lambda x: -x["taxa"])
        sinais[key] = rows
    return {"n_backtest": len(done), "acertos": hits, "taxa_geral": round(base, 3) if base is not None else None,
            "sinais": sinais}


def load_records(root):
    recs = []
    for path in sorted(glob.glob(os.path.join(root, "data", "amplo", "revenda", "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                recs.append(json.load(f))
        except (OSError, ValueError):
            continue
    return recs


def velocity_watch(root, now):
    """Vendas por hora entre rodadas do catálogo amplo hoje (itens que ainda estão à venda)."""
    path = os.path.join(root, "data", "amplo", now.strftime("%Y-%m-%d") + ".jsonl")
    pts = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r.get("units_remaining"), (int, float)):
                    pts.setdefault(r["asset_id"], {})[r["ts"]] = (r["units_remaining"], r)
    except OSError:
        return []
    out = []
    for aid, by_ts in pts.items():
        seq = sorted(by_ts.items())
        if len(seq) < 2:
            continue
        (t0, (u0, _)), (t1, (u1, r)) = seq[0], seq[-1]
        hours = (_date(t1) - _date(t0)).total_seconds() / 3600
        if hours < 0.5 or u1 > u0 or u0 - u1 < 2 or u1 == 0:
            continue
        vel = (u0 - u1) / hours
        out.append({"asset_id": aid, "name": r.get("name"), "price": r.get("price"), "restantes": u1,
                    "vendas_por_hora": round(vel, 2), "esgota_em_h": round(u1 / vel, 1)})
    out.sort(key=lambda x: x["esgota_em_h"])
    return out[:25]


def run(root, cfg, now):
    min_n = (cfg.get("calibracao") or {}).get("min_itens_faixa", 20)
    recs = load_records(root)
    results = [r for r in (evaluate(x, now, cfg) for x in recs) if r]
    summary = summarize(results, min_n)
    summary.update({"generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "registros": len(recs),
                    "sem_desfecho": sum(1 for r in results if r.get("margem") is None),
                    "min_itens_faixa": min_n, "alvo_margem": TARGET,
                    "esgotando_agora": velocity_watch(root, now),
                    "curva_pos_esgote": post_sellout_curve(results)})
    best = sorted((r for r in results if r.get("margem") is not None), key=lambda r: -r["margem"])
    summary["melhores"] = [{k: r[k] for k in ("asset_id", "name", "original_price", "venda_dia30", "margem")}
                           for r in best[:10]]
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "calibracao.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(data_dir, "calibracao.md"), "w", encoding="utf-8") as f:
        f.write(render_md(summary))
    return summary


def pct(v):
    return "—" if v is None else f"{v * 100:.0f}%"


def render_md(s):
    L = [f"# Calibração do radar ({s['generated_at']})", "",
         "Backtest: quem comprou no preço original e vendeu depois da trava de 30 dias "
         "(mediana do gráfico nos dias 30 a 37 da revenda), com as taxas do radar "
         "(recebe 50%, custo ×1,11). Acerto = margem líquida ≥ 30%.", "",
         f"- Itens com histórico coletado: **{s['registros']}**",
         f"- Com desfecho (37+ dias de revenda, gráfico não cortado): **{s['n_backtest']}**",
         f"- Ainda sem desfecho: {s['sem_desfecho']}",
         f"- **Taxa geral de acerto: {pct(s['taxa_geral'])}** ({s['acertos']} de {s['n_backtest']})", "",
         f"Faixas com menos de {s['min_itens_faixa']} itens aparecem com ⚠ (amostra pequena, não use para decidir).", ""]
    for key, label in SIGNAL_LABELS.items():
        rows = s["sinais"].get(key) or []
        if not rows:
            continue
        L += [f"## {label}", "", "| Faixa | Itens | Acerto | Margem mediana | Lift |", "|---|---|---|---|---|"]
        for r in rows:
            warn = "" if r["confiavel"] else " ⚠"
            L.append(f"| {r['faixa']}{warn} | {r['n']} | {pct(r['taxa'])} | {r['margem_mediana'] * 100:+.0f}% | "
                     f"{'—' if r['lift'] is None else r['lift']} |")
        L.append("")
    curve = s.get("curva_pos_esgote") or {}
    if curve.get("geral"):
        L += ["## Curva depois de esgotar (preço mediano ÷ preço original)", "",
              "Início = primeiro dia do gráfico de revenda (≈ quando esgotou). Inclui itens ainda sem desfecho.", "",
              "| Grupo | +1 dia | +7 dias | +30 dias |", "|---|---|---|---|"]
        def cell(c, lab):
            v = c.get(lab)
            return "—" if not v else f"{v['mediana']:.2f}x (n={v['n']})"
        for key in ("geral", "faixa_preco", "estoque"):
            for g, c in sorted((curve.get(key) or {}).items()):
                L.append(f"| {g} | {cell(c, '+1d')} | {cell(c, '+7d')} | {cell(c, '+30d')} |")
        L.append("")
    if s.get("melhores"):
        L += ["## Melhores desfechos", "", "| Item | Preço | Venda dia 30 | Margem |", "|---|---|---|---|"]
        for r in s["melhores"]:
            L.append(f"| [{r['name']}](https://www.roblox.com/catalog/{r['asset_id']}) | {r['original_price']} | "
                     f"{r['venda_dia30']:.0f} | {r['margem'] * 100:+.0f}% |")
        L.append("")
    if s.get("esgotando_agora"):
        L += ["## Esgotando agora (velocidade medida entre rodadas de hoje)", "",
              "| Item | Preço | Restam | Vendas/h | Esgota em |", "|---|---|---|---|---|"]
        for r in s["esgotando_agora"]:
            L.append(f"| [{r['name']}](https://www.roblox.com/catalog/{r['asset_id']}) | {r['price']} | {r['restantes']} | "
                     f"{r['vendas_por_hora']} | ~{r['esgota_em_h']} h |")
        L.append("")
    L += ["> Passado não garante futuro. Lift só vale com amostra grande; um dia de coleta é ponto de partida.", ""]
    return "\n".join(L)


def load_lifts(root):
    """{sinal: {faixa: lift}} só das faixas confiáveis e dos sinais anteriores à compra."""
    try:
        with open(os.path.join(root, "data", "calibracao.json"), encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for key in PRE_BUY:
        for r in (s.get("sinais") or {}).get(key) or []:
            if r.get("confiavel") and r.get("lift") is not None:
                out.setdefault(key, {})[r["faixa"]] = {"lift": r["lift"], "taxa": r["taxa"], "n": r["n"]}
    return out
