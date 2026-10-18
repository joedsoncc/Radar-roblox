"""Cadastro da carteira por issue (formulário .github/ISSUE_TEMPLATE/carteira.yml).

O corpo da issue chega por variável de ambiente (nunca interpolado no workflow) e é tratado
como texto não confiável: só aceitamos o que passa na validação abaixo.
"""
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

from . import carteira

NO_RESPONSE = "_no response_"
CAMPOS = {  # chave -> prefixos do título da seção (sem acento, minúsculo)
    "acao": ("acao",),
    "item": ("item",),
    "preco_pago": ("preco",),
    "quantidade": ("quantidade",),
    "comprado_em": ("comprado",),
    "nota": ("nota",),
}


class CadastroError(ValueError):
    """Erro de validação com mensagem em português para comentar na issue."""


def _plain(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def parse_body(body):
    """Lê as seções '### Título' do corpo do issue form. '_No response_' vira ''."""
    sections, key, buf = {}, None, []

    def close():
        if key is not None and key not in sections:
            val = "\n".join(buf).strip()
            sections[key] = "" if val.lower() == NO_RESPONSE else val

    for line in (body or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith("### "):
            close()
            title = _plain(line[4:])
            key = next((k for k, pre in CAMPOS.items() if title.startswith(pre)), None)
            buf = []
        elif key is not None:
            buf.append(line)
    close()
    return sections


LINHAS_LIVRES = {  # "Chave: valor" no texto livre (link do site sem formulário, app do GitHub)
    "preco_pago": ("preco",),
    "quantidade": ("quantidade", "qtd"),
    "comprado_em": ("comprado", "data"),
    "nota": ("nota",),
}


def parse_free(title, body):
    """Texto livre: o app do GitHub abre a issue sem o formulário, então lemos o que der.

    Item = primeiro link do catálogo no corpo ou no título; senão um número de 6+ dígitos
    (IDs do Roblox são longos; preço e quantidade não chegam lá). Ação = Remover só se o
    texto começar com "remover"; o resto é Adicionar. Preço/quantidade/data vêm de linhas
    "Chave: valor"; o que faltar fica vazio (só acompanhar / 1 / hoje).
    """
    title = re.sub(r"^\s*\[carteira\]\s*", "", title or "", flags=re.I)
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    fields = {k: "" for k in CAMPOS}
    for line in body.split("\n"):
        if ":" not in line or re.search(r"https?://", line.split(":", 1)[0]):
            continue
        chave, valor = (x.strip() for x in line.split(":", 1))
        chave = _plain(chave)
        k = next((k for k, pre in LINHAS_LIVRES.items() if any(chave.startswith(p) for p in pre)), None)
        if k and not fields[k]:
            fields[k] = valor
    item = ""
    for texto in (body, title):
        m = re.search(r"\S*roblox\.com/\S*?(?:catalog|library)/\d+\S*", texto, re.I)
        if m:
            item = m.group(0)
            break
    if not item:
        for texto in (body, title):
            m = re.search(r"(?<![\d/])(\d{6,19})(?!\d)", texto)
            if m:
                item = m.group(1)
                break
    fields["item"] = item
    primeira = _plain(body.strip().split("\n", 1)[0] if body.strip() else title)
    fields["acao"] = "remover" if primeira.startswith("remover") or _plain(title).startswith("remover") else "adicionar"
    return fields


def read_request(title, body):
    """Usa as seções do formulário quando existem; senão, o texto livre."""
    fields = parse_body(body)
    if fields.get("acao") is None and fields.get("item") is None:
        return parse_free(title, body)
    return fields


def extract_asset_id(text):
    text = (text or "").strip()
    m = re.search(r"/(?:catalog|library)/(\d+)", text)
    if m:
        aid = int(m.group(1))
    elif re.fullmatch(r"\d+", text):
        aid = int(text)
    else:
        raise CadastroError("Não achei o item: cole o link do catálogo "
                            "(`https://www.roblox.com/catalog/123456789/Nome`) ou só o número do ID.")
    if aid <= 0 or aid >= 2 ** 63:
        raise CadastroError("O ID do item é inválido.")
    return aid


def today_br(now=None):
    """Data de hoje no horário de Brasília (UTC-3), para o padrão de 'comprado em'."""
    return ((now or datetime.now(timezone.utc)) - timedelta(hours=3)).date()


def validate(fields, now=None):
    """Devolve o pedido validado ou levanta CadastroError."""
    acao = _plain(fields.get("acao"))
    if acao not in ("adicionar", "remover"):
        raise CadastroError("O campo **Ação** deve ser *Adicionar* ou *Remover*.")
    req = {"acao": acao, "asset_id": extract_asset_id(fields.get("item"))}
    if acao == "remover":
        return req
    raw = (fields.get("preco_pago") or "").strip()
    if raw == "":
        preco = None
    elif re.fullmatch(r"\d+", raw):
        preco = int(raw)
    else:
        raise CadastroError("**Preço pago** deve ser um número inteiro de Robux, 0 ou mais "
                            "(sem vírgula, ponto ou texto), ou ficar vazio para só acompanhar.")
    raw = (fields.get("quantidade") or "").strip()
    if raw == "":
        qtd = 1
    elif re.fullmatch(r"\d+", raw) and 1 <= int(raw) <= 100:
        qtd = int(raw)
    else:
        raise CadastroError("**Quantidade** deve ser um número inteiro de 1 a 100.")
    hoje = today_br(now)
    raw = (fields.get("comprado_em") or "").strip()
    if raw == "":
        data = hoje
    else:
        try:
            data = date.fromisoformat(raw) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw) else None
        except ValueError:
            data = None
        if data is None:
            raise CadastroError("**Comprado em** deve ser uma data válida no formato AAAA-MM-DD (ex.: 2026-10-17).")
        if data > hoje:
            raise CadastroError("**Comprado em** não pode estar no futuro.")
    nota = " ".join((fields.get("nota") or "").split())[:200]
    req.update({"preco_pago": preco, "quantidade": qtd, "comprado_em": data.isoformat(), "nota": nota})
    return req


def apply(root, req):
    """Altera carteira.json e devolve a mensagem de sucesso. Levanta CadastroError sem alterar nada."""
    data = carteira.load_carteira(root)
    aid = req["asset_id"]
    if req["acao"] == "remover":
        keep = [e for e in data["itens"] if not (isinstance(e, dict) and carteira._int(e.get("asset_id")) == aid)]
        n = len(data["itens"]) - len(keep)
        if n == 0:
            raise CadastroError(f"O item `{aid}` não está na carteira; nada foi alterado.")
        data["itens"] = keep
        carteira.save_carteira(root, data)
        return f"Removido da carteira: item `{aid}` ({n} lote{'s' if n != 1 else ''})."
    lote = {"asset_id": aid, "preco_pago": req["preco_pago"], "quantidade": req["quantidade"],
            "comprado_em": req["comprado_em"], "nota": req["nota"]}
    # Item que estava só sendo acompanhado (sem preço) e agora ganhou preço: o lote é substituído,
    # assim dá para salvar só o link primeiro e informar o preço depois.
    vazio = next((n for n, e in enumerate(data["itens"]) if isinstance(e, dict)
                  and carteira._int(e.get("asset_id")) == aid and e.get("preco_pago") is None), None)
    if req["preco_pago"] is not None and vazio is not None:
        data["itens"][vazio] = lote
    elif req["preco_pago"] is None and any(isinstance(e, dict) and carteira._int(e.get("asset_id")) == aid
                                           for e in data["itens"]):
        raise CadastroError(f"O item `{aid}` já está na carteira. Para informar o preço pago, mande de novo com o preço.")
    else:
        data["itens"].append(lote)
    carteira.save_carteira(root, data)
    if req["preco_pago"] is None:
        quando = "Só acompanhando (sem preço pago, fica fora dos totais)"
    else:
        quando = f"{req['quantidade']} × {req['preco_pago']} Robux"
    return f"Adicionado à carteira: item `{aid}` — {quando}, data {req['comprado_em']}."


def cadastrar(root, body, now=None, title=""):
    """Devolve (ok, mensagem, asset_id|None). Nunca levanta por erro do usuário."""
    try:
        req = validate(read_request(title, body), now)
        return True, apply(root, req), req["asset_id"]
    except CadastroError as e:
        return False, f"Não consegui cadastrar: {e}\n\nNada foi alterado. Abra uma nova issue com o link do item (ex.: `https://www.roblox.com/catalog/123456789`).", None
    except ValueError as e:  # carteira.json ilegível
        return False, f"Não consegui cadastrar: {e}", None
