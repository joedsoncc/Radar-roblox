# Calibração do radar (2026-10-17T20:30:13Z)

Backtest: quem comprou no preço original e vendeu depois da trava de 30 dias (mediana do gráfico 30 a 37 dias depois de esgotar), com as taxas do radar (recebe 50%, custo ×1,11). Acerto = margem líquida ≥ 30%.

- Itens com histórico coletado: **1800**
- Com desfecho (37+ dias depois de esgotar, item pago): **769**
- Ainda sem desfecho: 78
- **Taxa geral de acerto: 8%** (59 de 769)

Faixas com menos de 20 itens aparecem com ⚠ (amostra pequena, não use para decidir).

## Preço original

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 51 a 100 | 66 | 30% | -53% | 3.95 |
| até 50 | 46 | 9% | -37% | 1.13 |
| acima de 500 | 508 | 6% | -55% | 0.72 |
| 101 a 250 | 81 | 5% | -55% | 0.64 |
| 251 a 500 | 68 | 4% | -34% | 0.58 |

## Estoque total

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 2.001 a 10.000 un. | 55 | 31% | -36% | 4.03 |
| até 100 un. | 429 | 7% | -55% | 0.91 |
| 101 a 500 un. | 92 | 6% | -55% | 0.85 |
| acima de 10.000 un. | 182 | 3% | -41% | 0.43 |
| 501 a 2.000 un. ⚠ | 11 | 0% | -49% | 0.0 |

## Categoria

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| front ⚠ | 9 | 33% | -19% | 4.34 |
| shoulder | 32 | 12% | -53% | 1.63 |
| back | 105 | 10% | -55% | 1.37 |
| neck | 48 | 8% | -55% | 1.09 |
| hair | 29 | 7% | -55% | 0.9 |
| hat | 471 | 7% | -55% | 0.86 |
| face | 68 | 6% | -49% | 0.77 |
| waist ⚠ | 7 | 0% | -55% | 0.0 |

## Criador verificado

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 354 | 11% | -55% | 1.47 |
| sim | 415 | 5% | -51% | 0.6 |

## Favoritos por unidade

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| < 1 favorito/un. | 236 | 10% | -49% | 1.27 |
| 1 a 5 favoritos/un. | 167 | 8% | -55% | 1.09 |
| 5+ favoritos/un. | 366 | 6% | -55% | 0.78 |

## Preço da 1ª semana de revenda ÷ preço original (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 4x ou mais | 28 | 68% | +125% | 8.84 |
| 2,5x a 4x | 22 | 32% | -25% | 4.15 |
| 1,5x a 2,5x | 72 | 19% | -21% | 2.53 |
| < 1,5x o preço | 436 | 4% | -55% | 0.51 |

## Vendas na 1ª semana de revenda (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 100 a 499 vendas | 72 | 11% | -28% | 1.45 |
| 500+ vendas | 117 | 11% | -46% | 1.45 |
| < 20 vendas | 499 | 7% | -55% | 0.89 |
| 20 a 99 vendas | 81 | 5% | -51% | 0.64 |

## Estoque ≥ 1.000 e preço ≤ 250 (regra antiga do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| sim | 136 | 15% | -45% | 2.01 |
| não | 633 | 6% | -55% | 0.78 |

## Estoque acima de 10.000 (regra EVITAR do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 587 | 9% | -55% | 1.18 |
| sim | 182 | 3% | -41% | 0.43 |

## Curva depois de esgotar (preço mediano ÷ preço original)

Início = 1º dia em que o preço saiu de ±15% do preço de loja (≈ quando esgotou). Inclui itens ainda sem desfecho.

