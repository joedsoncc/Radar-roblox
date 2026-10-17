# Contrato da carteira e do histórico das lojas

Complementa `CONTRATO-DADOS.md`. Tudo é gerado pelo `radar.py run`; o site só lê JSON.

## Entrada: `carteira.json` (raiz do repositório)

Lista dos itens que o Jhow comprou ou quer acompanhar. Editado à mão ou pelo workflow de cadastro (issue).

```json
{
  "itens": [
    {
      "asset_id": 90254996174236,
      "preco_pago": 195,          // Robux pagos por unidade; null = só acompanhar (não comprou)
      "quantidade": 1,
      "comprado_em": "2026-10-17", // data da compra (ou do cadastro, se só acompanhar)
      "nota": "texto livre curto"
    }
  ]
}
```

Regras: `asset_id` é o número da URL `roblox.com/catalog/<asset_id>`. Itens repetidos (mesmo `asset_id`) são somados como lotes separados.

## Histórico por item: `data/carteira/<asset_id>.jsonl`

Uma linha por execução para cada item da carteira (mesmo que esteja fora dos filtros do radar):
`{"ts", "price", "units_remaining", "total_quantity", "rap", "lowest_resale", "resale_avg_low", "volume_7d", "is_off_sale"}`.

## Saída: `docs/carteira.json`

```json
{
  "generated_at": "2026-10-17T08:17:00Z",
  "status_note": "",
  "totals": {"cost": 195, "value_now": 97.5, "pnl": -97.5, "pnl_pct": -0.5},
  "items": [
    {
      "asset_id": 90254996174236,
      "name": "8-Bit Royal Crown", "creator_name": "X", "category": "hat",
      "url": "https://www.roblox.com/catalog/90254996174236", "thumbnail": "https://... ou null",
      "lots": [{"preco_pago": 195, "quantidade": 1, "comprado_em": "2026-10-17", "nota": ""}],
      "quantity": 1,
      "original_price": 195,       // preço de loja (catálogo)
      "avg_paid": 195,             // média ponderada dos lotes com preço; null se só acompanha
      "units_remaining": 50, "total_quantity": 3000, "is_off_sale": false,
      "rap": 195, "lowest_resale": 210, "volume_7d": 40,
      "resale_avg_low": 230, "resale_avg_n": 10, // média dos N anúncios mais baratos (até 10; 1 = só o menor do catálogo)
      "sale_ref": 195, "sale_ref_source": "rap", // menor entre RAP e resale_avg_low ("rap" | "anuncios")
      "value_now": 97.5,           // quanto receberia vendendo tudo: sale_ref × 0,5 × quantidade
      "cost_total": 195,           // avg_paid × quantidade (sem margem 1,11: é o que já foi pago)
      "pnl": -97.5, "pnl_pct": -0.5,
      "breakeven_rap": 390,        // RAP necessário para empatar: avg_paid / 0,5
      "retention": 1.0,            // RAP / original_price (1,0 = mantém o preço de loja)
      "change_7d": 0.05,           // variação da mediana do gráfico: últimos 7 dias × 7 dias anteriores
      "change_30d": -0.10,         // últimos 30 dias × 30 dias anteriores
      "trend": "subindo | estável | caindo | sem dados",
      "days_held": 0,
      "series": {
        "chart":   [["2026-10-01", 180, 12]],            // data, preço médio do dia, volume (até 180 dias, da revenda)
        "tracked": [["2026-10-17T06:00:00Z", 195, 210, 50]] // ts, RAP, média dos menores anúncios, restantes (nossas coletas)
      }
    }
  ]
}
```

`trend`: `subindo` se change_7d ≥ +5%, `caindo` se ≤ −5%, senão `estável`; `sem dados` com menos de 3 dias de venda.
Qualquer número pode ser `null`; o site mostra "—".

## Histórico das lojas (criadores): `data/criadores.json`

Cache por criador (renovado a cada 7 dias) com os outros limiteds do mesmo criador no catálogo:
`{"<creator_id>": {"updated_at", "name", "items_seen", "sold_out", "with_resale", "median_retention", "pct_above_price"}}`

- `median_retention`: mediana de (menor revenda ÷ preço original) dos limiteds dele com revenda.
- `pct_above_price`: fração desses itens com menor revenda acima do preço original.

Cada item do radar (`docs/data.json`) ganha:
`creator_track` (o objeto acima, ou null), `retention` (RAP ÷ preço), `change_7d`, `trend` e
`spark` (até 30 pares `[data, preço]` do gráfico de revenda, para o mini-gráfico do card).
O score ganha um peso `historico_loja` em `config.json` (criador com boa retenção sobe; sem dado fica neutro).
