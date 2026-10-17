# Calibração do radar (2026-10-17T20:40:12Z)

Backtest: quem comprou no preço original e vendeu depois da trava de 30 dias (mediana do gráfico 30 a 37 dias depois de esgotar), com as taxas do radar (recebe 50%, custo ×1,11). Acerto = margem líquida ≥ 30%.

- Itens com histórico coletado: **2100**
- Com desfecho (37+ dias depois de esgotar, item pago): **787**
- Ainda sem desfecho: 86
- **Taxa geral de acerto: 8%** (59 de 787)

Faixas com menos de 20 itens aparecem com ⚠ (amostra pequena, não use para decidir).

## Preço original

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 51 a 100 | 70 | 29% | -55% | 3.81 |
| até 50 | 46 | 9% | -37% | 1.16 |
| acima de 500 | 518 | 5% | -55% | 0.72 |
| 101 a 250 | 84 | 5% | -55% | 0.64 |
| 251 a 500 | 69 | 4% | -36% | 0.58 |

## Estoque total

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 2.001 a 10.000 un. | 55 | 31% | -36% | 4.12 |
| até 100 un. | 446 | 7% | -55% | 0.9 |
| 101 a 500 un. | 92 | 6% | -55% | 0.87 |
| acima de 10.000 un. | 183 | 3% | -42% | 0.44 |
| 501 a 2.000 un. ⚠ | 11 | 0% | -49% | 0.0 |

## Categoria

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| front ⚠ | 9 | 33% | -19% | 4.45 |
| shoulder | 33 | 12% | -55% | 1.62 |
| back | 107 | 10% | -55% | 1.37 |
| neck | 50 | 8% | -55% | 1.07 |
| hair | 30 | 7% | -55% | 0.89 |
| hat | 481 | 6% | -55% | 0.86 |
| face | 70 | 6% | -50% | 0.76 |
| waist ⚠ | 7 | 0% | -55% | 0.0 |

## Criador verificado

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 370 | 11% | -55% | 1.44 |
| sim | 417 | 5% | -51% | 0.61 |

## Favoritos por unidade

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| < 1 favorito/un. | 242 | 10% | -50% | 1.27 |
| 1 a 5 favoritos/un. | 172 | 8% | -55% | 1.09 |
| 5+ favoritos/un. | 373 | 6% | -55% | 0.79 |

## Preço da 1ª semana de revenda ÷ preço original (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 4x ou mais | 28 | 68% | +125% | 9.05 |
| 2,5x a 4x | 23 | 30% | -31% | 4.06 |
| 1,5x a 2,5x | 72 | 19% | -21% | 2.59 |
| < 1,5x o preço | 447 | 4% | -55% | 0.51 |

## Vendas na 1ª semana de revenda (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 100 a 499 vendas | 72 | 11% | -28% | 1.48 |
| 500+ vendas | 118 | 11% | -47% | 1.47 |
| < 20 vendas | 515 | 7% | -55% | 0.88 |
| 20 a 99 vendas | 82 | 5% | -51% | 0.65 |

## Estoque ≥ 1.000 e preço ≤ 250 (regra antiga do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| sim | 137 | 15% | -45% | 2.04 |
| não | 650 | 6% | -55% | 0.78 |

## Estoque acima de 10.000 (regra EVITAR do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 604 | 9% | -55% | 1.17 |
| sim | 183 | 3% | -42% | 0.44 |

## Curva depois de esgotar (preço mediano ÷ preço original)

Início = 1º dia em que o preço saiu de ±15% do preço de loja (≈ quando esgotou). Inclui itens ainda sem desfecho.

| Grupo | +1 dia | +7 dias | +30 dias |
|---|---|---|---|
| todos | 1.00x (n=366) | 1.23x (n=259) | 1.19x (n=301) |
| 101 a 250 | 1.00x (n=60) | 0.97x (n=51) | 0.99x (n=56) |
| 251 a 500 | 1.00x (n=40) | 1.22x (n=33) | 1.77x (n=39) |
| 51 a 100 | 2.16x (n=104) | 3.30x (n=86) | 1.73x (n=56) |
| acima de 500 | 0.99x (n=139) | 1.15x (n=82) | 1.34x (n=105) |
| até 50 | 0.00x (n=23) | 1.00x (n=7) | 1.09x (n=45) |
| 101 a 500 un. | 1.02x (n=16) | 1.00x (n=9) | 1.07x (n=12) |
| 2.001 a 10.000 un. | 2.00x (n=110) | 2.95x (n=95) | 1.63x (n=60) |
| 501 a 2.000 un. | 1.12x (n=10) | 1.35x (n=8) | 1.03x (n=7) |
| acima de 10.000 un. | 1.00x (n=156) | 1.09x (n=126) | 1.14x (n=182) |
| até 100 un. | 0.00x (n=74) | 1.00x (n=21) | 1.26x (n=40) |

## Melhores desfechos

