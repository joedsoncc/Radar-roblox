#!/usr/bin/env python3
"""Radar de UGC Limiteds do Roblox (somente análise; nunca compra ou vende).

Uso:
  python radar.py run                 # coleta real + site + alertas (NTFY_TOPIC no ambiente)
  python radar.py run --no-notify     # sem alertas
  python radar.py run --fake --root /tmp/teste   # dados falsos, sem internet
  python radar.py carteira            # só a carteira (workflow de cadastro); aceita --fake --root
  python radar.py cadastrar           # lê o corpo da issue em ISSUE_BODY e atualiza carteira.json
  python radar.py send                # envia os alertas guardados em data/outbox.json (depois do commit)
  python radar.py launches            # vigia lançamentos de limiteds da Roblox oficial
  python radar.py send --outbox launch_outbox.json
  python radar.py notice "texto"      # aviso de falha do workflow pelo ntfy
  python radar.py amplo               # uma rodada da coleta ampla (calibração); aceita --fake --root
  python radar.py visual              # aparência dos mais revendidos (miniaturas, cores); --sem-coleta só analisa
  python radar.py calibrar            # backtest: quais sinais previram margem >= 30% (data/calibracao.md)
"""
import argparse
import logging
import os
import shutil
import sys
from datetime import datetime, timezone

from radar.notify import send_ntfy, send_outbox
from radar.runner import load_config, run

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--no-notify", action="store_true")
    for p in (r, sub.add_parser("carteira")):
        p.add_argument("--fake", action="store_true", help="usa dados falsos (não acessa a internet)")
        p.add_argument("--root", default=HERE, help="pasta do projeto (config.json, data/, docs/)")
    cart = sub.choices["carteira"]
    cart.add_argument("--asset", type=int, help="item a resumir em --anexar")
    cart.add_argument("--anexar", help="arquivo de texto onde acrescentar uma linha sobre --asset")
    cd = sub.add_parser("cadastrar")
    cd.add_argument("--mensagem", default="cadastro_resultado.md", help="arquivo onde gravar a resposta para a issue")
    sd = sub.add_parser("send")
    sd.add_argument("--outbox", default="outbox.json")
    sub.add_parser("launches")
    am = sub.add_parser("amplo")
    am.add_argument("--fake", action="store_true")
    am.add_argument("--root", default=HERE)
    cb = sub.add_parser("calibrar")
    cb.add_argument("--root", default=HERE)
    vs = sub.add_parser("visual")
    vs.add_argument("--root", default=HERE)
    vs.add_argument("--sem-coleta", action="store_true", help="não acessa a internet; usa o que já está em data/visual")
    nt = sub.add_parser("notice")
    nt.add_argument("text")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.cmd == "send":
        send_outbox(HERE, name=args.outbox)
        return 0
    if args.cmd == "launches":
        from radar import launches
        from radar.http import Client
        cfg = load_config(HERE)
        col = cfg["coleta"]
        launches.run(HERE, Client(col["request_delay_s"], 2, col["timeout_s"]), cfg)
        return 0
    if args.cmd == "notice":
        topic = os.environ.get("NTFY_TOPIC", "").strip()
        if topic:
            send_ntfy(load_config(HERE)["alertas"]["ntfy_server"], topic, title="Radar UGC: falha",
                      message=args.text[:500], tags=["warning"], priority=3)
        return 0

    if args.cmd == "cadastrar":
        return cadastrar(args.mensagem)
    if args.cmd == "calibrar":
        from radar import calibrar
        calibrar.run(args.root, load_config(args.root), datetime.now(timezone.utc).replace(microsecond=0))
        return 0

    if args.cmd == "visual":
        from radar import visual
        from radar.http import Client
        col = load_config(args.root)["coleta"]
        client = None if args.sem_coleta else Client(col["request_delay_s"], col["max_retries"], col["timeout_s"])
        res = visual.run(args.root, client)
        print(f"visual: {res['itens']} itens; erros: {len(res['erros'])}")
        if res["erros"]:
            print(f"::warning title=Visual::{'; '.join(res['erros'][:10])}")
        return 0

    client = None
    if args.fake:
        if os.path.abspath(args.root) == HERE:
            sys.exit("--fake precisa de --root em outra pasta para não sujar o histórico real.")
        os.makedirs(args.root, exist_ok=True)
        shutil.copy(os.path.join(HERE, "config.json"), os.path.join(args.root, "config.json"))
        dest = os.path.join(args.root, "carteira.json")
        if not os.path.exists(dest) and os.path.exists(os.path.join(HERE, "carteira.json")):
            shutil.copy(os.path.join(HERE, "carteira.json"), dest)
        from radar.fake import FakeClient
        client = FakeClient(datetime.now(timezone.utc), days=90)

    if args.cmd == "amplo":
        from radar import amplo
        from radar.http import Client
        cfg = load_config(args.root)
        col = cfg["coleta"]
        client = client or Client(col["request_delay_s"], col["max_retries"], col["timeout_s"])
        res = amplo.rodada(args.root, client, datetime.now(timezone.utc).replace(microsecond=0), cfg)
        if res["erros"]:
            print(f"::warning title=Coleta ampla::{'; '.join(res['erros'])}")
        return 0

    if args.cmd == "carteira":
        from radar import carteira
        from radar.http import Client
        cfg = load_config(args.root)
        col = cfg["coleta"]
        client = client or Client(col["request_delay_s"], col["max_retries"], col["timeout_s"])
        res = carteira.run(args.root, client, datetime.now(timezone.utc).replace(microsecond=0), cfg)
        if res["status"] != "ok":
            print(f"::warning title=Carteira ({res['status']})::{res['note']}")
        if args.anexar and args.asset:
            with open(args.anexar, "a", encoding="utf-8") as f:
                f.write("\n" + carteira.summary_line(res, args.asset) + "\n")
        return 0

    try:
        res = run(args.root, client=client, notify=not args.no_notify and not args.fake)
    except Exception as e:  # falha inesperada: registra no site em vez de sumir em silêncio
        logging.exception("falha inesperada")
        mark_site_error(args.root, f"Falha inesperada na execução ({type(e).__name__}). Itens exibidos são da coleta anterior.")
        raise
    if res["status"] in ("auth_required", "error"):
        # Anotação visível na página do GitHub Actions.
        print(f"::warning title=Radar UGC ({res['status']})::{res['note']}")
    return 0


def cadastrar(msg_path):
    """Cadastro por issue. O corpo vem de ISSUE_BODY e o título de ISSUE_TITLE (variáveis de ambiente, nunca da linha de comando).

    Sempre sai com 0; o resultado vai para o arquivo de mensagem e para `ok=true|false` em GITHUB_OUTPUT.
    """
    from radar import cadastro
    ok, msg, aid = cadastro.cadastrar(HERE, os.environ.get("ISSUE_BODY", ""), title=os.environ.get("ISSUE_TITLE", ""))
    with open(msg_path, "w", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"ok={'true' if ok else 'false'}\nasset_id={aid or ''}\n")
    return 0


def mark_site_error(root, note):
    import json
    from radar.storage import iso
    path = os.path.join(root, "docs", "data.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    data["run_status"] = "error"
    data["status_note"] = note + f" (última coleta boa: {data.get('generated_at')})"
    data["error_at"] = iso(datetime.now(timezone.utc))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())
