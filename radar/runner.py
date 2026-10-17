"""Uma execução completa: coleta -> histórico -> análise -> site -> notificação."""
import json
import logging
import os
import time
from datetime import datetime, timezone

from . import calibrar, carteira, collect, lojas
from .analyze import analyze
from .http import Client
from .notify import process_alerts, send_outbox, system_notice, write_outbox
from .site import build_payload, write_site
from .storage import Storage, iso

log = logging.getLogger("radar")


def load_config(root):
    with open(os.path.join(root, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def in_scope(item, cfg):
    p = cfg["perfil"]
    rem, price = item.get("units_remaining"), item.get("price")
    return (price is not None and 0 < price <= p["max_price"]
            and rem is not None and p["min_remaining"] <= rem < p["max_remaining"]
            and not item.get("is_off_sale"))


def run(root, client=None, now=None, notify=True, send=None, topic=None):
    cfg = load_config(root)
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    col = cfg["coleta"]
    client = client or Client(col["request_delay_s"], col["max_retries"], col["timeout_s"])
    store = Storage(root)
    errors = []

    history = store.load_recent(now, max(col["watch_days"], 2))
    found = collect.search_catalog(client, cfg, errors)
    log.info("catálogo: %d acessórios collectible", len(found))

    watched = {r["asset_id"] for r in history} - set(found)
    if watched:
        found.update(collect.fetch_details(client, watched, cfg, errors))

    current = sorted((i for i in found.values() if in_scope(i, cfg)),
                     key=lambda i: i["units_remaining"])
    log.info("dentro dos filtros: %d", len(current))

    statuses = {"ok": 0, "auth_required": 0, "error": 0, "skipped": 0}
    started = time.monotonic()
    consecutive_errors = 0
    stop_reason = None
    n_listings = col.get("anuncios_media", 10)
    listings_status = {"ok": 0, "auth_required": 0, "error": 0}
    listings_stop = False
    for n, item in enumerate(current):
        if stop_reason or n >= col["max_resale_lookups"]:
            item["resale_status"] = "auth_required" if stop_reason == "auth" else "skipped"
            statuses[item["resale_status"]] += 1
            continue
        if time.monotonic() - started > col.get("resale_time_budget_s", 780):
            stop_reason = "tempo"
            item["resale_status"] = "skipped"
            statuses["skipped"] += 1
            continue
        summary, st = collect.fetch_resale(client, item, now)
        item["resale_status"] = st
        statuses[st] += 1
        if summary:
            item.update(summary)
        if st == "auth_required":
            # A API passou a exigir login: paramos todas as chamadas de histórico (sem contorno).
            stop_reason = "auth"
        if st == "ok" and n_listings and not listings_stop:
            lst, lst_st = collect.fetch_listings(client, item, n_listings)
            listings_status[lst_st] += 1
            if lst:
                item.update(lst)
            if lst_st == "auth_required":
                listings_stop = True  # anúncios pedem login: usamos só o menor anúncio do catálogo
        consecutive_errors = consecutive_errors + 1 if st == "error" else 0
        if consecutive_errors >= col.get("max_consecutive_errors", 5):
            stop_reason = "erros"
            errors.append(f"histórico: {consecutive_errors} falhas seguidas, coleta interrompida")
    for item in current:
        for k in ("rap", "volume_7d", "volume_30d", "last_chart_price", "last_chart_date"):
            item.setdefault(k, None)
        if "resale_avg_n" not in item:
            # Sem a lista de anúncios: o menor anúncio do catálogo vira "média de 1".
            low = item.get("lowest_resale")
            item["resale_avg_low"], item["resale_avg_n"] = (low, 1) if low else (None, 0)

    thumbs = collect.fetch_thumbnails(client, [i["asset_id"] for i in current], errors) if current else {}
    for item in current:
        item["thumbnail"] = thumbs.get(item["asset_id"])
        item["ts"] = iso(now)

    if current:
        store.append_snapshots(current, now)
        history = store.load_recent(now, max(col["watch_days"], 2))

    # Histórico das lojas: se falhar, o radar segue com o peso neutro (sem dado).
    tracks = {}
    try:
        creators = {i["creator_id"]: {"type": i.get("creator_type"), "name": i.get("creator_name")}
                    for i in current if i.get("creator_id") is not None}
        tracks = lojas.update(root, client, creators, now, cfg, [])
    except Exception:  # noqa: BLE001
        log.exception("histórico das lojas falhou; seguindo sem ele")

    items = analyze(current, history, now, cfg, tracks=tracks, lifts=calibrar.load_lifts(root))

    # Status da execução
    if not found and errors:
        run_status = "error"
        note = "Falha ao consultar o catálogo do Roblox: " + "; ".join(sorted(set(errors)))
    elif statuses["auth_required"]:
        run_status = "auth_required"
        note = ("A API de histórico (resale-data) respondeu 401/403: exige login. "
                f"Coleta de histórico interrompida; {statuses['ok']} itens tinham dados antes disso. "
                "Itens sem RAP não recebem recomendação de compra e nenhum alerta de oportunidade foi enviado.")
    elif errors or statuses["error"]:
        run_status = "partial"
        note = (f"Coleta parcial: {statuses['error']} falhas no histórico; "
                f"outros erros: {'; '.join(sorted(set(errors))) or 'nenhum'}.")
    else:
        run_status = "ok"
        note = ""
    if listings_status["auth_required"]:
        note = (note + " A lista de anúncios pediu login; a média usa só o menor anúncio do catálogo.").strip()
    if statuses["skipped"]:
        note = (note + f" {statuses['skipped']} itens ficaram sem histórico por limite de chamadas.").strip()

    snaps = len({r["ts"] for r in history})
    payload = build_payload(items, cfg, iso(now), run_status, note, snaps)
    if run_status == "error":
        # Mantém os itens anteriores no site e só atualiza o aviso.
        prev_path = os.path.join(root, "docs", "data.json")
        try:
            with open(prev_path, encoding="utf-8") as f:
                prev = json.load(f)
            payload["items"] = prev.get("items", [])
            payload["status_note"] = note + f" Itens exibidos são da coleta de {prev.get('generated_at')}."
        except (OSError, ValueError):
            pass
    write_site(root, payload)

    # Alertas: decididos e marcados no estado AGORA, mas só enviados depois do commit
    # (passo `radar.py send`), para que um push perdido não gere alerta repetido.
    state = store.load_state()
    outbox = []
    queue = lambda **kw: outbox.append(kw) or True  # noqa: E731
    topic = topic if topic is not None else os.environ.get("NTFY_TOPIC", "").strip()
    sent = []
    if notify and run_status in ("ok", "partial"):
        sent = process_alerts(items, state, now, cfg, send=queue, topic=topic)
    if notify and run_status in ("auth_required", "error"):
        system_notice(state, now, run_status, note, cfg, send=queue, topic=topic)
    store.save_state(state, now)
    write_outbox(root, outbox, now)
    if send is not None:
        send_outbox(root, send=send, now=now)

    # Carteira depois do radar: uma falha aqui nunca derruba o radar.
    cart = {"status": "error", "note": ""}
    try:
        cart = carteira.run(root, client, now, cfg)
    except Exception as e:  # noqa: BLE001
        log.exception("carteira falhou")
        cart = {"status": "error", "note": f"A carteira não foi atualizada ({type(e).__name__}); valores são da coleta anterior."}
        try:
            carteira.mark_error(root, cart["note"])
        except Exception:  # noqa: BLE001
            log.exception("não consegui anotar o erro da carteira")

    log.info("status=%s itens=%d alertas=%d chamadas=%d", run_status, len(items), len(sent), client.calls)
    return {"status": run_status, "note": note, "items": items, "alerts": sent, "statuses": statuses,
            "listings": listings_status, "carteira": cart}
