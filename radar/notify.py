"""Alertas pelo ntfy. O tópico vem só da variável de ambiente NTFY_TOPIC (segredo do GitHub)."""
import json
import logging
import os
import urllib.request
from datetime import datetime, timezone

from .analyze import CLASS_RANK, alert_eligible, fmt_eta
from .storage import iso

log = logging.getLogger("radar.notify")
DISCLAIMER = "Não é recomendação financeira. Preços de itens virtuais variam muito."


def build_message(item, cat_labels):
    title = f"Oportunidade UGC: {item['name']}"[:120]
    lines = [
        f"{cat_labels.get(item['category'], item['category'])} · preço {item['price']} Robux",
        f"Restantes: {item['units_remaining']}/{item['total_quantity'] or '—'}",
        f"RAP {item['rap']} · lucro líquido est. {item['net_profit']:+.0f} ({item['net_margin']:+.0%})",
        f"Esgota em {fmt_eta(item['eta_hours'])} · vol. 7d {item['volume_7d']}",
        item["url"],
        DISCLAIMER,
    ]
    return title, "\n".join(lines)


def send_ntfy(server, topic, title, message, click=None, tags=None, priority=4, opener=None):
    payload = {"topic": topic, "title": title, "message": message, "priority": priority,
               "tags": tags or ["chart_with_upwards_trend"]}
    if click:
        payload["click"] = click
    req = urllib.request.Request(server.rstrip("/"), data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with (opener or urllib.request.urlopen)(req, timeout=15) as r:
            return 200 <= r.status < 300
    except Exception as e:  # nunca registra o tópico
        log.warning("ntfy falhou: %s", type(e).__name__)
        return False


def process_alerts(items, state, now, cfg, send=None, topic=None):
    """Decide e envia alertas. Devolve a lista de itens alertados.

    Uma vez por item; novo alerta só se a classe melhorar em relação ao último alerta.
    Limite diário em alertas.max_alerts_per_day.
    """
    a = cfg["alertas"]
    topic = topic if topic is not None else os.environ.get("NTFY_TOPIC", "").strip()
    if not a.get("ativo", True):
        return []
    send = send or (lambda **kw: send_ntfy(a["ntfy_server"], topic, **kw))
    labels = {c["key"]: c["label"] for c in cfg["categorias"]}
    today = now.strftime("%Y-%m-%d")
    alerts = state.setdefault("alerts", {})
    daily = state.setdefault("daily", {})
    sent = []
    for item in items:
        if not alert_eligible(item, cfg):
            continue
        key = str(item["asset_id"])
        prev = alerts.get(key)
        if prev and CLASS_RANK[item["class"]] <= CLASS_RANK.get(prev.get("class"), -1):
            continue
        if daily.get(today, 0) >= a["max_alerts_per_day"]:
            log.info("limite diário de alertas atingido")
            break
        if not topic:
            log.info("NTFY_TOPIC ausente: alerta não enviado para %s", key)
            continue
        title, msg = build_message(item, labels)
        if send(title=title, message=msg, click=item["url"]):
            alerts[key] = {"class": item["class"], "ts": iso(now), "net_margin": item["net_margin"]}
            daily[today] = daily.get(today, 0) + 1
            sent.append(item)
    return sent


def system_notice(state, now, status, note, cfg, send=None, topic=None):
    """Aviso de falha (ex.: API exigiu login) no máximo 1 vez por dia por tipo."""
    a = cfg["alertas"]
    topic = topic if topic is not None else os.environ.get("NTFY_TOPIC", "").strip()
    if not topic or not a.get("avisar_falhas", True):
        return False
    today = now.strftime("%Y-%m-%d")
    notices = state.setdefault("system_notices", {})
    done = notices.setdefault(today, [])
    if status in done:
        return False
    send = send or (lambda **kw: send_ntfy(a["ntfy_server"], topic, **kw))
    ok = send(title=f"Radar UGC: {status}", message=note, click=None, tags=["warning"], priority=3)
    if ok:
        done.append(status)
    return ok


def _outbox_path(root):
    return os.path.join(root, "data", "outbox.json")


def write_outbox(root, messages, now):
    """Mensagens a enviar depois do commit. Não contém o tópico."""
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    with open(_outbox_path(root), "w", encoding="utf-8") as f:
        json.dump({"generated_at": iso(now), "messages": messages}, f, ensure_ascii=False, indent=1)


def send_outbox(root, send=None, topic=None, now=None, max_age_min=60):
    """Envia o que a última execução deixou no outbox. Ignora outbox antigo."""
    try:
        with open(_outbox_path(root), encoding="utf-8") as f:
            box = json.load(f)
    except (OSError, ValueError):
        return 0
    now = now or datetime.now(timezone.utc)
    try:
        gen = datetime.fromisoformat(box["generated_at"].replace("Z", "+00:00"))
    except (KeyError, ValueError, AttributeError):
        return 0
    if (now - gen).total_seconds() > max_age_min * 60:
        log.info("outbox antigo (%s): nada enviado", box.get("generated_at"))
        return 0
    if send is None:
        topic = topic if topic is not None else os.environ.get("NTFY_TOPIC", "").strip()
        if not topic:
            log.info("NTFY_TOPIC ausente: nada enviado")
            return 0
        with open(os.path.join(root, "config.json"), encoding="utf-8") as f:
            server = json.load(f)["alertas"]["ntfy_server"]
        send = lambda **kw: send_ntfy(server, topic, **kw)  # noqa: E731
    ok = 0
    for m in box.get("messages", []):
        if send(**m):
            ok += 1
    log.info("alertas enviados: %d de %d", ok, len(box.get("messages", [])))
    return ok