| Item | Preço | Venda dia 30 | Margem |
|---|---|---|---|
| [Diamond W Chain](https://www.roblox.com/catalog/13062988718) | 100 | 29999 | +13413% |
| [Nuke Chain](https://www.roblox.com/catalog/13832615792) | 200 | 5000 | +1026% |
| [Pepper](https://www.roblox.com/catalog/13850956216) | 5000 | 100069 | +802% |
| [⌛ Stormbreaker Horns](https://www.roblox.com/catalog/121976686814942) | 95 | 1558 | +639% |
| [[⏳LIMITED Classic] White Sparkle Time Fedora](https://www.roblox.com/catalog/83446680555913) | 95 | 1476 | +600% |
| [Blue Valk](https://www.roblox.com/catalog/124270180080726) | 95 | 1461 | +593% |
| [Emperor Top Hat](https://www.roblox.com/catalog/13742588059) | 3333 | 50000 | +576% |
| [[ANIMATED] Twinkling Star Aura](https://www.roblox.com/catalog/75260672285911) | 55 | 753 | +517% |
| [QT Bandana](https://www.roblox.com/catalog/13609645958) | 100000 | 1333337 | +501% |
| [Rainbow Electric Face Mask](https://www.roblox.com/catalog/14010092071) | 35 | 455 | +486% |

## Esgotando agora (velocidade medida entre rodadas de hoje)

| Item | Preço | Restam | Vendas/h | Esgota em |
|---|---|---|---|---|
| [Birthday Cake Axolu](https://www.roblox.com/catalog/110467381278652) | 0 | 3 | 99.0 | ~0.0 h |
| [HUGE Hugging Halloween Cat on your Back](https://www.roblox.com/catalog/103418642515401) | 0 | 8 | 23.99 | ~0.3 h |
| [Betrayers Crown](https://www.roblox.com/catalog/121229291644581) | 0 | 10 | 15.0 | ~0.7 h |
| [Asta](https://www.roblox.com/catalog/111579290317799) | 0 | 3 | 3.0 | ~1.0 h |
| [Gráinneog](https://www.roblox.com/catalog/106355599246932) | 0 | 8 | 6.0 | ~1.3 h |
| [⏳ Sparkle Red Hair + Crown Valk + Clockworks](https://www.roblox.com/catalog/79846453984508) | 149 | 7 | 3.0 | ~2.3 h |
| [Diego](https://www.roblox.com/catalog/110126764663521) | 0 | 6 | 2.0 | ~3.0 h |
| [Fries Shoulder Pal](https://www.roblox.com/catalog/92059852230172) | 0 | 301 | 74.0 | ~4.1 h |
| [Flying Squirrel Hugger](https://www.roblox.com/catalog/107550244108021) | 0 | 10 | 2.0 | ~5.0 h |
| [The Shumpkin](https://www.roblox.com/catalog/86553542522636) | 0 | 24 | 4.0 | ~6.0 h |
| [Cute White Angel Wings](https://www.roblox.com/catalog/95651415246994) | 0 | 56 | 8.0 | ~7.0 h |
| [NIGHT DEMON 👹 | exclusive ](https://www.roblox.com/catalog/95006433998697) | 900 | 126 | 17.0 | ~7.4 h |
| [Keith_crowned’s sparkle time traffic birthday cake](https://www.roblox.com/catalog/90498366287453) | 0 | 40 | 5.0 | ~8.0 h |
| [Emilia](https://www.roblox.com/catalog/130782686627629) | 0 | 31 | 3.0 | ~10.3 h |
| [Black Hair w Goggles](https://www.roblox.com/catalog/105612037282720) | 0 | 80 | 7.0 | ~11.4 h |
| [[ANIMATED] Nyan Cat HP Bar ](https://www.roblox.com/catalog/118306309849671) | 95 | 185 | 15.0 | ~12.3 h |
| [Black Messy Hair](https://www.roblox.com/catalog/91863676683138) | 0 | 84 | 6.0 | ~14.0 h |
| [Armour Shoulder Left](https://www.roblox.com/catalog/100309523892085) | 0 | 31 | 2.0 | ~15.5 h |
| [Blue Dress](https://www.roblox.com/catalog/114508257602750) | 0 | 35 | 2.0 | ~17.5 h |
| [Christmas Aura with Snowflakes and Gingerbread](https://www.roblox.com/catalog/126938298102120) | 0 | 36 | 2.0 | ~18.0 h |
| [Blue Valkyrie](https://www.roblox.com/catalog/103264888144153) | 145 | 77 | 4.0 | ~19.2 h |
| [[⏳LIMITED] Traffic Cone+Clockwork+Hair+Antlers ](https://www.roblox.com/catalog/98276569007154) | 199 | 96 | 5.0 | ~19.2 h |
| [Retro Classic Roblox Aura](https://www.roblox.com/catalog/107664742122292) | 55 | 60 | 3.0 | ~20.0 h |
| [Red Valkyrie](https://www.roblox.com/catalog/70913805587976) | 95 | 70 | 3.0 | ~23.3 h |
| [Green Warlord Horns](https://www.roblox.com/catalog/73228227707947) | 0 | 148 | 5.0 | ~29.6 h |

> Passado não garante futuro. Lift só vale com amostra grande; um dia de coleta é ponto de partida.
