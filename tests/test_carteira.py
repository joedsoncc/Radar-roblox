import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from radar import analyze, cadastro, carteira, collect, lojas  # noqa: E402
from radar.fake import FakeClient  # noqa: E402
from radar.runner import load_config, run  # noqa: E402
from test_radar import tmp_root  # noqa: E402

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CFG = load_config(ROOT)


def write_carteira(root, itens):
    with open(os.path.join(root, "carteira.json"), "w", encoding="utf-8") as f:
        json.dump({"itens": itens}, f)


def read_json(root, *path):
    with open(os.path.join(root, *path), encoding="utf-8") as f:
        return json.load(f)


def serie(prices_by_age):
    """{idade em dias: preço} -> série do contrato [["AAAA-MM-DD", preço, volume]]."""
    return [[(NOW - timedelta(days=a)).date().isoformat(), p, 5] for a, p in sorted(prices_by_age.items(), reverse=True)]


class ContasDaCarteira(unittest.TestCase):
    def lot(self, paid, qty=1, day="2026-10-17"):
        return {"preco_pago": paid, "quantidade": qty, "comprado_em": day, "nota": ""}

    def item(self, lots, rap, price=195, series=None, low=210, listings=None):
        detail = {"name": "X", "creator_name": "C", "category": "hat", "price": price,
                  "units_remaining": 50, "total_quantity": 3000, "is_off_sale": False, "lowest_resale": low}
        summary = {"rap": rap, "volume_7d": 40, "chart_series": series or []}
        if listings is not None:
            summary["resale_avg_low"], summary["resale_avg_n"] = collect.avg_lowest(listings, 10)
        return carteira.compute_item(1, lots, detail, summary, [], None, NOW, CFG)

    def test_exemplo_pago_195_rap_195(self):
        it = self.item([self.lot(195)], 195)
        self.assertEqual(it["value_now"], 97.5)
        self.assertEqual(it["cost_total"], 195)
        self.assertEqual(it["pnl"], -97.5)
        self.assertEqual(it["pnl_pct"], -0.5)
        self.assertEqual(it["breakeven_rap"], 390)
        self.assertEqual(it["retention"], 1.0)
        self.assertEqual(it["days_held"], 0)

    def test_anuncios_abaixo_do_rap_baixam_o_valor(self):
        it = self.item([self.lot(100, 2)], 400, listings=[300] * 9 + [200, 900])  # média dos 10 menores = 290
        self.assertEqual((it["resale_avg_low"], it["resale_avg_n"], it["sale_ref_source"]), (290, 10, "anuncios"))
        self.assertEqual(it["value_now"], 290)  # 290 × 0,5 × 2
        self.assertEqual(it["pnl"], 90)

    def test_sem_lista_de_anuncios_usa_menor_do_catalogo(self):
        it = self.item([self.lot(100)], 400, low=210)
        self.assertEqual((it["resale_avg_low"], it["resale_avg_n"]), (210, 1))
        self.assertEqual(it["value_now"], 105)

    def test_lotes_somados_com_media_ponderada(self):
        it = self.item([self.lot(100, 1, "2026-10-10"), self.lot(200, 3, "2026-10-15")], 400, low=None)
        self.assertEqual(it["quantity"], 4)
        self.assertEqual(it["avg_paid"], 175)
        self.assertEqual(it["cost_total"], 700)
        self.assertEqual(it["value_now"], 800)  # 400 × 0,5 × 4
        self.assertEqual(it["pnl"], 100)
        self.assertEqual(it["breakeven_rap"], 350)
        self.assertEqual(it["days_held"], 7)

    def test_so_acompanhar_fica_fora_dos_totais(self):
        a = self.item([self.lot(195)], 195)
        b = self.item([self.lot(None, 2)], 400, low=None)
        self.assertIsNone(b["avg_paid"])
        self.assertIsNone(b["pnl"])
        self.assertEqual(b["value_now"], 400)
        tot = carteira.compute_totals([a, b])
        self.assertEqual((tot["cost"], tot["value_now"], tot["pnl"], tot["pnl_pct"]), (195, 97.5, -97.5, -0.5))

    def test_sem_rap_nao_inventa(self):
        it = self.item([self.lot(195)], None)
        self.assertIsNone(it["value_now"])
        self.assertIsNone(it["pnl"])
        self.assertEqual(it["breakeven_rap"], 390)  # só depende do que foi pago
        self.assertEqual(carteira.compute_totals([it])["pnl"], None)

    def test_preco_zero_nao_divide(self):
        it = self.item([self.lot(0)], 100)
        self.assertEqual(it["pnl"], 50)
        self.assertIsNone(it["pnl_pct"])


