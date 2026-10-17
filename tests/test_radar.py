import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, ROOT)

from radar import analyze, collect  # noqa: E402
from radar.fake import FakeClient  # noqa: E402
from radar.runner import load_config, run  # noqa: E402

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CFG = load_config(ROOT)


def tmp_root():
    d = tempfile.mkdtemp()
    shutil.copy(os.path.join(ROOT, "config.json"), d)
    return d


class Contas(unittest.TestCase):
    def test_exemplo_do_readme(self):
        cost, profit, margin = analyze.economics(100, 260, CFG)
        self.assertEqual(cost, 111.0)
        self.assertEqual(profit, 19.0)
        self.assertAlmostEqual(margin, 19 / 111, places=3)

    def test_equilibrio_2x(self):
        _, profit, _ = analyze.economics(100, 222, CFG)
        self.assertAlmostEqual(profit, 0.0)

    def test_sem_rap_nao_inventa(self):
        self.assertEqual(analyze.economics(100, None, CFG), (111.0, None, None))


class Series(unittest.TestCase):
    def test_serie_mais_nova_primeiro(self):
        data = {"recentAveragePrice": 200,
                "priceDataPoints": [{"value": 90, "date": "2026-10-16T00:00:00Z"},
                                    {"value": 300, "date": "2026-09-01T00:00:00Z"}],
                "volumeDataPoints": [{"value": 10, "date": "2026-10-16T00:00:00Z"},
                                     {"value": 50, "date": "2026-10-01T00:00:00Z"},
                                     {"value": 99, "date": "2026-08-01T00:00:00Z"}]}
        s = collect.summarize_resale(data, NOW)
        self.assertEqual(s["last_chart_price"], 90)  # o mais novo, não o primeiro/último da lista
        self.assertEqual(s["volume_7d"], 10)
        self.assertEqual(s["volume_30d"], 60)
        # 90 < 0,5 × 200 -> RAP não confiável
        self.assertFalse(analyze.rap_consistency(200, 90, s["last_chart_date"], NOW, CFG))

    def test_filtra_nao_acessorios(self):
        self.assertIsNone(collect.normalize_catalog_item(
            {"id": 1, "assetType": 61, "itemRestrictions": ["Collectible"]}, CFG["categorias"]))
        self.assertEqual(collect.normalize_catalog_item(
            {"id": 1, "assetType": 47, "itemRestrictions": ["Collectible"]}, CFG["categorias"])["category"], "waist")


class FluxoCompleto(unittest.TestCase):
    def _two_runs(self, root, sends, rap_mult=4):
        c1 = FakeClient(NOW - timedelta(hours=2), seed=1, n=20)
        for it in c1.items:
            it["assetType"] = 8
            it["price"] = 100
            it["totalQuantity"] = 500
            it["unitsAvailableForConsumption"] = 60
        c1.rap = {k: 100 * rap_mult for k in c1.rap}
        send = lambda **kw: sends.append(kw) or True  # noqa: E731
        run(root, client=c1, now=NOW - timedelta(hours=2), send=send, topic="t")
        c1.now = NOW
        for it in c1.items:
            it["unitsAvailableForConsumption"] = 50
        return run(root, client=c1, now=NOW, send=send, topic="t")

    def test_alerta_uma_vez_e_limite_diario(self):
        root, sends = tmp_root(), []
        res = self._two_runs(root, sends)
        buy = [i for i in res["items"] if i["class"] == "COMPRAR-AGORA"]
        self.assertTrue(buy, "com RAP 4x, volume alto e velocidade medida deve haver COMPRAR-AGORA")
        self.assertEqual(len(sends), CFG["alertas"]["max_alerts_per_day"])
        self.assertIn("Não é recomendação financeira", sends[0]["message"])
        self.assertTrue(sends[0]["click"].startswith("https://www.roblox.com/catalog/"))
        # 3ª execução no mesmo dia: nada novo
        before = len(sends)
        run(root, client=FakeClient(NOW, seed=1, n=0), now=NOW + timedelta(minutes=5),
            send=lambda **kw: sends.append(kw) or True, topic="t")
        self.assertEqual(len(sends), before)

    def test_sem_velocidade_nao_compra(self):
        root = tmp_root()
        res = run(root, client=FakeClient(NOW, seed=3), now=NOW, send=lambda **kw: True, topic="t")
        self.assertFalse([i for i in res["items"] if i["class"] == "COMPRAR-AGORA"])
        self.assertEqual(res["alerts"], [])

    def test_prejuizo_vira_evitar(self):
        root, sends = tmp_root(), []
        res = self._two_runs(root, sends, rap_mult=1)
        self.assertTrue(all(i["class"] in ("EVITAR", "OBSERVAR") for i in res["items"]))
        self.assertEqual(sends, [])

    def test_api_exige_login(self):
        root, notices = tmp_root(), []
        res = run(root, client=FakeClient(NOW, resale_mode="auth"), now=NOW,
                  send=lambda **kw: notices.append(kw) or True, topic="t")
        self.assertEqual(res["status"], "auth_required")
        self.assertTrue(all(i["rap"] is None and i["net_profit"] is None for i in res["items"]))
        self.assertEqual(len(notices), 1)  # aviso de sistema, não oportunidade
        # para de insistir depois das primeiras recusas
        self.assertLess(res["statuses"]["auth_required"] + 0, 999)

    def test_catalogo_fora_mantem_site_anterior(self):
        root = tmp_root()
        run(root, client=FakeClient(NOW), now=NOW, notify=False)
        with open(os.path.join(root, "docs", "data.json")) as f:
            before = json.load(f)["items"]
        res = run(root, client=FakeClient(NOW, fail_catalog=True, n=0), now=NOW + timedelta(hours=2), notify=False)
        with open(os.path.join(root, "docs", "data.json")) as f:
            after = json.load(f)
        self.assertEqual(res["status"], "error")
        self.assertEqual(after["items"], before)
        self.assertIn("Falha", after["status_note"])

    def test_topico_nunca_vai_para_arquivos(self):
        root, topic = tmp_root(), "segredo-topico-XYZ123"
        self._two_runs(root, [])
        run(root, client=FakeClient(NOW, seed=1), now=NOW + timedelta(hours=1),
            send=lambda **kw: True, topic=topic)
        for dirpath, _, files in os.walk(root):
            for fn in files:
                with open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore") as f:
                    self.assertNotIn(topic, f.read(), fn)


