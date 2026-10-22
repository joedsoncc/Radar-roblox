"""Aparência dos UGC mais revendidos: miniaturas, descrição, cor, tamanho e tipo de acessório.

Base: coleta ampla (data/amplo/*.jsonl e data/amplo/revenda/*.json). Ranking = revendas nos
últimos 30 dias (soma do gráfico de volume do resale-data), só UGC pago já esgotado.
Compara os 50 mais revendidos com os outros do mesmo formato (1.001 a 3.000 cópias) e com o resto.

Coleta (precisa de internet, roda no GitHub Actions):
- thumbnails.roblox.com/v1/assets (420x420) -> data/visual/miniaturas/<asset_id>.png
- catalog.roblox.com/v1/catalog/items/details -> descrição
Cores e silhueta saem do PNG com Pillow (pip install pillow); sem Pillow, só nome e descrição.
Somente análise: não muda score nem alerta.
"""
import colorsys
import glob
import json
import logging
import os
import re
import statistics as st
import urllib.parse
from datetime import datetime, timedelta

from . import collect
from .http import ApiError

log = logging.getLogger("radar.visual")

TOP = 50

# Palavras do nome/descrição que dizem como o item é. Ordem = prioridade do "tipo".
GRUPOS = {
    "forma": {
        "valk": r"valk",
        "dominus": r"dominus",
        "chifres": r"horn",
        "coroa": r"crown|royal|corona|tiara",
        "fone": r"headphone",
        "fedora": r"fedora",
        "squid": r"squid",
        "asas": r"wing",
        "orelhas/gato": r"kitty|\bcat\b|ears|bunny|tabby",
        "aura": r"aura",
        "corrente": r"chain|necklace",
        "cabelo": r"hair",
        "halo": r"halo",
        "óculos/máscara": r"mask|shades|glasses",
    },
    "cor": {
        "preto": r"black|dark|shadow|void",
        "branco": r"white",
        "rosa": r"pink|sakura|cherry",
        "vermelho": r"\bred\b|crimson|infernal|blood",
        "azul": r"blue|navy|\bice\b",
        "roxo": r"purple|violet",
        "dourado": r"gold|aureus",
        "verde": r"green",
        "arco-íris": r"rainbow",
    },
    "efeito": {
        "sparkle": r"sparkle",
        "brilho/neon": r"glow|neon",
        "animado": r"animat",
        "8-bit": r"8-bit|8 bit|pixel",
        "estrela/galáxia": r"galaxy|\bstar",
        "fogo": r"fire|fiery|infernal|blaz|flame",
    },
    "tema": {
        "halloween": r"hallow|pumpkin|\bbat\b|vampire|demon|evil|devil|skull|😈",
        "clássico Roblox": r"valk|dominus|sparkle time|clockwork|fedora|korblox|8-bit|bombastic",
        "meme/fofo": r"doge|nyan|kitty|bitcoin|ice cream|bunny|\bcat\b",
        "combo": r"\+|horn.*crown|crown.*horn",
    },
}

# Faixas de matiz (graus) para nomear a cor dominante do PNG.
MATIZES = [(15, "vermelho"), (40, "laranja"), (70, "amarelo"), (165, "verde"), (200, "ciano"),
           (255, "azul"), (290, "roxo"), (335, "rosa"), (360, "vermelho")]


def _dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def tags(text):
    low = (text or "").lower()
    return {g: [k for k, pat in d.items() if re.search(pat, low)] for g, d in GRUPOS.items()}


def store_price(prices):
    """Preço de loja = mediana dos 3 primeiros dias do gráfico (a API nova não manda o original)."""
    pts = sorted((_dt(a), p) for a, p in (prices or []) if p)
    if not pts:
        return None
    first = pts[0][0]
    return st.median(p for d, p in pts if d <= first + timedelta(days=3))


def ranking(root):
    """Todos os UGC pagos esgotados com histórico, do mais revendido (30 d) para o menos."""
    rows = []
    for f in glob.glob(os.path.join(root, "data", "amplo", "revenda", "*.json")):
        with open(f, encoding="utf-8") as fh:
            r = json.load(fh)
        it = r.get("item") or {}
        if it.get("creator_id") == 1 or it.get("units_remaining") != 0:
            continue
        loja = store_price(r.get("prices"))
        if not loja:
            continue
        t = _dt(r["fetched_at"])
        vol = sum(v for a, v in (r.get("volumes") or []) if _dt(a) >= t - timedelta(days=30))
        rows.append({
            "asset_id": it["asset_id"], "name": it.get("name"), "creator_name": it.get("creator_name"),
            "category": it.get("category"), "total_quantity": it.get("total_quantity"),
            "favorite_count": it.get("favorite_count"), "loja": loja, "rap": r.get("rap"),
            "revendas_30d": vol,
        })
    rows.sort(key=lambda x: (-x["revendas_30d"], x["asset_id"]))
    for i, r in enumerate(rows):
        qty = r["total_quantity"] or 0
        r["grupo"] = "top" if i < TOP else ("mesmo_formato" if 1001 <= qty <= 3000 else "resto")
    return rows