class TendenciaEVariacao(unittest.TestCase):
    def test_subindo(self):
        s = serie({1: 120, 3: 120, 5: 120, 9: 100, 11: 100, 13: 100})
        ch = analyze.window_change(s, NOW, 7)
        self.assertEqual(ch, 0.2)
        self.assertEqual(analyze.trend_for(s, ch, NOW), "subindo")

    def test_caindo_e_estavel(self):
        s = serie({1: 90, 3: 90, 5: 90, 9: 100, 11: 100, 13: 100})
        self.assertEqual(analyze.trend_for(s, analyze.window_change(s, NOW, 7), NOW), "caindo")
        s = serie({1: 101, 3: 101, 5: 101, 9: 100, 11: 100, 13: 100})
        self.assertEqual(analyze.trend_for(s, analyze.window_change(s, NOW, 7), NOW), "estável")

    def test_sem_dados(self):
        s = serie({1: 120, 9: 100})  # menos de 3 dias de venda em 14 dias
        self.assertEqual(analyze.trend_for(s, analyze.window_change(s, NOW, 7), NOW), "sem dados")
        self.assertIsNone(analyze.window_change([], NOW, 7))
        self.assertIsNone(analyze.window_change(serie({1: 100}), NOW, 30))  # sem janela anterior

    def test_change_30d(self):
        s = serie({2: 150, 10: 150, 20: 150, 35: 100, 50: 100})
        self.assertEqual(analyze.window_change(s, NOW, 30), 0.5)

    def test_serie_do_grafico_ate_180_dias_ordenada(self):
        data = {"recentAveragePrice": 100,
                "priceDataPoints": [{"value": 90, "date": "2026-10-16T00:00:00Z"},
                                    {"value": 80, "date": "2026-01-01T00:00:00Z"},
                                    {"value": 70, "date": "2026-05-01T00:00:00Z"}],
                "volumeDataPoints": [{"value": 4, "date": "2026-10-16T00:00:00Z"},
                                     {"value": 9, "date": "2026-05-01T00:00:00Z"}]}
        s = collect.summarize_resale(data, NOW)["chart_series"]
        self.assertEqual(s, [["2026-05-01", 70, 9], ["2026-10-16", 90, 4]])  # janeiro tem mais de 180 dias


CORPO = """### Ação

Adicionar

### Item (link do catálogo ou ID)

{item}

### Preço pago (Robux por unidade)

{preco}

### Quantidade

{qtd}

### Comprado em (AAAA-MM-DD)

{data}

### Nota

{nota}
"""


def corpo(item="123456", preco="195", qtd="1", data="_No response_", nota="_No response_", acao=None):
    b = CORPO.format(item=item, preco=preco, qtd=qtd, data=data, nota=nota)
    return b.replace("Adicionar", acao, 1) if acao else b


