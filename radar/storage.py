"""Histórico de snapshots (JSONL por dia) e estado dos alertas."""
import json
import os
from datetime import datetime, timedelta, timezone

SNAPSHOT_FIELDS = [
    "ts", "asset_id", "collectible_item_id", "name", "creator_name", "creator_id",
    "creator_verified", "category", "asset_type_id", "price", "total_quantity",
    "units_remaining", "rap", "lowest_resale", "resale_avg_low", "resale_avg_n", "volume_7d", "volume_30d",
    "last_chart_price", "last_chart_date", "chart_median_14d", "chart_points_14d", "resale_status",
]


class Storage:
    def __init__(self, root):
        self.root = root
        self.snap_dir = os.path.join(root, "data", "snapshots")
        self.state_path = os.path.join(root, "data", "state.json")

    def append_snapshots(self, rows, now):
        os.makedirs(self.snap_dir, exist_ok=True)
        path = os.path.join(self.snap_dir, now.strftime("%Y-%m-%d") + ".jsonl")
        with open(path, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps({k: r.get(k) for k in SNAPSHOT_FIELDS}, ensure_ascii=False) + "\n")
        return path

    def load_recent(self, now, days):
        rows = []
        if not os.path.isdir(self.snap_dir):
            return rows
        cut = now - timedelta(days=days)
        for d in range(days + 1, -1, -1):
            day = (now - timedelta(days=d)).strftime("%Y-%m-%d")
            path = os.path.join(self.snap_dir, day + ".jsonl")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
                    except (ValueError, KeyError, TypeError):
                        continue
                    if ts >= cut:
                        r["_ts"] = ts
                        rows.append(r)
        rows.sort(key=lambda r: r["_ts"])
        return rows

    def load_state(self):
        try:
            with open(self.state_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"alerts": {}, "daily": {}, "system_notices": {}}

    def save_state(self, state, now):
        # Mantém só os últimos 14 dias de contadores diários.
        keep = {(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)}
        state["daily"] = {k: v for k, v in state.get("daily", {}).items() if k in keep}
        state["system_notices"] = {k: v for k, v in state.get("system_notices", {}).items() if k in keep}
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
