# Roblox UGC Limited Radar

Read-only tracker for Roblox UGC Limited accessories that are close to selling out. Every 2 hours a GitHub Actions job collects public catalog and resale data, stores snapshots, scores each item (BUY-NOW / WATCH / AVOID in Portuguese), publishes a static PWA from `docs/` on GitHub Pages and sends ntfy push alerts for strong opportunities.

It never buys, sells, lists items or uses account credentials. Not financial advice.

Setup instructions are in Portuguese in [LEIAME.md](LEIAME.md). Run tests with `python -m unittest discover -s tests`.
