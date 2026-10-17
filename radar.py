#!/usr/bin/env python3
"""Radar de UGC Limiteds do Roblox (somente análise; nunca compra ou vende).

Uso:
  python radar.py run                 # coleta real + site + alertas (NTFY_TOPIC no ambiente)
  python radar.py run --no-notify     # sem alertas
  python radar.py run --fake --root /tmp/teste   # dados falsos, sem internet
  python radar.py send                # envia os alertas guardados em data/outbox.json (depois do commit)
  python radar.py notice "texto"      # aviso de falha do workflow pelo ntfy
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
    r.add_argument("--fake", action="store_true", help="usa dados falsos (não acessa a internet)")
    r.add_argument("--root", default=HERE, help="pasta do projeto (config.json, data/, docs/)")
    sub.add_parser("send")
    nt = sub.add_parser("notice")
    nt.add_argument("text")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.cmd == "send":
        send_outbox(HERE)
        return 0
    if args.cmd == "notice":
        topic = os.environ.get("NTFY_TOPIC", "").strip()
        if topic:
            send_ntfy(load_config(HERE)["alertas"]["ntfy_server"], topic, title="Radar UGC: falha",
                      message=args.text[:500], tags=["warning"], priority=3)
        return 0

    client = None
    if args.fake:
        if os.path.abspath(args.root) == HERE:
            sys.exit("--fake precisa de --root em outra pasta para não sujar o histórico real.")
        os.makedirs(args.root, exist_ok=True)
        shutil.copy(os.path.join(HERE, "config.json"), os.path.join(args.root, "config.json"))
        from radar.fake import FakeClient
        client = FakeClient(datetime.now(timezone.utc))

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
