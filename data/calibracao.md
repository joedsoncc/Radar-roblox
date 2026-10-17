# Calibração do radar (2026-10-17T20:10:15Z)

Backtest: quem comprou no preço original e vendeu depois da trava de 30 dias (mediana do gráfico 30 a 37 dias depois de esgotar), com as taxas do radar (recebe 50%, custo ×1,11). Acerto = margem líquida ≥ 30%.

- Itens com histórico coletado: **1200**
- Com desfecho (37+ dias depois de esgotar, item pago): **446**
- Ainda sem desfecho: 78
- **Taxa geral de acerto: 8%** (36 de 446)

Faixas com menos de 20 itens aparecem com ⚠ (amostra pequena, não use para decidir).

## Preço original

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 51 a 100 | 54 | 33% | -47% | 4.13 |
| até 50 | 46 | 9% | -37% | 1.08 |
| 101 a 250 | 64 | 5% | -55% | 0.58 |
| 251 a 500 | 48 | 4% | -26% | 0.52 |
| acima de 500 | 234 | 4% | -55% | 0.48 |

## Estoque total

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 2.001 a 10.000 un. | 54 | 32% | -33% | 3.9 |
| 101 a 500 un. | 25 | 8% | -48% | 0.99 |
| até 100 un. | 180 | 7% | -55% | 0.83 |
| acima de 10.000 un. | 177 | 3% | -40% | 0.35 |
| 501 a 2.000 un. ⚠ | 10 | 0% | -49% | 0.0 |

## Categoria

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| front ⚠ | 3 | 33% | -19% | 4.13 |
| neck | 22 | 14% | -55% | 1.69 |
| face | 45 | 9% | -44% | 1.1 |
| shoulder | 23 | 9% | -50% | 1.08 |
| back | 60 | 8% | -55% | 1.03 |
| hat | 275 | 7% | -52% | 0.9 |
| hair ⚠ | 16 | 6% | -55% | 0.77 |
| waist ⚠ | 2 | 0% | -50% | 0.0 |

## Criador verificado

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 177 | 15% | -55% | 1.89 |
| sim | 269 | 3% | -46% | 0.41 |

## Favoritos por unidade

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| < 1 favorito/un. | 205 | 10% | -45% | 1.27 |
| 1 a 5 favoritos/un. | 71 | 8% | -44% | 1.05 |
| 5+ favoritos/un. | 170 | 5% | -55% | 0.66 |

## Preço da 1ª semana de revenda ÷ preço original (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 4x ou mais ⚠ | 14 | 79% | +150% | 9.73 |
| 2,5x a 4x ⚠ | 13 | 31% | -31% | 3.81 |
| 1,5x a 2,5x | 31 | 29% | -10% | 3.6 |
| < 1,5x o preço | 263 | 4% | -53% | 0.47 |

## Vendas na 1ª semana de revenda (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 100 a 499 vendas | 65 | 12% | -26% | 1.52 |
| 500+ vendas | 115 | 10% | -46% | 1.29 |
| 20 a 99 vendas | 49 | 6% | -43% | 0.76 |
| < 20 vendas | 217 | 6% | -55% | 0.74 |

## Estoque ≥ 1.000 e preço ≤ 250 (regra antiga do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| sim | 133 | 16% | -45% | 1.96 |
| não | 313 | 5% | -55% | 0.59 |

## Estoque acima de 10.000 (regra EVITAR do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 269 | 12% | -55% | 1.43 |
| sim | 177 | 3% | -40% | 0.35 |

## Curva depois de esgotar (preço mediano ÷ preço original)

Início = 1º dia em que o preço saiu de ±15% do preço de loja (≈ quando esgotou). Inclui itens ainda sem desfecho.

| Grupo | +1 dia | +7 dias | +30 dias |
|---|---|---|---|
| todos | 1.01x (n=301) | 1.23x (n=230) | 1.19x (n=262) |
| 101 a 250 | 1.00x (n=50) | 0.97x (n=45) | 0.99x (n=49) |
| 251 a 500 | 1.01x (n=36) | 1.26x (n=30) | 1.83x (n=33) |
| 51 a 100 | 2.28x (n=95) | 3.47x (n=81) | 1.74x (n=51) |
| acima de 500 | 1.00x (n=97) | 1.14x (n=67) | 1.36x (n=84) |
| até 50 | 0.00x (n=23) | 1.00x (n=7) | 1.09x (n=45) |
| 101 a 500 un. | 1.04x (n=3) | 1.73x (n=3) | 1.07x (n=4) |
| 2.001 a 10.000 un. | 2.00x (n=106) | 2.95x (n=91) | 1.65x (n=59) |
| 501 a 2.000 un. | 1.12x (n=10) | 1.35x (n=8) | 1.03x (n=7) |
| acima de 10.000 un. | 1.00x (n=150) | 1.09x (n=122) | 1.15x (n=176) |
| até 100 un. | 0.00x (n=32) | 1.31x (n=6) | 1.00x (n=16) |

## Melhores desfechos

| Item | Preço | Venda dia 30 | Margem |
|---|---|---|---|
| [Nuke Chain](https://www.roblox.com/catalog/13832615792) | 200 | 5000 | +1026% |
| [Pepper](https://www.roblox.com/catalog/13850956216) | 5000 | 100069 | +802% |
| [⌛ Stormbreaker Horns](https://www.roblox.com/catalog/121976686814942) | 95 | 1558 | +639% |
| [[⏳LIMITED Classic] White Sparkle Time Fedora](https://www.roblox.com/catalog/83446680555913) | 95 | 1476 | +600% |
| [Blue Valk](https://www.roblox.com/catalog/124270180080726) | 95 | 1461 | +593% |
| [Emperor Top Hat](https://www.roblox.com/catalog/13742588059) | 3333 | 50000 | +576% |
| [[ANIMATED] Twinkling Star Aura](https://www.roblox.com/catalog/75260672285911) | 55 | 753 | +517% |
| [Rainbow Electric Face Mask](https://www.roblox.com/catalog/14010092071) | 35 | 455 | +486% |
| [Stellar Dominus](https://www.roblox.com/catalog/102708321894339) | 95 | 1022 | +385% |
| [Black Neck Ribbon](https://www.roblox.com/catalog/15905629786) | 3000 | 30000 | +350% |

> Passado não garante futuro. Lift só vale com amostra grande; um dia de coleta é ponto de partida.
