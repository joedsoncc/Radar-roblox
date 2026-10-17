import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import analyze, revenda  # noqa: E402
from radar.fake import FakeClient  # noqa: E402
from radar.runner import load_config, run  # noqa: E402

CFG = load_config(ROOT)
NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def sold_out(low=200, rap=500, avg=520, v7=80):
    return {"asset_id": 9, "name": "x", "category": "hat", "price": None, "lowest_resale": low,
            "units_remaining": 0, "total_quantity": 3000, "rap": rap, "resale_avg_low": avg, "volume_7d": v7,
            "last_chart_price": rap, "last_chart_date": NOW.date().isoformat(), "chart_median_14d": rap,
            "chart_points_14d": 10, "creator_verified": False}


class CompraNaRevenda(unittest.TestCase):
    def test_exemplo_do_cartao(self):
        # anúncio 200, venda hoje 500, fator 0,95 -> 475 × 0,5 − 222 = +15,5
        r = revenda.build(sold_out(), CFG, NOW, 0.95, {})
        self.assertEqual(r["tipo"], "revenda")
        self.assertEqual(r["sale_ref"], 475)
        self.assertAlmostEqual(r["net_profit"], 15.5)
        self.assertEqual(r["class"], "OBSERVAR")

    def test_anuncio_muito_barato_vira_comprar(self):
        r = revenda.build(sold_out(low=100), CFG, NOW, 1.0, {})  # 500 × 0,5 − 111 = +125%
        self.assertEqual(r["class"], "COMPRAR-AGORA")

    def test_anuncio_caro_e_evitar(self):
        r = revenda.build(sold_out(low=400), CFG, NOW, 1.0, {})
        self.assertEqual(r["class"], "EVITAR")

    def test_nunca_alerta(self):
        r = revenda.build(sold_out(low=50, v7=500), CFG, NOW, 1.0, {})
        self.assertFalse(analyze.alert_eligible(r, CFG))


class FatorDaTrava(unittest.TestCase):
    def test_lucro_da_loja_usa_fim_da_trava(self):
        it = {"asset_id": 1, "price": 100, "rap": 300, "resale_avg_low": None, "units_remaining": 50,
              "total_quantity": 3000, "last_chart_price": 300, "last_chart_date": NOW.date().isoformat(),
              "chart_median_14d": 300, "chart_points_14d": 10, "name": "x", "volume_7d": 80}
        sem = analyze.analyze([dict(it)], [], NOW, CFG)[0]
        com = analyze.analyze([dict(it)], [], NOW, CFG, holds={"loja": 0.8})[0]
        self.assertEqual(com["sale_ref"], round(sem["sale_ref"] * 0.8, 2))
        self.assertLess(com["net_margin"], sem["net_margin"])
        self.assertTrue(any("trava de 30 dias" in r for r in com["reasons"]))


class Execucao(unittest.TestCase):
    def test_fake_inclui_esgotados_da_revenda(self):
        d = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(ROOT, "config.json"), d)
            res = run(d, client=FakeClient(NOW, days=90), now=NOW, notify=False)
            rev = [i for i in res["items"] if i.get("tipo") == "revenda"]
            self.assertTrue(rev)
            self.assertTrue(all(i["units_remaining"] == 0 for i in rev))
            self.assertTrue(all(i["price"] <= CFG["perfil"]["max_price"] for i in rev))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
