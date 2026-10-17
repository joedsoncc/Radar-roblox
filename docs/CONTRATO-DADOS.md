# Contrato do arquivo `docs/data.json`

Gerado por `radar.py` a cada execução. O site só lê este arquivo (nada de chamadas ao Roblox no navegador).

```json
{
  "generated_at": "2026-10-17T08:17:00Z",
  "run_status": "ok | partial | auth_required | error",
  "status_note": "texto curto em PT-BR explicando falhas (ex.: API de histórico exigiu login)",
  "snapshots_count": 14,
  "disclaimer": "Não é recomendação financeira...",
  "config": {"max_price": 500, "max_remaining": 100, "fee_multiplier": 1.11, "seller_share": 0.5},
  "categories": [
    {"key": "hat", "label": "Chapéu/Coroa", "asset_type_ids": [8]}
  ],
  "items": [
    {
      "asset_id": 123,
      "name": "Nome",
      "creator_name": "Criador",
      "creator_verified": true,
      "category": "hat",
      "url": "https://www.roblox.com/catalog/123",
      "thumbnail": "https://tr.rbxcdn.com/....png ou null",
      "price": 100,
      "total_quantity": 500,
      "units_remaining": 40,
      "pct_sold": 92.0,
      "rap": 260,
      "lowest_resale": 300,
      "volume_7d": 120,
      "volume_30d": 400,
      "last_chart_price": 250,
      "last_chart_date": "2026-10-16",
      "rap_consistent": true,
      "cost": 111.0,
      "net_profit": 19.0,
      "net_margin": 0.171,
      "velocity_per_hour": 2.5,
      "eta_hours": 16.0,
      "score": 63,
      "class": "COMPRAR-AGORA | OBSERVAR | EVITAR",
      "reasons": ["frase curta", "..."],
      "invalidators": ["o que invalidaria", "..."],
      "data_quality": "ok | sem_rap | sem_velocidade | rap_incoerente"
    }
  ]
}
```

Regras: qualquer campo numérico pode ser `null` quando a API falhou ou ainda não há snapshots suficientes. O site deve mostrar "—" e nunca inventar valor.
