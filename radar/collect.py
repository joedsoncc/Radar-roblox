"""Coleta nas APIs públicas do Roblox.

Endpoints (somente leitura, sem login):
- catalog.roblox.com/v2/search/items/details  -> lista de collectibles de acessórios
- catalog.roblox.com/v1/catalog/items/details -> detalhes de itens já acompanhados (POST + CSRF)
- apis.roblox.com/marketplace-sales/v1/item/{collectibleItemId}/resale-data -> RAP e séries
- economy.roblox.com/v1/assets/{assetId}/resale-data -> alternativa para o mesmo dado
- thumbnails.roblox.com/v1/assets -> fotos
"""
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone

from .http import ApiError, AuthRequired

log = logging.getLogger("radar.collect")

CATALOG_SEARCH = "https://catalog.roblox.com/v2/search/items/details"
CATALOG_DETAILS = "https://catalog.roblox.com/v1/catalog/items/details"
RESALE_NEW = "https://apis.roblox.com/marketplace-sales/v1/item/{cid}/resale-data"
RESALE_OLD = "https://economy.roblox.com/v1/assets/{aid}/resale-data"
THUMBS = "https://thumbnails.roblox.com/v1/assets"


def num(v):
    """Só aceita número de verdade (bool e texto viram None)."""
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def category_for(asset_type_id, categories):
    for c in categories:
        if asset_type_id in c["asset_type_ids"]:
            return c["key"]
    return None


def normalize_catalog_item(raw, categories):
    """Converte um item do catálogo no nosso formato. Devolve None se não for acessório collectible."""
    if (raw.get("itemType") or "Asset") != "Asset":
        return None
    asset_type = raw.get("assetType")
    cat = category_for(asset_type, categories)
    if cat is None:
        return None
    restrictions = raw.get("itemRestrictions") or []
    if "Collectible" not in restrictions and not raw.get("collectibleItemId"):
        return None
    return {
        "asset_id": raw.get("id"),
        "collectible_item_id": raw.get("collectibleItemId"),
        "name": raw.get("name"),
        "creator_name": raw.get("creatorName"),
        "creator_id": raw.get("creatorTargetId"),
        "creator_type": raw.get("creatorType"),
        "creator_verified": bool(raw.get("creatorHasVerifiedBadge")),
        "asset_type_id": asset_type,
        "category": cat,
        "price": num(raw.get("price")),
        "total_quantity": num(raw.get("totalQuantity")),
        "units_remaining": num(raw.get("unitsAvailableForConsumption")),
        "lowest_resale": num(raw.get("lowestResalePrice")),
        "is_off_sale": bool(raw.get("isOffSale")) or raw.get("priceStatus") == "Off Sale",
        "favorite_count": num(raw.get("favoriteCount")),
    }


def search_catalog(client, cfg, errors):
    col = cfg["coleta"]
    found = {}
    limit = col["page_limit"]
    for q in col["catalog_queries"]:
        cursor = ""
        page = 0
        while page < col["max_pages_per_query"]:
            params = {"Category": 11, "Subcategory": 19, "SalesTypeFilter": 2,
                      "IncludeNotForSale": "false", "Limit": limit,
                      "MaxPrice": cfg["perfil"]["max_price"]}
            params.update(q["params"])
            if cursor:
                params["Cursor"] = cursor
            url = CATALOG_SEARCH + "?" + urllib.parse.urlencode(params)
            try:
                resp = client.get_json(url)
            except ApiError as e:
                if e.status == 400 and limit != 30:
                    log.info("catálogo recusou Limit=%s; tentando 30", limit)
                    limit = 30
                    continue
                errors.append(f"catálogo ({q['nome']}): {e.status}")
                log.warning("catálogo falhou em %s: %s", q["nome"], e)
                break
            for raw in (resp or {}).get("data") or []:
                item = normalize_catalog_item(raw, cfg["categorias"])
                if item and item["asset_id"]:
                    found[item["asset_id"]] = item
            page += 1
            cursor = (resp or {}).get("nextPageCursor")
            if not cursor:
                break
    return found


