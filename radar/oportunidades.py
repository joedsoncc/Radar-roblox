"""Só o que pode dar lucro alto vai para o site, a lista de compra e os alertas (decisão do Jhow, 18/10).

Entra: COMPRAR-AGORA ou OBSERVAR com lucro líquido projetado acima de 100% do valor gasto
(config oportunidades.min_net_margin = 1.0). Lucro% = (valor de venda × 0,5 − preço × 1,11) / (preço × 1,11).
Fica de fora (só em data/descartados.md): EVITAR, sem estimativa de lucro (sem RAP, RAP de venda
primária sem histórico da loja) e, se ligado, itens cuja faixa foi fraca no backtest (calibração).
Exemplo: preço 100 (custo 111): valor de venda 450 -> lucro +114 (+103%) entra; valor 400 -> +89 (+80%) fica fora.
"""
import os


def why_out(item, cfg):
    """Motivo do descarte, ou None se o item pode dar lucro."""
    o = cfg.get("oportunidades", {})
    if item.get("class") == "EVITAR":
        return "EVITAR"
    m = item.get("net_margin")
    if m is None:
        return "sem estimativa de lucro"
    if m <= o.get("min_net_margin", 0.0):
        return f"lucro projetado {m:+.0%} (precisa passar de {o.get('min_net_margin', 0.0):+.0%})"
    cal = item.get("calibracao")
    if o.get("excluir_calibracao_fraca", True) and cal and cal["score"] <= o.get("calibracao_fraca", 0.3):
        return "itens parecidos foram mal no backtest"
    return None


def split(items, cfg):
    shown, out = [], []
    for it in items:
        reason = why_out(it, cfg)
        if reason:
            out.append(dict(it, motivo_descarte=reason))
        else:
            shown.append(it)
    return shown, out


def descartados_md(out, generated_at):
    lines = [f"# Itens descartados ({generated_at})", "",
             "Não aparecem no site, na lista de compra nem nos alertas porque o lucro projetado não passa do corte.", "",
             "| Item | Classe | Preço | Lucro líq. | Motivo |", "|---|---|---|---|---|"]
    for i in out:
        m = i.get("net_margin")
        lines.append(f"| [{(i.get('name') or '').replace('|', '/')}]({i.get('url')}) | {i.get('class')} | "
                     f"{i.get('price')} | {'—' if m is None else f'{m:+.0%}'} | {i['motivo_descarte']} |")
    if not out:
        lines.append("| — | — | — | — | nenhum descarte |")
    return "\n".join(lines) + "\n"


def write_descartados(root, out, generated_at):
    path = os.path.join(root, "data", "descartados.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(descartados_md(out, generated_at))