class CorpoDaIssue(unittest.TestCase):
    def test_parse_basico(self):
        f = cadastro.parse_body(corpo(nota="comprei no lançamento"))
        self.assertEqual(f["acao"], "Adicionar")
        self.assertEqual(f["item"], "123456")
        self.assertEqual(f["preco_pago"], "195")
        self.assertEqual(f["comprado_em"], "")  # _No response_
        self.assertEqual(f["nota"], "comprei no lançamento")

    def test_parse_crlf(self):
        f = cadastro.parse_body(corpo().replace("\n", "\r\n"))
        self.assertEqual(f["item"], "123456")

    def test_url_com_nome_no_final(self):
        self.assertEqual(cadastro.extract_asset_id("https://www.roblox.com/catalog/90254996174236/8-Bit-Royal-Crown"),
                         90254996174236)
        self.assertEqual(cadastro.extract_asset_id("https://www.roblox.com/catalog/42?x=1"), 42)
        self.assertEqual(cadastro.extract_asset_id(" 777 "), 777)

    def test_item_invalido(self):
        for bad in ("", "abc", "https://example.com/x", "12a", "-5"):
            with self.assertRaises(cadastro.CadastroError):
                cadastro.extract_asset_id(bad)

    def test_validacoes(self):
        ok = cadastro.validate(cadastro.parse_body(corpo(preco="0", qtd="100", data="2026-10-01")), NOW)
        self.assertEqual((ok["preco_pago"], ok["quantidade"], ok["comprado_em"]), (0, 100, "2026-10-01"))
        for kw in ({"preco": "-1"}, {"preco": "19,5"}, {"preco": "abc"}, {"qtd": "0"}, {"qtd": "101"},
                   {"qtd": "1.5"}, {"data": "17/10/2026"}, {"data": "2026-02-30"}, {"data": "2030-01-01"}):
            with self.assertRaises(cadastro.CadastroError, msg=str(kw)):
                cadastro.validate(cadastro.parse_body(corpo(**kw)), NOW)

    def test_padroes_vazios(self):
        v = cadastro.validate(cadastro.parse_body(corpo(preco="_No response_", qtd="_No response_")), NOW)
        self.assertIsNone(v["preco_pago"])
        self.assertEqual(v["quantidade"], 1)
        self.assertEqual(v["comprado_em"], "2026-10-17")  # hoje (Brasília)

    def test_adicionar_e_remover_todos_os_lotes(self):
        root = tmp_root()
        write_carteira(root, [{"asset_id": 5, "preco_pago": 10, "quantidade": 1, "comprado_em": "2026-10-01", "nota": ""}])
        ok, msg, aid = cadastro.cadastrar(root, corpo(item="https://www.roblox.com/catalog/5/Nome", preco="20"), NOW)
        self.assertTrue(ok, msg)
        self.assertEqual(aid, 5)
        ok, msg, _ = cadastro.cadastrar(root, corpo(item="6", preco="_No response_"), NOW)
        self.assertTrue(ok)
        itens = read_json(root, "carteira.json")["itens"]
        self.assertEqual([i["asset_id"] for i in itens], [5, 5, 6])
        self.assertIsNone(itens[2]["preco_pago"])
        ok, msg, _ = cadastro.cadastrar(root, corpo(item="5", acao="Remover"), NOW)
        self.assertTrue(ok, msg)
        self.assertIn("2 lotes", msg)
        self.assertEqual([i["asset_id"] for i in read_json(root, "carteira.json")["itens"]], [6])

    def texto(self, root):
        with open(os.path.join(root, "carteira.json"), encoding="utf-8") as f:
            return f.read()

    def test_erro_nao_altera_nada(self):
        root = tmp_root()
        write_carteira(root, [])
        antes = self.texto(root)
        for body in (corpo(preco="abc"), corpo(item="lixo"), corpo(item="99", acao="Remover"), ""):
            ok, msg, _ = cadastro.cadastrar(root, body, NOW)
            self.assertFalse(ok)
            self.assertIn("Não consegui", msg)
        self.assertEqual(self.texto(root), antes)



class TextoLivre(unittest.TestCase):
    """Issue aberta sem o formulário (link do site ou app do GitHub)."""

    def test_so_o_link(self):
        root = tmp_root()
        write_carteira(root, [])
        ok, msg, aid = cadastro.cadastrar(root, "https://www.roblox.com/pt/catalog/90254996174236/8-Bit-Crown", NOW,
                                          title="[carteira] 8-Bit Crown")
        self.assertTrue(ok, msg)
        self.assertEqual(aid, 90254996174236)
        lote = read_json(root, "carteira.json")["itens"][0]
        self.assertIsNone(lote["preco_pago"])
        self.assertEqual(lote["quantidade"], 1)

    def test_corpo_do_site(self):
        corpo_site = ("Adicionar\nItem: https://www.roblox.com/catalog/5551234\nPreço pago: 120\n"
                      "Quantidade: 2\nComprado em: 2026-10-01")
        f = cadastro.read_request("[carteira] Coroa · 5551234", corpo_site)
        v = cadastro.validate(f, NOW)
        self.assertEqual((v["acao"], v["asset_id"], v["preco_pago"], v["quantidade"], v["comprado_em"]),
                         ("adicionar", 5551234, 120, 2, "2026-10-01"))

    def test_id_so_no_titulo(self):
        v = cadastro.validate(cadastro.read_request("[carteira] Coroa · 5551234", "Comprei"), NOW)
        self.assertEqual(v["asset_id"], 5551234)

    def test_remover(self):
        v = cadastro.validate(cadastro.read_request("[carteira] Remover Coroa · 5551234",
                                                    "Remover\nItem: https://www.roblox.com/catalog/5551234"), NOW)
        self.assertEqual(v["acao"], "remover")

    def test_sem_item_erro(self):
        root = tmp_root()
        write_carteira(root, [])
        ok, msg, _ = cadastro.cadastrar(root, "Comprei", NOW, title="[carteira] Blue Valkyrie")
        self.assertFalse(ok)
        self.assertIn("link", msg)

    def test_preco_depois_substitui_acompanhamento(self):
        root = tmp_root()
        write_carteira(root, [])
        self.assertTrue(cadastro.cadastrar(root, "https://www.roblox.com/catalog/5551234", NOW)[0])
        ok, msg, _ = cadastro.cadastrar(root, "https://www.roblox.com/catalog/5551234", NOW)
        self.assertFalse(ok)  # repetir só o link não duplica
        ok, _, _ = cadastro.cadastrar(root, "Item: https://www.roblox.com/catalog/5551234\nPreço pago: 90", NOW)
        self.assertTrue(ok)
        itens = read_json(root, "carteira.json")["itens"]
        self.assertEqual([(i["asset_id"], i["preco_pago"]) for i in itens], [(5551234, 90)])


