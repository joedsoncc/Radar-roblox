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
valor de venda = menor entre RAP e média dos 10 anúncios mais baratos (sem anúncio: RAP)
custo efetivo  = preço × 1,11      (1,11 é margem de segurança; a Roblox não cobra taxa na compra)
você recebe    = valor de venda × 0,5   (10% criador, 10% afiliado, 30% Roblox)
lucro líquido  = valor de venda × 0,5 − preço × 1,11
```
Exemplo: preço 100, RAP 260, média dos anúncios 300 → vale 260, recebe 130, custo 111, lucro **+19 (+17%)**. Se os 10 anúncios mais baratos forem de 100, 105, 110 … até 150 (média ≈ 118) → vale 118, recebe 59, **prejuízo de 52**.

A média usa os 10 anúncios mais baratos para que um único anúncio barato não distorça a conta. Com menos de 10 anúncios, usa a média dos que existem e mostra "média de N" (o número muda em `coleta.anuncios_media` no `config.json`). Se a lista de anúncios pedir login, o radar usa o menor anúncio do catálogo ("média de 1") e avisa na nota da coleta. O card, a lista de compra, o score, o alerta do ntfy e o "valor hoje" da carteira usam esse valor de venda.

### Classes (mude os números em `config.json`)

| Classe | Quando |
|---|---|
| COMPRAR-AGORA | margem ≥ 30%, volume 7d ≥ 50, RAP coerente com o gráfico, velocidade medida e esgota em até 72 h |
| EVITAR | estoque total ≥ 1.000 com preço ≤ 250, RAP incoerente (último preço do gráfico < 50% do RAP ou gráfico com mais de 14 dias), volume 7d < 5, ou margem ≤ 0 |
| OBSERVAR | o resto (inclui itens sem RAP, itens com prejuízo hoje mas esgotando em menos de 24 h, e itens com nome de clássico como Valkyrie/Dominus) |

**Ainda à venda (RAP ≈ preço):** enquanto a loja vende, as vendas dela formam o RAP, então RAP ≈ preço de loja e isso não diz nada sobre a revenda. Nesses itens o lucro é projetado como preço × retenção mediana dos limiteds **já esgotados** da mesma loja (3+ itens; 5+ para alerta). Sem esse histórico, o item fica em OBSERVAR sem lucro estimado. Exemplo: preço 200, loja com retenção 4,0 → venda estimada 800, recebe 400, custo 222, lucro +178 (+80%).

**Alerta no celular** (bem mais exigente): COMPRAR-AGORA **e** margem ≥ 50%, volume 7d ≥ 100, menos de 100 un., RAP coerente e velocidade medida (2+ snapshots). Uma vez por item; novo alerta só se a classe melhorar. Máximo de 3 por dia. Se a API pedir login ou o workflow falhar, chega um aviso de sistema (no máximo 1 por dia por tipo).

Velocidade de venda só conta com snapshots separados por pelo menos 1,5 h e 2+ unidades vendidas; se o estoque aumentar (reposição), a velocidade não é medida. O RAP só é considerado coerente se o último preço do gráfico **e** a mediana de 14 dias forem pelo menos metade do RAP, com 3+ dias de venda.

## Lançamentos da Roblox (a cada 10 min)

Um segundo workflow (`.github/workflows/lancamentos.yml`) procura **limiteds de acessórios publicados pela conta oficial da Roblox**, de qualquer preço. Quando aparece um item novo, ele salva no repositório e manda um alerta urgente no ntfy com nome, preço, estoque e link. O item também aparece no topo do site, na seção "Lançamentos da Roblox".

- Na primeira execução, ele só registra o que já existe, sem avisar.
- Itens criados há mais de 7 dias que reaparecem na lista são ignorados. Se a data de criação não puder ser confirmada, o alerta avisa isso.
- Só gera commit quando acha algo novo. O GitHub pode atrasar o agendamento alguns minutos, e lançamentos costumam esgotar rápido.

## Carteira: cadastrar e acompanhar

A carteira (`carteira.json`) guarda os itens que você comprou ou quer só acompanhar. A cada execução do radar (e a cada cadastro) o programa lê o RAP e o gráfico de revenda de cada item, grava uma linha em `data/carteira/<asset_id>.jsonl` e escreve `docs/carteira.json` (contrato em `docs/CONTRATO-CARTEIRA.md`).

- **Cadastrar pelo celular**: no repositório, *Issues → New issue → Carteira*. Escolha *Adicionar* ou *Remover*, cole o link do catálogo (ou o ID), o preço pago, a quantidade e a data (vazios = só acompanhar / 1 / hoje). Em poucos minutos o workflow `carteira.yml` atualiza `carteira.json`, comenta o resultado na issue e a fecha. Só issues do dono do repositório e com título `[carteira] ...` são processadas; o texto da issue nunca é executado, só lido e validado (preço inteiro ≥ 0, quantidade 1 a 100, data AAAA-MM-DD). *Remover* tira todos os lotes daquele item. Se algo for inválido, nada muda e o comentário explica o motivo.
- **Editar à mão**: `{"itens": [{"asset_id": 123, "preco_pago": 195, "quantidade": 1, "comprado_em": "2026-10-17", "nota": ""}]}`. `preco_pago: null` = só acompanhar (fica fora dos totais). O mesmo `asset_id` repetido vira lotes separados.
- **Contas**: valor atual = RAP × 0,5 × quantidade; lucro = valor atual − o que você pagou (sem a margem de 1,11); empate = pago ÷ 0,5. Se a API de revenda pedir login, esses campos ficam vazios e `status_note` explica; nada é estimado.
- Só a carteira, sem rodar o radar: `python radar.py carteira` (aceita `--fake --root PASTA`).

## Histórico das lojas

Para cada criador dos itens do radar, o programa olha os outros limiteds dele no catálogo e guarda em `data/criadores.json` (renovado a cada 7 dias, no máximo 15 criadores novos por execução, configurável em `lojas` no `config.json`): quantos itens, quantos esgotaram, e a **retenção** (menor revenda ÷ preço original, mediana) e a fração que revende acima do preço. Cada item do radar ganha `creator_track`, `retention` (RAP ÷ preço), `change_7d`, `trend` e `spark` (mini-gráfico). O score tem um peso `historico_loja` (10 pontos; sem dado vale neutro) e o motivo do item cita lojas com histórico forte ou fraco. É um indício, não garantia: criador bom pode lançar item ruim.

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
| `radar.py` | ponto de entrada (`run`, `carteira`, `cadastrar`, `--no-notify`, `--fake --root PASTA`) |
| `radar/` | coleta (`collect.py`), análise (`analyze.py`), alertas (`notify.py`), site (`site.py`), histórico (`storage.py`), carteira (`carteira.py`, `cadastro.py`), lojas (`lojas.py`) |
| `carteira.json` | itens da carteira (editado à mão ou pela issue de cadastro) |
| `.github/ISSUE_TEMPLATE/carteira.yml`, `.github/workflows/carteira.yml` | formulário e workflow de cadastro por issue |
| `config.json` | limites, categorias, pesos do score e gatilho do alerta |
| `.github/workflows/radar.yml` | agendamento a cada 2 h |
| `docs/` | site + PWA (`index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, `data.json`, `carteira.json`) |
| `data/` | snapshots, `latest.json`, `state.json` (alertas enviados), `lista-de-compra.md`, `carteira/` (histórico por item) e `criadores.json` (histórico das lojas) |
| `PESQUISA.md` | regras do mercado conferidas com fontes |
| `tests/` | testes com dados falsos: `python -m unittest discover -s tests` |

Testar sem internet: `python radar.py run --fake --root /tmp/teste` e abra `/tmp/teste/docs/data.json`.
