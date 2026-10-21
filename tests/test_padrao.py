import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import analyze, carteira  # noqa: E402
from radar.runner import load_config  # noqa: E402

CFG = load_config(ROOT)
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


class FormatoMaisVendidos(unittest.TestCase):
    def test_formato(self):
        self.assertTrue(analyze.best_seller_format({"total_quantity": 3000, "price": 95}, CFG))
        self.assertTrue(analyze.best_seller_format({"total_quantity": 2500, "price": 55}, CFG))
        self.assertFalse(analyze.best_seller_format({"total_quantity": 3000, "price": 199}, CFG))
        self.assertFalse(analyze.best_seller_format({"total_quantity": 5000, "price": 95}, CFG))
        self.assertFalse(analyze.best_seller_format({"total_quantity": 3000, "price": 0}, CFG))
        self.assertFalse(analyze.best_seller_format({"total_quantity": None, "price": 95}, CFG))

    def test_oferta(self):
        s = lambda t, p=95: analyze.supply_score({"total_quantity": t, "price": p}, CFG)  # noqa: E731
        self.assertEqual(s(3000), 1.0)
        self.assertEqual(s(3000, 199), 0.8)  # fora do preço, mas estoque > 2.000
        self.assertEqual(s(5000), 0.8)
        self.assertEqual(s(50), 0.0)  # estoque minúsculo
        self.assertEqual(s(20000), 0.0)
        self.assertEqual(s(500), 0.5)
        self.assertEqual(s(None), 0.3)

    def test_favoritos(self):
        self.assertEqual(analyze.favorites_score({"favorite_count": 2000}, CFG), 1.0)
        self.assertEqual(analyze.favorites_score({"favorite_count": 500}, CFG), 0.5)
        self.assertEqual(analyze.favorites_score({}, CFG), 0.3)

    def test_ritmo_de_esgote(self):
        r = lambda v, t=3000: analyze.sellout_pace_score({"velocity_per_hour": v, "total_quantity": t}, CFG)  # noqa: E731
        self.assertEqual(r(None), 0.5)       # sem medida: neutro
        self.assertEqual(r(0.0), 0.0)        # vendas paradas
        self.assertEqual(r(2.0), 1.0)        # 3000 / 48 por dia = 62,5 dias
        self.assertEqual(r(1.0), 0.5)        # 125 dias
        self.assertEqual(r(0.5), 0.1)        # 250 dias
        self.assertEqual(analyze.sellout_days({"velocity_per_hour": 2.0, "total_quantity": 3000}), 62.5)

    def test_motivo(self):
        self.assertIn("Formato dos mais revendidos",
                      analyze.pattern_reason({"total_quantity": 3000, "price": 95, "favorite_count": 1200}, CFG))
        self.assertIn("1200 favoritos",
                      analyze.pattern_reason({"total_quantity": 3000, "price": 95, "favorite_count": 1200}, CFG))
        self.assertIn("minúsculo", analyze.pattern_reason({"total_quantity": 40, "price": 300}, CFG))
        self.assertIsNone(analyze.pattern_reason({"total_quantity": 500, "price": 300}, CFG))

    def test_formato_sobe_o_score(self):
        base = {"net_margin": 0.5, "volume_7d": 100, "rap_consistent": True, "eta_hours": 20,
                "velocity_per_hour": 2.0, "price": 95, "favorite_count": 1500}
        campeao = analyze.score(dict(base, total_quantity=3000), CFG)
        minusculo = analyze.score(dict(base, total_quantity=50), CFG)
        self.assertGreater(campeao, minusculo)


class JanelaDeVenda(unittest.TestCase):
    def h(self, *pts):
        return [{"ts": ts, "units_remaining": u} for ts, u in pts]

    def test_a_venda(self):
        j = carteira.sell_window(self.h(("2026-10-20T00:00:00Z", 10)), NOW, CFG)
        self.assertEqual(j["status"], "a_venda")

    def test_sem_data(self):
        j = carteira.sell_window(self.h(("2026-10-20T00:00:00Z", 0)), NOW, CFG)
        self.assertEqual(j["status"], "sem_data")
        self.assertIsNone(j["dias_desde_esgote"])

    def test_antes_agora_passou(self):
        for esgote, status, dias in (("2026-10-16T00:00:00Z", "antes", 5),
                                     ("2026-09-21T00:00:00Z", "agora", 30),
                                     ("2026-08-01T00:00:00Z", "passou", 81)):
            j = carteira.sell_window(self.h(("2026-07-01T00:00:00Z", 5), (esgote, 0), ("2026-10-21T00:00:00Z", 0)),
                                     NOW, CFG)
            self.assertEqual((j["status"], j["dias_desde_esgote"]), (status, dias))
            self.assertEqual(j["esgotou_em"], esgote[:10])
        self.assertIn("faltam 10 dias", carteira.sell_window(
            self.h(("2026-10-01T00:00:00Z", 5), ("2026-10-16T00:00:00Z", 0)), NOW, CFG)["texto"])

    def test_voltou_a_venda(self):
        j = carteira.sell_window(self.h(("2026-10-01T00:00:00Z", 5), ("2026-10-05T00:00:00Z", 0),
                                         ("2026-10-20T00:00:00Z", 3)), NOW, CFG)
        self.assertEqual(j["status"], "a_venda")

    def test_sem_historico(self):
        self.assertIsNone(carteira.sell_window([], NOW, CFG))


if __name__ == "__main__":
    unittest.main()
