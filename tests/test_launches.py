import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import launches  # noqa: E402
from radar.http import ApiError  # noqa: E402
from radar.notify import send_outbox  # noqa: E402
from radar.runner import load_config  # noqa: E402

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CFG = load_config(ROOT)


def raw(i, creator=1, atype=8, tags=("Limited",)):
    return {"id": i, "name": f"Item {i}", "assetType": atype, "creatorTargetId": creator,
            "itemRestrictions": list(tags), "price": 100, "totalQuantity": 500,
            "unitsAvailableForConsumption": 480}


class Fake:
    def __init__(self, items, created=None, fail_details=False):
        self.items, self.created, self.fail_details = items, created or {}, fail_details

    def get_json(self, url):
        if "catalog.roblox.com" in url:
            return {"data": self.items}
        if "economy.roblox.com/v2/assets/" in url:
            if self.fail_details:
                raise ApiError(url, 500)
            aid = int(url.split("/assets/")[1].split("/")[0])
            return {"Created": self.created.get(aid, "2020-01-01T00:00:00Z")}
        raise ApiError(url, 404)


class Lancamentos(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def sent(self, now):
        out = []
        send_outbox(self.root, send=lambda **kw: out.append(kw) or True, now=now, name="launch_outbox.json")
        return out

    def test_primeira_execucao_nao_avisa(self):
        r = launches.run(self.root, Fake([raw(1), raw(2)]), CFG, now=NOW)
        self.assertEqual(r["status"], "seeded")
        self.assertEqual(self.sent(NOW), [])

    def test_novo_item_avisa_uma_vez(self):
        launches.run(self.root, Fake([raw(1)]), CFG, now=NOW)
        later = NOW + timedelta(minutes=10)
        f = Fake([raw(1), raw(2)], created={2: "2026-10-17T11:55:00Z"})
        r = launches.run(self.root, f, CFG, now=later)
        self.assertEqual([i["asset_id"] for i in r["new"]], [2])
        msgs = self.sent(later)
        self.assertEqual(len(msgs), 1)
        self.assertIn("Novo limited da Roblox", msgs[0]["title"])
        self.assertIn("https://www.roblox.com/catalog/2", msgs[0]["message"])
        r2 = launches.run(self.root, f, CFG, now=later + timedelta(minutes=10))
        self.assertFalse(r2["changed"])

    def test_filtra_criador_tipo_e_antigos(self):
        launches.run(self.root, Fake([]), CFG, now=NOW)
        items = [raw(3, creator=999), raw(4, atype=61), raw(5, tags=()), raw(6)]
        r = launches.run(self.root, Fake(items, created={6: "2025-01-01T00:00:00Z"}), CFG, now=NOW)
        self.assertEqual(r["new"], [])  # 6 é antigo; 3, 4 e 5 não são limiteds-acessórios da Roblox

    def test_data_desconhecida_avisa_com_ressalva(self):
        launches.run(self.root, Fake([]), CFG, now=NOW)
        r = launches.run(self.root, Fake([raw(7)], fail_details=True), CFG, now=NOW)
        self.assertTrue(r["new"][0]["created_unknown"])
        self.assertIn("não confirmada", self.sent(NOW)[0]["message"])


if __name__ == "__main__":
    unittest.main()