def hist(asset_id, pts):
    return [{"asset_id": asset_id, "units_remaining": u, "_ts": NOW - timedelta(hours=h)} for h, u in pts]


class Velocidade(unittest.TestCase):
    def test_snapshots_muito_proximos(self):
        v, note = analyze.velocity(1, hist(1, [(0.05, 99), (0, 97)]), NOW, CFG)
        self.assertIsNone(v)
        self.assertIn("próximos", note)

    def test_vendas_pararam(self):
        v, _ = analyze.velocity(1, hist(1, [(22, 99), (20, 60), (10, 60), (0, 60)]), NOW, CFG)
        self.assertEqual(v, 0.0)

    def test_estoque_aumentou(self):
        v, note = analyze.velocity(1, hist(1, [(4, 99), (2, 50), (0, 95)]), NOW, CFG)
        self.assertIsNone(v)
        self.assertIn("aumentou", note)

    def test_velocidade_normal(self):
        v, _ = analyze.velocity(1, hist(1, [(4, 90), (2, 80), (0, 70)]), NOW, CFG)
        self.assertEqual(v, 5.0)


class RespostasRuins(unittest.TestCase):
    def test_resposta_vazia_eh_erro(self):
        class C:
            calls = 0
            def get_json(self, url):
                return {}
        s, st = collect.fetch_resale(C(), {"asset_id": 1, "collectible_item_id": "x"}, NOW)
        self.assertEqual((s, st), (None, "error"))

    def test_sem_serie_de_volume_vira_none(self):
        s = collect.summarize_resale({"recentAveragePrice": 100, "priceDataPoints": []}, NOW)
        self.assertIsNone(s["volume_7d"])

    def test_401_nao_tenta_outro_endpoint(self):
        from radar.http import AuthRequired
        calls = []
        class C:
            def get_json(self, url):
                calls.append(url)
                raise AuthRequired(url, 401)
        _, st = collect.fetch_resale(C(), {"asset_id": 1, "collectible_item_id": "x"}, NOW)
        self.assertEqual(st, "auth_required")
        self.assertEqual(len(calls), 1)

    def test_rap_inflado_por_uma_venda(self):
        # último preço alto, mas mediana de 14 dias bem abaixo da metade do RAP
        self.assertFalse(analyze.rap_consistency(400, 390, "2026-10-16", NOW, CFG, median_14d=120, points_14d=6))


class Outbox(unittest.TestCase):
    def test_outbox_antigo_nao_envia(self):
        from radar.notify import send_outbox, write_outbox
        root, sent = tmp_root(), []
        write_outbox(root, [{"title": "t", "message": "m"}], NOW - timedelta(hours=3))
        self.assertEqual(send_outbox(root, send=lambda **kw: sent.append(kw) or True, now=NOW), 0)
        self.assertEqual(sent, [])

    def test_mensagem_tem_link(self):
        root, sends = tmp_root(), []
        FluxoCompleto()._two_runs(root, sends)
        self.assertIn("https://www.roblox.com/catalog/", sends[0]["message"])


if __name__ == "__main__":
    unittest.main()
