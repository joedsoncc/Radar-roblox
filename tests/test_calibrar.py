import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import amplo, analyze, calibrar  # noqa: E402
from radar.fake import FakeClient  # noqa: E402
from radar.http import AuthRequired  # noqa: E402
from radar.runner import load_config  # noqa: E402

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CFG = load_config(ROOT)


def rec(orig, start_days_ago, price_after, stock=500, cat="hat", verified=False, first_week=None):
    start = NOW - timedelta(days=start_days_ago)
    prices = []
    for d in range(start_days_ago):
        day = start + timedelta(days=d)
        v = first_week if (first_week and d < 7) else price_after
        prices.append([day.isoformat(), v])
    return {"original_price": orig, "asset_stock": stock, "prices": prices,
            "volumes": [[p[0], 5] for p in prices],
            "item": {"asset_id": 1, "name": "x", "price": orig, "category": cat,
                     "creator_verified": verified, "total_quantity": stock, "favorite_count": stock * 2}}


class Backtest(unittest.TestCase):
    def test_margem_depois_da_trava(self):
        # compra 100 × 1,11 = 111; vende 300 × 0,5 = 150 -> +35%
        r = calibrar.evaluate(rec(100, 60, 300), NOW, CFG)
        self.assertAlmostEqual(r["margem"], (150 - 111) / 111, places=3)
        self.assertEqual(r["features"]["faixa_preco"], "51 a 100")
        self.assertEqual(r["features"]["favoritos_por_un"], "1 a 5 favoritos/un.")

    def test_curva_pos_esgote(self):
        r = calibrar.evaluate(rec(100, 60, 300, first_week=200), NOW, CFG)
        self.assertEqual(r["curva"], {"+1d": 2.0, "+7d": 3.0, "+30d": 3.0})
        c = calibrar.post_sellout_curve([r])
        self.assertEqual(c["geral"]["todos"]["+7d"], {"mediana": 3.0, "n": 1})

    def test_sem_desfecho_antes_de_37_dias(self):
        r = calibrar.evaluate(rec(100, 20, 300), NOW, CFG)
        self.assertIsNone(r["margem"])

    def test_grafico_cortado_fica_fora(self):
        self.assertIsNone(calibrar.evaluate(rec(100, 179, 300), NOW, CFG))

    def test_sem_preco_original_fica_fora(self):
        r = rec(0, 60, 300)
        r["item"]["price"] = None
        self.assertIsNone(calibrar.evaluate(r, NOW, CFG))

    def test_premio_da_primeira_semana(self):
        r = calibrar.evaluate(rec(100, 60, 300, first_week=500), NOW, CFG)
        self.assertEqual(r["features"]["premio_1a_semana"], "4x ou mais")

    def test_lift_e_amostra_pequena(self):
        results = [calibrar.evaluate(rec(100, 60, 300, cat="hat"), NOW, CFG) for _ in range(3)]
        results += [calibrar.evaluate(rec(100, 60, 150, cat="back"), NOW, CFG) for _ in range(3)]
        s = calibrar.summarize(results, min_n=3)
        self.assertEqual(s["taxa_geral"], 0.5)
        cats = {r["faixa"]: r for r in s["sinais"]["categoria"]}
        self.assertEqual(cats["hat"]["lift"], 2.0)
        self.assertEqual(cats["back"]["lift"], 0.0)
        self.assertTrue(cats["hat"]["confiavel"])
        self.assertFalse(calibrar.summarize(results, min_n=4)["sinais"]["categoria"][0]["confiavel"])

    def test_relatorio_e_lifts_no_disco(self):
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, "data", "amplo", "revenda"))
            for i in range(25):
                r = rec(100, 60, 300 if i % 2 else 150, cat="hat")
                r["item"]["asset_id"] = i
                with open(os.path.join(d, "data", "amplo", "revenda", f"{i}.json"), "w") as f:
                    json.dump(r, f)
            s = calibrar.run(d, CFG, NOW)
            self.assertEqual(s["n_backtest"], 25)
            with open(os.path.join(d, "data", "calibracao.md"), encoding="utf-8") as f:
                self.assertIn("Taxa geral de acerto", f.read())
            lifts = calibrar.load_lifts(d)
            self.assertIn("hat", lifts["categoria"])
            self.assertNotIn("premio_1a_semana", lifts)  # sinal pós-esgotar não entra no score
        finally:
            shutil.rmtree(d)


class ScoreComCalibracao(unittest.TestCase):
    ITEM = {"price": 80, "total_quantity": 300, "category": "hat", "creator_verified": True,
            "favorite_count": 100}

    def test_sem_calibracao_e_neutro(self):
        self.assertIsNone(analyze.calibration_for(self.ITEM, {}))

    def test_lift_alto_puxa_para_cima(self):
        lifts = {"categoria": {"hat": {"lift": 2.0, "taxa": 0.4, "n": 50}}}
        cal = analyze.calibration_for(self.ITEM, lifts)
        self.assertEqual(cal["score"], 1.0)
        self.assertIn("favorável", analyze.calibration_reason(cal))

    def test_lift_baixo_puxa_para_baixo(self):
        lifts = {"categoria": {"hat": {"lift": 0.2, "taxa": 0.04, "n": 50}}}
        cal = analyze.calibration_for(self.ITEM, lifts)
        self.assertAlmostEqual(cal["score"], 0.1)
        self.assertIn("fraco", analyze.calibration_reason(cal))


class Coleta(unittest.TestCase):
    def test_alvos_do_historico(self):
        self.assertTrue(amplo.wants_history({"units_remaining": 0, "total_quantity": 500}, CFG))
        self.assertTrue(amplo.wants_history({"units_remaining": 50, "total_quantity": 5000}, CFG))
        self.assertTrue(amplo.wants_history({"units_remaining": 150, "total_quantity": 1000}, CFG))
        self.assertFalse(amplo.wants_history({"units_remaining": 900, "total_quantity": 1000}, CFG))

    def test_rodada_fake_grava_catalogo_e_historico(self):
        d = tempfile.mkdtemp()
        try:
            res = amplo.rodada(d, FakeClient(NOW, days=90), NOW, CFG)
            self.assertGreater(res["catalogo"], 0)
            self.assertGreater(res["historico"]["ok"], 0)
            files = os.listdir(os.path.join(d, "data", "amplo", "revenda"))
            self.assertEqual(len(files), res["historico"]["ok"])
            # Segunda rodada no mesmo dia não busca o histórico de novo.
            res2 = amplo.rodada(d, FakeClient(NOW, days=90), NOW, CFG)
            self.assertEqual(res2["historico"]["ok"], 0)
        finally:
            shutil.rmtree(d)

    def test_login_exigido_para_tudo(self):
        class AuthClient(FakeClient):
            def get_json(self, url):
                if "resale-data" in url:
                    raise AuthRequired(url, 401)
                return super().get_json(url)
        d = tempfile.mkdtemp()
        try:
            res = amplo.rodada(d, AuthClient(NOW, days=90), NOW, CFG)
            self.assertEqual(res["historico"]["auth_required"], 1)
            self.assertEqual(res["historico"]["ok"], 0)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
