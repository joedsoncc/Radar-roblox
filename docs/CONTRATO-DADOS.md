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
      "resale_avg_low": 318.5,
      "resale_avg_n": 10,
      "sale_ref": 260,
      "sale_ref_source": "rap | anuncios | historico_loja | null",
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
      "data_quality": "ok | sem_rap | rap_primario | sem_velocidade | rap_incoerente",
      "creator_track": {"updated_at": "2026-10-15T08:00:00Z", "name": "Criador", "items_seen": 12, "sold_out": 5,
                        "with_resale": 9, "median_retention": 1.4, "pct_above_price": 0.67},
      "retention": 2.6,
      "change_7d": 0.08,
      "trend": "subindo | estável | caindo | sem dados",
      "spark": [["2026-10-01", 240], ["2026-10-03", 255]]
    }
  ]
}
```

Histórico da loja e tendência (campos novos):
- `creator_track`: resumo dos outros limiteds do mesmo criador (cache de 7 dias em `data/criadores.json`), ou `null` se ainda não foi consultado. `median_retention` = mediana de (menor revenda ÷ preço original) só dos itens já esgotados (enquanto a loja vende, anúncio não é preço); `pct_above_price` = fração desses com menor revenda acima do preço original; ambos `null` se nenhum item esgotado dele tem revenda. `metodo` = 2 (registros sem ele são recalculados). Detalhes em `CONTRATO-CARTEIRA.md`.
- `retention`: RAP ÷ preço de loja (1,0 = mantém o preço).
- `change_7d`: variação da mediana do gráfico, últimos 7 dias × 7 dias anteriores (0,08 = +8%).
- `trend`: `subindo` (≥ +5%), `caindo` (≤ −5%), `estável`, ou `sem dados` (menos de 3 dias de venda em 14 dias).
- `spark`: até 30 pares `[data, preço médio do dia]` do gráfico de revenda, do mais antigo ao mais novo (lista vazia sem gráfico).
- O score ganhou o peso `historico_loja` (config `score_pesos`); sem dado da loja vale 0,5 (neutro). `reasons` pode trazer uma frase sobre loja com histórico forte ou fraco.

Anúncios: `lowest_resale` é o menor anúncio do catálogo; `resale_avg_low` é a média dos `resale_avg_n` anúncios mais baratos (até 10; `resale_avg_n` = 1 quando só havia o menor anúncio do catálogo, 0 sem anúncio). `sale_ref` é o valor de venda usado no lucro (menor entre `rap` e `resale_avg_low`) e `sale_ref_source` diz de onde veio. Quando o item ainda está à venda e o RAP está a até 15% do preço de loja (`rap_primary: true`, as vendas da loja formam o RAP), `sale_ref` = preço × `creator_track.median_retention` (`historico_loja`), ou `null` sem histórico da loja.

Campos de risco (pesquisa de 2026-10-17): `rap_primary` (bool); `copy_risk` (termo de item clássico achado no nome, ou `null`); `price_raised_from` (menor preço de loja visto antes, se o criador subiu o preço; senão `null`); `break_even` (preço de venda que só empata: custo ÷ 0,5); `hold_days` (trava de revenda no pior caso, 30).

Regras: qualquer campo numérico pode ser `null` quando a API falhou ou ainda não há snapshots suficientes. O site deve mostrar "—" e nunca inventar valor.