def fetch_descriptions(client, asset_ids, errors):
    out = {}
    ids = list(asset_ids)
    for i in range(0, len(ids), 30):
        payload = {"items": [{"itemType": "Asset", "id": a} for a in ids[i:i + 30]]}
        try:
            resp = client.post_json(collect.CATALOG_DETAILS, payload)
        except ApiError as e:
            errors.append(f"descrições: {e.status}")
            continue
        for raw in (resp or {}).get("data") or []:
            if raw.get("id"):
                out[raw["id"]] = raw.get("description") or ""
    return out


def fetch_thumbs(client, asset_ids, folder, errors):
    """Baixa o PNG 420x420 de cada item que ainda não tem arquivo. Devolve quantos baixou."""
    os.makedirs(folder, exist_ok=True)
    falta = [a for a in asset_ids if not os.path.exists(os.path.join(folder, f"{a}.png"))]
    urls = {}
    for i in range(0, len(falta), 100):
        batch = falta[i:i + 100]
        url = collect.THUMBS + "?" + urllib.parse.urlencode(
            {"assetIds": ",".join(str(a) for a in batch), "size": "420x420",
             "format": "Png", "isCircular": "false"})
        try:
            resp = client.get_json(url)
        except ApiError as e:
            errors.append(f"miniaturas: {e.status}")
            continue
        for t in (resp or {}).get("data") or []:
            if t.get("state") == "Completed" and t.get("imageUrl"):
                urls[t["targetId"]] = t["imageUrl"]
    got = 0
    for aid, u in urls.items():
        try:
            data = client.get_bytes(u)
        except ApiError as e:
            errors.append(f"PNG {aid}: {e.status}")
            continue
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append(f"PNG {aid}: não é PNG")
            continue
        with open(os.path.join(folder, f"{aid}.png"), "wb") as fh:
            fh.write(data)
        got += 1
    return got


def hue_name(h, s, v):
    if v < 0.22:
        return "preto"
    if s < 0.18:
        return "branco" if v > 0.75 else "cinza"
    deg = h * 360
    return next(n for lim, n in MATIZES if deg <= lim)


