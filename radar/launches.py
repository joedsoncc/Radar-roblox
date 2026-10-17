"""Vigia lançamentos de limiteds da conta oficial da Roblox (acessórios, qualquer preço).

Roda a cada 10 min num workflow separado. Só grava arquivos (e gera commit) quando
aparece algo novo, para não encher o repositório de commits vazios.
"""
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta, timezone

from . import collect
from .http import ApiError
from .notify import DISCLAIMER, write_outbox
from .storage import iso

log = logging.getLogger("radar.launches")

ROBLOX_USER_ID = 1
LIMITED_TAGS = {"Limited", "LimitedUnique", "Collectible"}
ASSET_DETAILS = "https://economy.roblox.com/v2/assets/{aid}/details"
QUERIES = [{"SalesTypeFilter": 2}, {"SalesTypeFilter": 1}]


def _paths(root):
    return (os.path.join(root, "data", "launches.json"),
            os.path.join(root, "docs", "launches.json"))


def load_state(root):
    try:
        with open(_paths(root)[0], encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"seeded": False, "seen": {}, "items": []}


def is_roblox_limited(raw):
    return (raw.get("creatorTargetId") == ROBLOX_USER_ID
            and bool(LIMITED_TAGS & set(raw.get("itemRestrictions") or [])))


def search(client, cfg, errors):
    found = {}
    for q in QUERIES:
        params = {"Category": 11, "Subcategory": 19, "CreatorName": "Roblox", "SortType": 3, "Limit": 30}
        params.update(q)
        url = collect.CATALOG_SEARCH + "?" + urllib.parse.urlencode(params)
        try:
            resp = client.get_json(url)
        except ApiError as e:
            errors.append(f"catálogo: {e.status}")
            continue
        for raw in (resp or {}).get("data") or []:
            if not is_roblox_limited(raw):
                continue
            cat = collect.category_for(raw.get("assetType"), cfg["categorias"])
            if cat is None or not raw.get("id"):
                continue
            found[raw["id"]] = {
                "asset_id": raw["id"],
                "name": raw.get("name"),
                "category": cat,
                "price": collect.num(raw.get("price")),
                "total_quantity": collect.num(raw.get("totalQuantity")),
                "units_remaining": collect.num(raw.get("unitsAvailableForConsumption")),
                "off_sale": bool(raw.get("isOffSale")) or raw.get("priceStatus") == "Off Sale",
                "restrictions": sorted(LIMITED_TAGS & set(raw.get("itemRestrictions") or [])),
                "url": f"https://www.roblox.com/catalog/{raw['id']}",
            }
    return found


def created_at(client, asset_id):
    """Data de criação do item (None se a API falhar; nunca inventamos)."""
    try:
        d = client.get_json(ASSET_DETAILS.format(aid=asset_id))
        return collect._parse_date((d or {}).get("Created"))
    except ApiError:
        return None


def message(item, labels):
    stock = (f"{item['units_remaining']}/{item['total_quantity']} restantes"
             if item["total_quantity"] else "estoque não informado")
    price = f"{item['price']} Robux" if item["price"] is not None else "preço não informado"
    lines = [f"{labels.get(item['category'], item['category'])} · {price} · {stock}",
             "Fora de venda no momento" if item["off_sale"] else "À venda agora",
             item["url"], DISCLAIMER]
    if item.get("created_unknown"):
        lines.insert(1, "Data de criação não confirmada (pode ser item antigo que voltou à lista).")
    return {"title": f"Novo limited da Roblox: {item['name']}"[:120], "message": "\n".join(lines),
            "click": item["url"], "tags": ["rotating_light"], "priority": 5}


def run(root, client, cfg, now=None, max_age_days=7):
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    errors = []
    state = load_state(root)
    found = search(client, cfg, errors)
    if not found and errors:
        log.warning("catálogo indisponível: %s", "; ".join(errors))
        return {"status": "error", "new": [], "changed": False}

    seen = state.setdefault("seen", {})
    new_ids = [a for a in found if str(a) not in seen]
    if not state.get("seeded"):
        # 1ª execução: só registra o que já existe, sem avisar.
        for a in new_ids:
            seen[str(a)] = iso(now)
        state["seeded"] = True
        save(root, state, now)
        write_outbox(root, [], now, name="launch_outbox.json")
        log.info("base inicial: %d limiteds da Roblox registrados", len(new_ids))
        return {"status": "seeded", "new": [], "changed": True}

    labels = {c["key"]: c["label"] for c in cfg["categorias"]}
    new, messages = [], []
    for a in new_ids:
        item = found[a]
        seen[str(a)] = iso(now)
        created = created_at(client, a)
        if created is not None and created < now - timedelta(days=max_age_days):
            log.info("item antigo ignorado: %s (criado em %s)", a, created.date())
            continue
        item["created_unknown"] = created is None
        item["created_at"] = iso(created) if created else None
        item["found_at"] = iso(now)
        new.append(item)
        messages.append(message(item, labels))

    changed = bool(new_ids)
    if new:
        state["items"] = (new + state.get("items", []))[:30]
    if changed:
        save(root, state, now)
        write_outbox(root, messages, now, name="launch_outbox.json")
    log.info("lançamentos: %d novos de %d vistos agora", len(new), len(found))
    return {"status": "ok", "new": new, "changed": changed}


def save(root, state, now):
    data_path, site_path = _paths(root)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    os.makedirs(os.path.dirname(site_path), exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(site_path, "w", encoding="utf-8") as f:
        json.dump({"updated_at": iso(now), "items": state.get("items", [])}, f, ensure_ascii=False, indent=1)
