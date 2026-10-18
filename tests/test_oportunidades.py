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
    def test_so_lucro_acima_de_100(self):
        # Corte do Jhow (18/10): lucro líquido > 100% do valor gasto (preço × 1,11).
        self.assertEqual(CFG["oportunidades"]["min_net_margin"], 1.0)
        self.assertIsNone(oportunidades.why_out(item("COMPRAR-AGORA", 1.03), CFG))  # preço 100, venda 450
        self.assertIsNone(oportunidades.why_out(item("OBSERVAR", 1.5), CFG))
        self.assertEqual(oportunidades.why_out(item("OBSERVAR", 0.8), CFG),
                         "lucro projetado +80% (precisa passar de +100%)")         # preço 100, venda 400
        self.assertIsNotNone(oportunidades.why_out(item("OBSERVAR", 1.0), CFG))   # exatamente 100% fica fora
        self.assertIsNotNone(oportunidades.why_out(item("OBSERVAR", -0.1), CFG))
        self.assertEqual(oportunidades.why_out(item("OBSERVAR", None), CFG), "sem estimativa de lucro")
        self.assertEqual(oportunidades.why_out(item("EVITAR", 0.5), CFG), "EVITAR")

    def test_calibracao_fraca_fica_fora(self):
        self.assertIsNotNone(oportunidades.why_out(item("OBSERVAR", 1.2, {"score": 0.2}), CFG))
        self.assertIsNone(oportunidades.why_out(item("OBSERVAR", 1.2, {"score": 0.5}), CFG))

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
            self.assertTrue(all(i["class"] != "EVITAR" and i["net_margin"] > 1.0 for i in data["items"]))
            self.assertEqual(len(data["items"]) + data["descartados"], len(res["items"]))
            self.assertEqual(data["config"]["min_net_margin"], 1.0)  # o app usa o mesmo corte
            self.assertFalse([i for i in data["items"] if "lowest_resale" in i])  # o site só mostra a média
            with open(os.path.join(d, "data", "descartados.md"), encoding="utf-8") as f:
                self.assertIn("Itens descartados", f.read())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
