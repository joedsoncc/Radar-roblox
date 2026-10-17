# Calibração do radar (2026-10-17T20:20:13Z)

Backtest: quem comprou no preço original e vendeu depois da trava de 30 dias (mediana do gráfico 30 a 37 dias depois de esgotar), com as taxas do radar (recebe 50%, custo ×1,11). Acerto = margem líquida ≥ 30%.

- Itens com histórico coletado: **1500**
- Com desfecho (37+ dias depois de esgotar, item pago): **636**
- Ainda sem desfecho: 78
- **Taxa geral de acerto: 8%** (52 de 636)

Faixas com menos de 20 itens aparecem com ⚠ (amostra pequena, não use para decidir).

## Preço original

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 51 a 100 | 60 | 32% | -50% | 3.87 |
| até 50 | 46 | 9% | -37% | 1.06 |
| acima de 500 | 398 | 6% | -55% | 0.71 |
| 101 a 250 | 74 | 5% | -55% | 0.66 |
| 251 a 500 | 58 | 3% | -30% | 0.42 |

## Estoque total

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 2.001 a 10.000 un. | 54 | 32% | -33% | 3.85 |
| até 100 un. | 336 | 8% | -55% | 0.98 |
| 101 a 500 un. | 58 | 5% | -54% | 0.63 |
| acima de 10.000 un. | 177 | 3% | -40% | 0.35 |
| 501 a 2.000 un. ⚠ | 11 | 0% | -49% | 0.0 |

## Categoria

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| front ⚠ | 5 | 60% | +32% | 7.34 |
| shoulder | 29 | 14% | -50% | 1.69 |
| back | 88 | 11% | -55% | 1.39 |
| neck | 39 | 10% | -55% | 1.25 |
| face | 55 | 7% | -47% | 0.89 |
| hat | 394 | 7% | -55% | 0.81 |
| hair | 22 | 4% | -55% | 0.56 |
| waist ⚠ | 4 | 0% | -55% | 0.0 |

## Criador verificado

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 279 | 13% | -55% | 1.62 |
| sim | 357 | 4% | -49% | 0.51 |

## Favoritos por unidade

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| < 1 favorito/un. | 224 | 10% | -46% | 1.2 |
| 1 a 5 favoritos/un. | 122 | 9% | -53% | 1.1 |
| 5+ favoritos/un. | 290 | 7% | -55% | 0.8 |

## Preço da 1ª semana de revenda ÷ preço original (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 4x ou mais | 20 | 75% | +144% | 9.17 |
| 2,5x a 4x ⚠ | 19 | 37% | -10% | 4.51 |
| 1,5x a 2,5x | 53 | 23% | -18% | 2.77 |
| < 1,5x o preço | 364 | 4% | -55% | 0.54 |

## Vendas na 1ª semana de revenda (sinal pós-esgotar)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| 100 a 499 vendas | 67 | 12% | -26% | 1.46 |
| 500+ vendas | 115 | 10% | -46% | 1.28 |
| < 20 vendas | 389 | 7% | -55% | 0.88 |
| 20 a 99 vendas | 65 | 6% | -48% | 0.75 |

## Estoque ≥ 1.000 e preço ≤ 250 (regra antiga do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| sim | 133 | 16% | -45% | 1.93 |
| não | 503 | 6% | -55% | 0.75 |

## Estoque acima de 10.000 (regra EVITAR do PR #4)

| Faixa | Itens | Acerto | Margem mediana | Lift |
|---|---|---|---|---|
| não | 459 | 10% | -55% | 1.25 |
| sim | 177 | 3% | -40% | 0.35 |

## Curva depois de esgotar (preço mediano ÷ preço original)

Início = 1º dia em que o preço saiu de ±15% do preço de loja (≈ quando esgotou). Inclui itens ainda sem desfecho.