def image_stats(path):
    """Cor dominante, fração da imagem ocupada (tamanho na miniatura), forma da silhueta, brilho."""
    from PIL import Image
    im = Image.open(path).convert("RGBA").resize((96, 96))
    px = [p for p in im.getdata()]
    W = H = 96
    solid = [(i % W, i // W, p) for i, p in enumerate(px) if p[3] > 40]
    if not solid:
        return None
    xs = [x for x, _, _ in solid]
    ys = [y for _, y, _ in solid]
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    count = {}
    sats, vals = [], []
    for _, _, (r, g, b, _) in solid:
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sats.append(ss)
        vals.append(vv)
        n = hue_name(hh, ss, vv)
        count[n] = count.get(n, 0) + 1
    ordem = sorted(count.items(), key=lambda kv: -kv[1])
    total = len(solid)
    return {
        "cor_1": ordem[0][0], "cor_2": ordem[1][0] if len(ordem) > 1 and ordem[1][1] / total >= 0.1 else None,
        "cores_fortes": sum(1 for _, c in ordem if c / total >= 0.1),
        "ocupa": round(total / (W * H), 3),
        "proporcao": round(w / h, 2),  # > 1,3 largo (chifres, coroa larga); < 0,8 alto (cabelo longo)
        "saturacao": round(st.median(sats), 2), "brilho": round(st.median(vals), 2),
    }


def contact_sheet(paths_labels, out, cols=10, cell=120):
    from PIL import Image, ImageDraw
    rows = (len(paths_labels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 14)), (40, 40, 46))
    d = ImageDraw.Draw(sheet)
    for i, (p, label) in enumerate(paths_labels):
        x, y = (i % cols) * cell, (i // cols) * (cell + 14)
        if p and os.path.exists(p):
            im = Image.open(p).convert("RGBA").resize((cell, cell))
            sheet.paste(im, (x, y), im)
        d.text((x + 2, y + cell), label[:20], fill=(230, 230, 230))
    sheet.save(out)


def _pct(rows, pred):
    return round(100 * sum(1 for r in rows if pred(r)) / len(rows)) if rows else None


def _med(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(st.median(vals), 2) if vals else None


def comparar(rows):
    """Tabela {linha: {grupo: valor}} com % por etiqueta e medianas das cores."""
    grupos = {g: [r for r in rows if r["grupo"] == g] for g in ("top", "mesmo_formato", "resto")}
    tab = {}
    for g, d in GRUPOS.items():
        for k in d:
            tab[f"{g}: {k}"] = {n: _pct(rs, lambda r, g=g, k=k: k in r["tags"][g]) for n, rs in grupos.items()}
    for n, rs in grupos.items():
        tab.setdefault("categoria hat", {})[n] = _pct(rs, lambda r: r["category"] == "hat")
    com_img = {n: [r for r in rs if r.get("img")] for n, rs in grupos.items()}
    if any(com_img.values()):
        cores = sorted({r["img"]["cor_1"] for rs in com_img.values() for r in rs})
        for c in cores:
            tab[f"miniatura: cor principal {c}"] = {
                n: _pct(rs, lambda r, c=c: r["img"]["cor_1"] == c) for n, rs in com_img.items()}
        tab["miniatura: 3+ cores fortes"] = {n: _pct(rs, lambda r: r["img"]["cores_fortes"] >= 3) for n, rs in com_img.items()}
        tab["miniatura: largo (proporção ≥ 1,3)"] = {n: _pct(rs, lambda r: r["img"]["proporcao"] >= 1.3) for n, rs in com_img.items()}
        tab["miniatura: alto (proporção ≤ 0,8)"] = {n: _pct(rs, lambda r: r["img"]["proporcao"] <= 0.8) for n, rs in com_img.items()}
        for key in ("ocupa", "saturacao", "brilho"):
            tab[f"miniatura: mediana {key}"] = {
                n: _med([r["img"] for r in rs], key) for n, rs in com_img.items()}
        tab["com miniatura"] = {n: len(rs) for n, rs in com_img.items()}
    tab["itens"] = {n: len(rs) for n, rs in grupos.items()}
    return tab


def run(root, client=None, errors=None):
    """Ranking + (com client) coleta de miniaturas/descrições + análise. Grava data/visual/."""
    errors = [] if errors is None else errors
    out = os.path.join(root, "data", "visual")
    folder = os.path.join(out, "miniaturas")
    os.makedirs(out, exist_ok=True)
    rows = ranking(root)
    desc_path = os.path.join(out, "descricoes.json")
    desc = {}
    if os.path.exists(desc_path):
        with open(desc_path, encoding="utf-8") as fh:
            desc = {int(k): v for k, v in json.load(fh).items()}
    if client is not None and rows:
        ids = [r["asset_id"] for r in rows]
        desc.update(fetch_descriptions(client, [a for a in ids if a not in desc], errors))
        with open(desc_path, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in sorted(desc.items())}, fh, ensure_ascii=False, indent=1)
        fetch_thumbs(client, ids, folder, errors)
    try:
        import PIL  # noqa: F401
        has_pil = True
    except ImportError:
        has_pil = False
    for r in rows:
        r["descricao"] = desc.get(r["asset_id"])
        r["tags"] = tags(r["name"])  # só o nome: descrição costuma ter palavra-chave de busca
        r["tags_descricao"] = tags(r["descricao"]) if r["descricao"] else None
        p = os.path.join(folder, f"{r['asset_id']}.png")
        r["img"] = image_stats(p) if has_pil and os.path.exists(p) else None
    tab = comparar(rows)
    with open(os.path.join(out, "visual.json"), "w", encoding="utf-8") as fh:
        json.dump({"comparacao": tab, "itens": rows, "erros": errors}, fh, ensure_ascii=False, indent=1)
    if has_pil and rows:
        for g, fname in (("top", "top50.png"), ("mesmo_formato", "mesmo-formato.png")):
            sel = [r for r in rows if r["grupo"] == g][:60]
            if not sel:
                continue
            contact_sheet([(os.path.join(folder, f"{r['asset_id']}.png"), r["name"] or "") for r in sel],
                          os.path.join(out, fname))
    return {"itens": len(rows), "comparacao": tab, "erros": errors}
