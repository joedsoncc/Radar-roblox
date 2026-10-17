# Radar de UGC Limiteds (Roblox)

Monitora UGC Limiteds de **acessórios** quase esgotando (menos de 100 unidades, preço até 500 Robux), calcula o lucro líquido, classifica em **COMPRAR-AGORA / OBSERVAR / EVITAR**, publica um site instalável no celular e avisa pelo **ntfy** quando aparece uma oportunidade forte.

> Só análise. O radar nunca compra, vende, anuncia ou usa senha/cookie. Não é recomendação financeira.

## Como funciona

A cada 2 h o GitHub Actions roda `python radar.py run`:

1. **Coleta** no catálogo público do Roblox (acessórios collectible) e no histórico de revenda (`resale-data`).
2. **Histórico**: grava um snapshot por item em `data/snapshots/AAAA-MM-DD.jsonl`.
3. **Análise**: lucro líquido, liquidez, coerência RAP × gráfico, velocidade de venda entre snapshots e criador verificado.
4. **Site**: escreve `docs/data.json` (lido pelo PWA) e `data/lista-de-compra.md`.
5. **Commit** do histórico, do site e do estado dos alertas.
6. **Notificação** no ntfy, só depois do commit salvo (assim um commit perdido não gera alerta repetido).

### As contas

```
custo efetivo  = preço × 1,11      (1,11 é margem de segurança; a Roblox não cobra taxa na compra)
você recebe    = RAP × 0,5         (10% criador, 10% afiliado, 30% Roblox)
lucro líquido  = RAP × 0,5 − preço × 1,11
```
Exemplo: preço 100, RAP 260 → recebe 130, custo 111, lucro **+19 (+17%)**. Com RAP 200 → recebe 100, **prejuízo de 11**.

### Classes (mude os números em `config.json`)

| Classe | Quando |
|---|---|
| COMPRAR-AGORA | margem ≥ 30%, volume 7d ≥ 50, RAP coerente com o gráfico, velocidade medida e esgota em até 72 h |
| EVITAR | RAP incoerente (último preço do gráfico < 50% do RAP ou gráfico com mais de 14 dias), volume 7d < 5, ou margem ≤ 0 |
| OBSERVAR | o resto (inclui itens sem RAP e itens com prejuízo hoje mas esgotando em menos de 24 h) |

**Alerta no celular** (bem mais exigente): COMPRAR-AGORA **e** margem ≥ 50%, volume 7d ≥ 100, menos de 100 un., RAP coerente e velocidade medida (2+ snapshots). Uma vez por item; novo alerta só se a classe melhorar. Máximo de 3 por dia. Se a API pedir login ou o workflow falhar, chega um aviso de sistema (no máximo 1 por dia por tipo).

Velocidade de venda só conta com snapshots separados por pelo menos 1,5 h e 2+ unidades vendidas; se o estoque aumentar (reposição), a velocidade não é medida. O RAP só é considerado coerente se o último preço do gráfico **e** a mediana de 14 dias forem pelo menos metade do RAP, com 3+ dias de venda.

## Lançamentos da Roblox (a cada 10 min)

Um segundo workflow (`.github/workflows/lancamentos.yml`) procura **limiteds de acessórios publicados pela conta oficial da Roblox**, de qualquer preço. Quando aparece um item novo, ele salva no repositório e manda um alerta urgente no ntfy com nome, preço, estoque e link. O item também aparece no topo do site, na seção "Lançamentos da Roblox".

- Na primeira execução, ele só registra o que já existe, sem avisar.
- Itens criados há mais de 7 dias que reaparecem na lista são ignorados. Se a data de criação não puder ser confirmada, o alerta avisa isso.
- Só gera commit quando acha algo novo. O GitHub pode atrasar o agendamento alguns minutos, e lançamentos costumam esgotar rápido.

## O que você precisa fazer (uma vez)

1. **Repositório**: crie um repositório **público** vazio no GitHub. GitHub Pages em repositório privado exige plano pago; no grátis o site fica público (os segredos não).
2. **Pages**: no repositório, *Settings → Pages → Build and deployment → Source: Deploy from a branch*, branch `main`, pasta `/docs`. O site fica em `https://SEU-USUARIO.github.io/NOME-DO-REPO/`.
3. **Actions com escrita**: *Settings → Actions → General → Workflow permissions → Read and write permissions* (o workflow precisa salvar o histórico).
4. **App ntfy**: instale o **ntfy** no celular (Play Store / App Store). Toque em **+** e assine um tópico com nome longo e aleatório, por exemplo `radar-ugc-k7Qp2vX9mLr4TzW8`. Quem souber o nome consegue ler, então não use nada óbvio.
5. **Segredo `NTFY_TOPIC`**: *Settings → Secrets and variables → Actions → New repository secret*. Nome `NTFY_TOPIC`, valor = só o nome do tópico (sem `https://ntfy.sh/`). Nunca coloque o tópico no código.
6. **Primeira execução**: aba *Actions → Radar UGC → Run workflow*. Depois roda sozinho a cada 2 h.
7. **Instalar o site como app**: abra o site no celular. Android/Chrome: menu ⋮ → *Instalar app*. iPhone/Safari: Compartilhar → *Adicionar à Tela de Início*. O app serve para consulta; **o alerta vem do ntfy** (o site instalado não avisa com o app fechado).

## Avisos importantes

- **Nenhum alerta garante lucro.** Esgotar é o melhor sinal de RAP alto, mas no histórico só ~11% dos esgotados dão margem ≥ 30% de forma consistente.
- **Revender exige Roblox Plus (ou Premium antigo)** e que o criador tenha habilitado a revenda. Há **trava de até 30 dias** depois da compra antes de poder revender (a documentação atual fala só em "até 30 dias"; o "7 dias na revenda" não foi confirmado). Limite de 3 cópias por pessoa por item.
- **RAP precisa de semanas de snapshots** para ser calibrado. Sinal de um dia não é tendência.
- **API de histórico pode exigir login.** Se responder 401/403, o site mostra um aviso, o RAP fica vazio e nenhuma compra é sugerida. O radar não contorna isso e não pede cookie.
- **Agendamento do GitHub** pode atrasar alguns minutos e é pausado após 60 dias sem atividade no repositório (o GitHub manda e-mail antes; basta reativar na aba Actions).

## Arquivos

| Caminho | O que é |
|---|---|
| `radar.py` | ponto de entrada (`run`, `--no-notify`, `--fake --root PASTA`) |
| `radar/` | coleta (`collect.py`), análise (`analyze.py`), alertas (`notify.py`), site (`site.py`), histórico (`storage.py`) |
| `config.json` | limites, categorias, pesos do score e gatilho do alerta |
| `.github/workflows/radar.yml` | agendamento a cada 2 h |
| `docs/` | site + PWA (`index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, `data.json`) |
| `data/` | snapshots, `latest.json`, `state.json` (alertas enviados) e `lista-de-compra.md` |
| `PESQUISA.md` | regras do mercado conferidas com fontes |
| `tests/` | testes com dados falsos: `python -m unittest discover -s tests` |

Testar sem internet: `python radar.py run --fake --root /tmp/teste` e abra `/tmp/teste/docs/data.json`.
