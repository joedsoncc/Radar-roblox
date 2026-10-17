"""Cliente falso para testes e para `python radar.py run --fake` (nunca acessa a internet)."""
import random
from datetime import timedelta

from .http import ApiError, AuthRequired


class FakeClient:
    def __init__(self, now, seed=7, n=40, resale_mode="ok", fail_catalog=False, days=30):
        self.days = days
        self.now = now
        self.rng = random.Random(seed)
        self.resale_mode = resale_mode  # ok | auth | error
        self.fail_catalog = fail_catalog
        self.calls = 0
        types = [8, 41, 42, 43, 44, 45, 46, 47, 61, 11]  # 61 emote e 11 camisa devem ser filtrados
        self.items = []
        for i in range(n):
            total = self.rng.choice([100, 250, 500, 1000])
            price = self.rng.choice([30, 60, 90, 150, 250, 400, 600])
            self.items.append({
                "id": 1000 + i, "itemType": "Asset", "assetType": types[i % len(types)],
                "name": f"[FALSO] Item {i}", "creatorName": f"Criador{i % 5}",
                "creatorTargetId": 50 + i % 5, "creatorType": "User",
                "creatorHasVerifiedBadge": i % 3 == 0, "price": price,
                "totalQuantity": total,
                "unitsAvailableForConsumption": self.rng.randint(0, min(total, 150)),
                "lowestResalePrice": int(price * self.rng.uniform(0.9, 4)),
                "itemRestrictions": ["Collectible"], "collectibleItemId": f"c-{i}",
                "favoriteCount": self.rng.randint(0, 5000),
            })
        self.rap = {it["collectibleItemId"]: int(it["price"] * self.rng.choice([0.9, 1.5, 2.5, 3.5, 5])) for it in self.items}

    def get_json(self, url):
        self.calls += 1
        if "catalog.roblox.com/v2/search" in url:
            if self.fail_catalog:
                raise ApiError(url, 503, "falso")
            if "CreatorTargetId=" in url:  # busca por criador (histórico das lojas): todos os tipos de limited
                self.creator_calls = getattr(self, "creator_calls", 0) + 1
                cid = int(url.split("CreatorTargetId=")[1].split("&")[0])
                return {"data": [it for it in self.items if it["creatorTargetId"] == cid], "nextPageCursor": None}
            return {"data": self.items, "nextPageCursor": None}
        if "resale-data" in url:
            if self.resale_mode == "auth":
                raise AuthRequired(url, 401, "falso")
            if self.resale_mode == "error":
                raise ApiError(url, 500, "falso")
            cid = url.split("/item/")[1].split("/")[0] if "/item/" in url else None
            rap = self.rap.get(cid, 100)
            # Série da mais nova para a mais antiga, só dias com venda.
            pts, vols = [], []
            for d in range(0, self.days, 2):
                day = (self.now - timedelta(days=d)).strftime("%Y-%m-%dT00:00:00Z")
                pts.append({"value": int(rap * self.rng.uniform(0.8, 1.2)), "date": day})
                vols.append({"value": self.rng.randint(5, 40), "date": day})
            return {"recentAveragePrice": rap, "priceDataPoints": pts, "volumeDataPoints": vols}
        if "thumbnails.roblox.com" in url:
            ids = url.split("assetIds=")[1].split("&")[0].replace("%2C", ",").split(",")
            return {"data": [{"targetId": int(a), "state": "Completed",
                              "imageUrl": "icons/icon-192.png"} for a in ids]}
        raise ApiError(url, 404, "falso")

    def post_json(self, url, data):
        self.calls += 1
        ids = {x["id"] for x in data["items"]}
        return {"data": [it for it in self.items if it["id"] in ids]}