def fetch_details(client, asset_ids, cfg, errors):
    out = {}
    ids = list(asset_ids)
    for i in range(0, len(ids), 30):  # lotes de 30, como a comunidade relata
        batch = ids[i:i + 30]
        payload = {"items": [{"itemType": "Asset", "id": a} for a in batch]}
        try:
            resp = client.post_json(CATALOG_DETAILS, payload)
        except ApiError as e:
            errors.append(f"detalhes do catálogo: {e.status}")
            log.warning("detalhes falharam: %s", e)
            continue
        for raw in (resp or {}).get("data") or []:
            item = normalize_catalog_item(raw, cfg["categorias"])
            if item:
                out[item["asset_id"]] = item
    return out


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def summarize_resale(data, now):
    """Extrai RAP, volumes, último preço e mediana recente do gráfico.

    As séries podem vir da mais nova para a mais antiga e só têm dias com venda,
    então ordenamos por data em vez de confiar na posição. Campo ausente vira None.
    """
    rap = num(data.get("recentAveragePrice"))
    prices = []
    for p in data.get("priceDataPoints") or []:
        d, v = _parse_date(p.get("date")), num(p.get("value"))
        if d is not None and v is not None:
            prices.append((d, v))
    prices.sort(key=lambda x: x[0])
    has_vol = isinstance(data.get("volumeDataPoints"), list)
    vols = []
    for p in data.get("volumeDataPoints") or []:
        d, v = _parse_date(p.get("date")), num(p.get("value"))
        if d is not None and v is not None:
            vols.append((d, v))

    def vol_since(days):
        if not has_vol:
            return None
        cut = now - timedelta(days=days)
        return sum(v for d, v in vols if d >= cut)

    cut14 = now - timedelta(days=14)
    recent = sorted(v for d, v in prices if d >= cut14)
    median = None
    if recent:
        m = len(recent) // 2
        median = recent[m] if len(recent) % 2 else (recent[m - 1] + recent[m]) / 2
    last = prices[-1] if prices else None
    return {
        "rap": rap if rap is not None and rap > 0 else None,
        "volume_7d": vol_since(7),
        "volume_30d": vol_since(30),
        "last_chart_price": last[1] if last else None,
        "last_chart_date": last[0].date().isoformat() if last else None,
        "chart_median_14d": median,
        "chart_points_14d": len(recent),
    }


def fetch_resale(client, item, now):
    """Devolve (resumo, status). status: ok | auth_required | error.

    401/403 em qualquer endpoint = auth_required, sem tentar o outro (não contornamos).
    O endpoint antigo só é usado se o novo falhar por outro motivo (404, 5xx...).
    """
    urls = []
    if item.get("collectible_item_id"):
        urls.append(RESALE_NEW.format(cid=item["collectible_item_id"]))
    urls.append(RESALE_OLD.format(aid=item["asset_id"]))
    for url in urls:
        try:
            data = client.get_json(url)
        except AuthRequired:
            return None, "auth_required"
        except ApiError as e:
            log.info("resale-data falhou (%s): %s", item["asset_id"], e.status)
            continue
        if isinstance(data, dict) and "recentAveragePrice" in data:
            return summarize_resale(data, now), "ok"
        log.info("resale-data sem RAP (%s)", item["asset_id"])
    return None, "error"


def fetch_thumbnails(client, asset_ids, errors):
    out = {}
    ids = list(asset_ids)
    for i in range(0, len(ids), 100):
        batch = ids[i:i + 100]
        url = THUMBS + "?" + urllib.parse.urlencode(
            {"assetIds": ",".join(str(a) for a in batch), "size": "150x150",
             "format": "Png", "isCircular": "false"})
        try:
            resp = client.get_json(url)
        except ApiError as e:
            errors.append(f"fotos: {e.status}")
            continue
        for t in (resp or {}).get("data") or []:
            if t.get("state") == "Completed" and t.get("imageUrl"):
                out[t["targetId"]] = t["imageUrl"]
    return out