| Grupo | +1 dia | +7 dias | +30 dias |
|---|---|---|---|
| todos | 1.00x (n=359) | 1.21x (n=256) | 1.19x (n=300) |
| 101 a 250 | 1.00x (n=58) | 0.95x (n=50) | 0.99x (n=55) |
| 251 a 500 | 1.00x (n=40) | 1.22x (n=33) | 1.77x (n=39) |
| 51 a 100 | 2.23x (n=100) | 3.44x (n=84) | 1.73x (n=56) |
| acima de 500 | 0.99x (n=138) | 1.15x (n=82) | 1.34x (n=105) |
| até 50 | 0.00x (n=23) | 1.00x (n=7) | 1.09x (n=45) |
| 101 a 500 un. | 1.02x (n=16) | 1.00x (n=9) | 1.07x (n=12) |
| 2.001 a 10.000 un. | 2.00x (n=107) | 2.94x (n=92) | 1.63x (n=60) |
| 501 a 2.000 un. | 1.12x (n=10) | 1.35x (n=8) | 1.03x (n=7) |
| acima de 10.000 un. | 1.00x (n=155) | 1.09x (n=126) | 1.14x (n=181) |
| até 100 un. | 0.00x (n=71) | 1.00x (n=21) | 1.26x (n=40) |

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
| [Birthday Cake Axolu](https://www.roblox.com/catalog/110467381278652) | 0 | 3 | 118.8 | ~0.0 h |
| [Asta](https://www.roblox.com/catalog/111579290317799) | 0 | 3 | 3.6 | ~0.8 h |
| [Betrayers Crown](https://www.roblox.com/catalog/121229291644581) | 0 | 13 | 14.4 | ~0.9 h |
| [Gráinneog](https://www.roblox.com/catalog/106355599246932) | 0 | 9 | 6.0 | ~1.5 h |
| [Diego](https://www.roblox.com/catalog/110126764663521) | 0 | 6 | 2.4 | ~2.5 h |
| [⏳ Sparkle Red Hair + Crown Valk + Clockworks](https://www.roblox.com/catalog/79846453984508) | 149 | 8 | 2.4 | ~3.3 h |
| [Flying Squirrel Hugger](https://www.roblox.com/catalog/107550244108021) | 0 | 10 | 2.4 | ~4.2 h |
| [Fries Shoulder Pal](https://www.roblox.com/catalog/92059852230172) | 0 | 317 | 69.6 | ~4.6 h |
| [The Shumpkin](https://www.roblox.com/catalog/86553542522636) | 0 | 24 | 4.8 | ~5.0 h |
| [Cute White Angel Wings](https://www.roblox.com/catalog/95651415246994) | 0 | 56 | 9.6 | ~5.8 h |
| [NIGHT DEMON 👹 | exclusive ](https://www.roblox.com/catalog/95006433998697) | 900 | 127 | 19.2 | ~6.6 h |
| [Keith_crowned’s sparkle time traffic birthday cake](https://www.roblox.com/catalog/90498366287453) | 0 | 40 | 6.0 | ~6.7 h |
| [Emilia](https://www.roblox.com/catalog/130782686627629) | 0 | 31 | 3.6 | ~8.6 h |
| [[ANIMATED] Nyan Cat HP Bar ](https://www.roblox.com/catalog/118306309849671) | 95 | 186 | 16.8 | ~11.1 h |
| [Armour Shoulder Left](https://www.roblox.com/catalog/100309523892085) | 0 | 31 | 2.4 | ~12.9 h |
| [Black Messy Hair](https://www.roblox.com/catalog/91863676683138) | 0 | 85 | 6.0 | ~14.2 h |
| [Blue Dress](https://www.roblox.com/catalog/114508257602750) | 0 | 35 | 2.4 | ~14.6 h |
| [Christmas Aura with Snowflakes and Gingerbread](https://www.roblox.com/catalog/126938298102120) | 0 | 36 | 2.4 | ~15.0 h |
| [Retro Classic Roblox Aura](https://www.roblox.com/catalog/107664742122292) | 55 | 60 | 3.6 | ~16.7 h |
| [[⏳LIMITED] Traffic Cone+Clockwork+Hair+Antlers ](https://www.roblox.com/catalog/98276569007154) | 199 | 97 | 4.8 | ~20.2 h |
| [Green Warlord Horns](https://www.roblox.com/catalog/73228227707947) | 0 | 148 | 6.0 | ~24.7 h |
| [Wings of Awakening](https://www.roblox.com/catalog/134635829576460) | 0 | 60 | 2.4 | ~25.0 h |
| [[⏳LiMITED SPARKLE] Black Valk + Fedora + Clockwork](https://www.roblox.com/catalog/98429339305128) | 199 | 490 | 16.8 | ~29.2 h |
| [Golden Club](https://www.roblox.com/catalog/94511447066622) | 0 | 71 | 2.4 | ~29.6 h |
| [Red Valkyrie](https://www.roblox.com/catalog/70913805587976) | 95 | 71 | 2.4 | ~29.6 h |

> Passado não garante futuro. Lift só vale com amostra grande; um dia de coleta é ponto de partida.