class Lojas(unittest.TestCase):
    def items(self, pairs):
        return [{"price": p, "lowest_resale": l, "units_remaining": r} for p, l, r in pairs]

    def test_estatisticas(self):
        st = lojas.compute_stats(self.items([(100, 200, 0), (100, 50, 0), (100, 400, 10), (100, None, 5),
                                             (100, 150, 0)]))
        self.assertEqual(st["items_seen"], 5)
        self.assertEqual(st["sold_out"], 3)
        self.assertEqual(st["with_resale"], 3)  # o anúncio de 400 num item ainda à venda não conta
        self.assertEqual(st["median_retention"], 1.5)  # mediana de 2,0 / 0,5 / 1,5
        self.assertAlmostEqual(st["pct_above_price"], 0.667, places=3)

    def test_sem_revenda_fica_null(self):
        st = lojas.compute_stats(self.items([(100, None, 3)]))
        self.assertIsNone(st["median_retention"])
        self.assertIsNone(st["pct_above_price"])

    def test_cache_de_7_dias(self):
        root = tmp_root()
        cli = FakeClient(NOW, seed=1, n=20)
        creators = {50: {"type": "User", "name": "Criador0"}, 51: {"type": "User", "name": "Criador1"}}
        lojas.update(root, cli, creators, NOW, CFG, [])
        self.assertEqual(cli.creator_calls, 2)
        lojas.update(root, cli, creators, NOW + timedelta(days=6, hours=23), CFG, [])
        self.assertEqual(cli.creator_calls, 2)  # cache ainda vale
        cache = lojas.update(root, cli, creators, NOW + timedelta(days=7, hours=1), CFG, [])
        self.assertEqual(cli.creator_calls, 4)  # venceu: busca de novo
        self.assertEqual(cache["50"]["items_seen"], 4)
        self.assertIn("updated_at", cache["50"])

    def test_limite_de_criadores_por_execucao(self):
        root, cfg = tmp_root(), json.loads(json.dumps(CFG))
        cfg["lojas"]["max_por_execucao"] = 2
        cli = FakeClient(NOW, seed=1, n=20)
        creators = {50 + i: {"type": "User", "name": f"C{i}"} for i in range(5)}
        cache = lojas.update(root, cli, creators, NOW, cfg, [])
        self.assertEqual(len(cache), 2)
        cache = lojas.update(root, cli, creators, NOW, cfg, [])
        self.assertEqual(len(cache), 4)  # os novos vêm antes dos já vistos

    def test_busca_falha_nao_derruba(self):
        root = tmp_root()
        cli = FakeClient(NOW, fail_catalog=True)
        errors = []
        self.assertEqual(lojas.update(root, cli, {50: {"type": "User", "name": "A"}}, NOW, CFG, errors), {})
        self.assertTrue(errors)

    def test_score_neutro_sem_dado_e_motivos(self):
        self.assertEqual(analyze.store_score(None, CFG), 0.5)
        self.assertEqual(analyze.store_score({"with_resale": 1, "median_retention": 3, "pct_above_price": 1}, CFG), 0.5)
        forte = {"with_resale": 8, "median_retention": 1.6, "pct_above_price": 0.8}
        fraca = {"with_resale": 8, "median_retention": 0.7, "pct_above_price": 0.1}
        self.assertGreater(analyze.store_score(forte, CFG), 0.9)
        self.assertEqual(analyze.store_score(fraca, CFG), 0.04)
        self.assertIn("bom histórico", analyze.store_reason(forte, CFG))
        self.assertIn("fraco", analyze.store_reason(fraca, CFG))
        self.assertIsNone(analyze.store_reason({"with_resale": 8, "median_retention": 1.1, "pct_above_price": 0.5}, CFG))

    def test_pesos_somam_100(self):
        self.assertEqual(sum(CFG["score_pesos"].values()), 100)


