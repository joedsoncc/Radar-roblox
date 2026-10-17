import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import oportunidades  # noqa: E402
from radar.fake import FakeClient  # noqa: E402
from radar.runner import load_config, run  # noqa: E402
from radar.site import buy_list_md  # noqa: E402

CFG = load_config(ROOT)
NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def item(cls, margin, cal=None):
    return {"class": cls, "net_margin": margin, "calibracao": cal, "name": "x", "url": "u", "price": 100}


class Filtro(unittest.TestCase):
    def test_so_o_que_pode_dar_lucro(self):
        self.assertIsNone(oportunidades.why_out(item("COMPRAR-AGORA", 0.4), CFG))
        self.assertIsNone(oportunidades.why_out(item("OBSERVAR", 0.17), CFG))   # 1b: OBSERVAR com lucro entra
        self.assertEqual(oportunidades.why_out(item("OBSERVAR", -0.1), CFG), "margem projetada -10%")
        self.assertEqual(oportunidades.why_out(item("OBSERVAR", 0.0), CFG), "margem projetada +0%")
        self.assertEqual(oportunidades.why_out(item("OBSERVAR", None), CFG), "sem estimativa de lucro")
        self.assertEqual(oportunidades.why_out(item("EVITAR", 0.5), CFG), "EVITAR")

    def test_calibracao_fraca_fica_fora(self):
        self.assertIsNotNone(oportunidades.why_out(item("OBSERVAR", 0.2, {"score": 0.2}), CFG))
        self.assertIsNone(oportunidades.why_out(item("OBSERVAR", 0.2, {"score": 0.5}), CFG))

    def test_lista_vazia_diz_nenhuma_oportunidade(self):
        md = buy_list_md({"generated_at": "t", "run_status": "ok", "status_note": "", "disclaimer": "d",
                          "categories": CFG["categorias"], "items": []})
        self.assertIn("Nenhuma oportunidade agora", md)


class SiteSoComLucro(unittest.TestCase):
    def test_execucao_fake(self):
        d = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(ROOT, "config.json"), d)
            res = run(d, client=FakeClient(NOW, days=90), now=NOW, notify=False)
            with open(os.path.join(d, "docs", "data.json"), encoding="utf-8") as f:
                data = json.load(f)
            self.assertTrue(all(i["class"] != "EVITAR" and i["net_margin"] > 0 for i in data["items"]))
            self.assertEqual(len(data["items"]) + data["descartados"], len(res["items"]))
            with open(os.path.join(d, "data", "descartados.md"), encoding="utf-8") as f:
                self.assertIn("Itens descartados", f.read())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