| Grupo | +1 dia | +7 dias | +30 dias |
|---|---|---|---|
| todos | 1.00x (n=332) | 1.23x (n=245) | 1.20x (n=279) |
| 101 a 250 | 1.00x (n=54) | 0.97x (n=47) | 0.99x (n=50) |
| 251 a 500 | 1.00x (n=37) | 1.22x (n=31) | 1.77x (n=36) |
| 51 a 100 | 2.17x (n=97) | 3.47x (n=82) | 1.73x (n=54) |
| acima de 500 | 0.99x (n=121) | 1.16x (n=78) | 1.37x (n=94) |
| até 50 | 0.00x (n=23) | 1.00x (n=7) | 1.09x (n=45) |
| 101 a 500 un. | 1.04x (n=7) | 1.03x (n=6) | 1.09x (n=9) |
| 2.001 a 10.000 un. | 2.00x (n=106) | 2.95x (n=91) | 1.65x (n=59) |
| 501 a 2.000 un. | 1.12x (n=10) | 1.35x (n=8) | 1.03x (n=7) |
| acima de 10.000 un. | 1.00x (n=150) | 1.09x (n=122) | 1.15x (n=176) |
| até 100 un. | 0.00x (n=59) | 1.40x (n=18) | 1.26x (n=28) |

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
| [Birthday Cake Axolu](https://www.roblox.com/catalog/110467381278652) | 0 | 3 | 148.56 | ~0.0 h |
| [Asta](https://www.roblox.com/catalog/111579290317799) | 0 | 3 | 4.5 | ~0.7 h |
| [Betrayers Crown](https://www.roblox.com/catalog/121229291644581) | 0 | 16 | 13.51 | ~1.2 h |
| [Gráinneog](https://www.roblox.com/catalog/106355599246932) | 0 | 9 | 7.5 | ~1.2 h |
| [Diego](https://www.roblox.com/catalog/110126764663521) | 0 | 6 | 3.0 | ~2.0 h |
| [Flying Squirrel Hugger](https://www.roblox.com/catalog/107550244108021) | 0 | 10 | 3.0 | ~3.3 h |
| [The Shumpkin](https://www.roblox.com/catalog/86553542522636) | 0 | 24 | 6.0 | ~4.0 h |
| [Fries Shoulder Pal](https://www.roblox.com/catalog/92059852230172) | 0 | 326 | 73.53 | ~4.4 h |
| [Keith_crowned’s sparkle time traffic birthday cake](https://www.roblox.com/catalog/90498366287453) | 0 | 40 | 7.5 | ~5.3 h |
| [Cute White Angel Wings](https://www.roblox.com/catalog/95651415246994) | 0 | 58 | 9.0 | ~6.4 h |
| [NIGHT DEMON 👹 | exclusive ](https://www.roblox.com/catalog/95006433998697) | 900 | 130 | 19.51 | ~6.7 h |
| [Emilia](https://www.roblox.com/catalog/130782686627629) | 0 | 31 | 4.5 | ~6.9 h |
| [[ANIMATED] Nyan Cat HP Bar ](https://www.roblox.com/catalog/118306309849671) | 95 | 187 | 19.51 | ~9.6 h |
| [Armour Shoulder Left](https://www.roblox.com/catalog/100309523892085) | 0 | 31 | 3.0 | ~10.3 h |
| [Blue Dress](https://www.roblox.com/catalog/114508257602750) | 0 | 35 | 3.0 | ~11.7 h |
| [Christmas Aura with Snowflakes and Gingerbread](https://www.roblox.com/catalog/126938298102120) | 0 | 36 | 3.0 | ~12.0 h |
| [Black Messy Hair](https://www.roblox.com/catalog/91863676683138) | 0 | 87 | 4.5 | ~19.3 h |
| [Wings of Awakening](https://www.roblox.com/catalog/134635829576460) | 0 | 60 | 3.0 | ~20.0 h |
| [Retro Classic Roblox Aura](https://www.roblox.com/catalog/107664742122292) | 55 | 61 | 3.0 | ~20.3 h |
| [[⏳LIMITED] Traffic Cone+Clockwork+Hair+Antlers ](https://www.roblox.com/catalog/98276569007154) | 199 | 98 | 4.5 | ~21.8 h |
| [[⏳LiMITED SPARKLE] Black Valk + Fedora + Clockwork](https://www.roblox.com/catalog/98429339305128) | 199 | 490 | 21.01 | ~23.3 h |
| [Red Valkyrie](https://www.roblox.com/catalog/70913805587976) | 95 | 71 | 3.0 | ~23.7 h |
| [Green Warlord Horns](https://www.roblox.com/catalog/73228227707947) | 0 | 149 | 6.0 | ~24.8 h |
| [Crimson Dominus](https://www.roblox.com/catalog/117646930298113) | 95 | 159 | 6.0 | ~26.5 h |
| [Pink Sigil Star Crown](https://www.roblox.com/catalog/120803233063988) | 95 | 321 | 9.0 | ~35.7 h |

> Passado não garante futuro. Lift só vale com amostra grande; um dia de coleta é ponto de partida.