class RunCompleto(unittest.TestCase):
    def test_run_fake_gera_carteira_e_campos_novos(self):
        root = tmp_root()
        write_carteira(root, [
            {"asset_id": 1003, "preco_pago": 195, "quantidade": 1, "comprado_em": "2026-10-10", "nota": ""},
            {"asset_id": 1008, "preco_pago": None, "quantidade": 2, "comprado_em": "2026-10-17", "nota": "fora da categoria"}])
        res = run(root, client=FakeClient(NOW, days=90), now=NOW, notify=False)
        self.assertEqual(res["carteira"]["status"], "ok")
        cart = read_json(root, "docs", "carteira.json")
        self.assertEqual([i["asset_id"] for i in cart["items"]], [1003, 1008])
        a, b = cart["items"]
        for k in ("name", "creator_name", "category", "url", "thumbnail", "lots", "quantity", "original_price",
                  "avg_paid", "units_remaining", "total_quantity", "is_off_sale", "rap", "lowest_resale",
                  "volume_7d", "value_now", "cost_total", "pnl", "pnl_pct", "breakeven_rap", "retention",
                  "change_7d", "change_30d", "trend", "days_held", "series"):
            self.assertIn(k, a)
        self.assertEqual(a["breakeven_rap"], 390)
        self.assertEqual(b["category"], "outro")  # fora das categorias do radar, mas aceito na carteira
        self.assertIsNone(b["pnl"])
        self.assertEqual(cart["totals"]["items_counted"], 1)
        self.assertEqual(cart["totals"]["cost"], 195)
        self.assertTrue(a["series"]["chart"] and a["series"]["tracked"])
        self.assertTrue(os.path.exists(os.path.join(root, "data", "carteira", "1003.jsonl")))
        # radar: campos novos
        data = read_json(root, "docs", "data.json")
        it = data["items"][0]
        for k in ("creator_track", "retention", "change_7d", "trend", "spark"):
            self.assertIn(k, it)
        self.assertLessEqual(len(it["spark"]), 30)
        self.assertEqual(len(it["spark"][0]), 2)
        self.assertTrue(os.path.exists(os.path.join(root, "data", "criadores.json")))
        self.assertIsNotNone(it["creator_track"])

    def test_resale_exige_login_deixa_null_e_explica(self):
        root = tmp_root()
        write_carteira(root, [{"asset_id": 1003, "preco_pago": 195, "quantidade": 1, "comprado_em": "2026-10-10", "nota": ""}])
        run(root, client=FakeClient(NOW, resale_mode="auth"), now=NOW, notify=False)
        cart = read_json(root, "docs", "carteira.json")
        it = cart["items"][0]
        self.assertIsNone(it["rap"])
        self.assertIsNone(it["value_now"])
        self.assertIsNone(it["pnl"])
        self.assertIn("401/403", cart["status_note"])
        self.assertEqual(it["name"], "[FALSO] Item 3")

    def test_falha_da_carteira_nao_quebra_o_radar(self):
        root = tmp_root()
        with open(os.path.join(root, "carteira.json"), "w") as f:
            f.write("{quebrado")
        res = run(root, client=FakeClient(NOW), now=NOW, notify=False)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["carteira"]["status"], "error")
        self.assertTrue(res["items"])
        self.assertIn("carteira não foi atualizada", read_json(root, "docs", "carteira.json")["status_note"])

    def test_carteira_vazia(self):
        root = tmp_root()
        write_carteira(root, [])
        run(root, client=FakeClient(NOW), now=NOW, notify=False)
        cart = read_json(root, "docs", "carteira.json")
        self.assertEqual(cart["items"], [])
        self.assertIsNone(cart["totals"]["pnl"])


if __name__ == "__main__":
    unittest.main()
