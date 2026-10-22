import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import visual  # noqa: E402

try:
    from PIL import Image
except ImportError:  # o workflow do radar não instala Pillow
    Image = None


def _hist(root, aid, name, vol, qty=3000, creator_id=99, remaining=0):
    os.makedirs(os.path.join(root, "data", "amplo", "revenda"), exist_ok=True)
    rec = {"fetched_at": "2026-10-17T20:00:00Z",
           "item": {"asset_id": aid, "name": name, "creator_name": "x", "creator_id": creator_id,
                    "category": "hat", "total_quantity": qty, "units_remaining": remaining,
                    "favorite_count": 10},
           "rap": 300, "prices": [["2026-06-01T00:00:00Z", 95], ["2026-10-10T00:00:00Z", 300]],
           "volumes": [["2026-08-01T00:00:00Z", 500], ["2026-10-10T00:00:00Z", vol]]}
    with open(os.path.join(root, "data", "amplo", "revenda", f"{aid}.json"), "w") as f:
        json.dump(rec, f)


class Visual(unittest.TestCase):
    def test_tags(self):
        t = visual.tags("[⏳] Pink Sparkle Time Fedora + Crown + Horns")
        self.assertIn("chifres", t["forma"])
        self.assertIn("coroa", t["forma"])
        self.assertIn("rosa", t["cor"])
        self.assertIn("sparkle", t["efeito"])
        self.assertIn("combo", t["tema"])
        self.assertEqual(visual.tags("Red Star")["cor"], ["vermelho"])
        self.assertEqual(visual.tags("Redwood")["cor"], [])

    def test_ranking_so_ugc_esgotado_e_volume_30d(self):
        with tempfile.TemporaryDirectory() as root:
            _hist(root, 1, "Valk", 50)
            _hist(root, 2, "Dominus", 80)
            _hist(root, 3, "Oficial", 999, creator_id=1)
            _hist(root, 4, "À venda", 999, remaining=5)
            rows = visual.ranking(root)
            self.assertEqual([r["asset_id"] for r in rows], [2, 1])
            self.assertEqual(rows[0]["revendas_30d"], 80)  # a venda de agosto fica fora
            self.assertEqual(rows[0]["loja"], 95)
            self.assertEqual(rows[0]["grupo"], "top")

    def test_run_sem_coleta(self):
        with tempfile.TemporaryDirectory() as root:
            _hist(root, 1, "Black Valk", 50)
            res = visual.run(root)
            self.assertEqual(res["itens"], 1)
            self.assertEqual(res["comparacao"]["forma: valk"]["top"], 100)
            self.assertTrue(os.path.exists(os.path.join(root, "data", "visual", "visual.json")))

    @unittest.skipIf(Image is None, "sem Pillow")
    def test_image_stats(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.png")
            im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            for x in range(10, 90):
                for y in range(40, 60):
                    im.putpixel((x, y), (220, 30, 30, 255))
            im.save(p)
            s = visual.image_stats(p)
            self.assertEqual(s["cor_1"], "vermelho")
            self.assertGreater(s["proporcao"], 3)
            self.assertLess(s["ocupa"], 0.3)


if __name__ == "__main__":
    unittest.main()
