(function () {
  'use strict';
  var NA = '—';
  var CUR = '⏣';
  var FALLBACK_REPO = 'joedsoncc/Radar-roblox';
  var state = { data: null, cart: undefined, cartKey: null, cat: 'all', cls: '', sort: 'score', view: 'radar' };
  var $ = function (id) { return document.getElementById(id); };

  var nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function num(v) { return isNum(v) ? nf.format(v) : NA; }
  function robux(v) { return isNum(v) ? nf.format(v) + ' ' + CUR : NA; }
  function pct(v) { return isNum(v) ? nf.format(v) + '%' : NA; }
  function margin(v) { return isNum(v) ? nf.format(Math.round(v * 1000) / 10) + '%' : NA; }
  function eta(h) {
    if (!isNum(h) || h < 0) return NA;
    if (h < 1) return '~' + Math.max(1, Math.round(h * 60)) + ' min';
    if (h < 48) return '~' + Math.round(h) + ' h';
    return '~' + Math.round(h / 24) + ' d';
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function signed(v, f) { return isNum(v) ? (v > 0 ? '+' : '') + f(v) : NA; }
  function sgnClass(v) { return isNum(v) ? (v > 0 ? 'pos' : v < 0 ? 'neg' : '') : ''; }
  function sgnPct(v) { return signed(v, margin); }
  function trendInfo(t, c7) {
    var m = { 'subindo': ['▲', 'up', 'Subindo'], 'caindo': ['▼', 'down', 'Caindo'], 'estável': ['▬', 'flat', 'Estável'] }[t];
    if (!m) return { arrow: '', cls: 'flat', text: NA };
    return { arrow: m[0], cls: m[1], text: m[0] + ' ' + m[2] + (isNum(c7) ? ' (' + sgnPct(c7) + ')' : '') };
  }
  function safeUrl(u) { return typeof u === 'string' && /^https?:\/\//i.test(u) ? u : null; }

  /* Cadastro via issue do GitHub */
  function repoSlug() {
    var m = /^([a-z0-9-]+)\.github\.io$/i.exec(location.hostname || '');
    if (m) {
      var seg = (location.pathname || '/').split('/')[1];
      if (seg) return m[1] + '/' + seg;
    }
    return FALLBACK_REPO;
  }
  /* Issue em texto livre (sem formulário): o app do GitHub ignora formulários e campos pré-preenchidos,
     então o ID vai também no título e o robô lê o que vier (radar/cadastro.py, parse_free). */
  function issueUrl(o) {
    var acao = o.acao || 'Adicionar';
    var id = (/(?:catalog|library)\/(\d+)/.exec(o.item || '') || [])[1] || o.item;
    var nome = o.nome && String(o.nome) !== String(id) ? o.nome + ' · ' : '';
    var linhas = [acao, 'Item: ' + o.item];
    if (acao === 'Adicionar') {
      if (o.preco != null) linhas.push('Preço pago: ' + o.preco);
      linhas.push('Quantidade: ' + (o.qtd || 1));
      if (o.data) linhas.push('Comprado em: ' + o.data);
    }
    var q = [['title', '[carteira] ' + (acao === 'Remover' ? 'Remover ' : '') + nome + id], ['body', linhas.join('\n')]];
    return 'https://github.com/' + repoSlug() + '/issues/new?' + q.map(function (p) {
      return encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1]);
    }).join('&');
  }
  function catalogUrl(i) { return safeUrl(i.url) || (i.asset_id != null ? 'https://www.roblox.com/catalog/' + i.asset_id : ''); }
  function linkBtn(label, href, cls) {
    var a = el('a', 'btn ' + (cls || ''), label);
    a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
    return a;
  }

  /* Tema */
  function getSaved() { try { return localStorage.getItem('radar-theme'); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem('radar-theme', v); } catch (e) {} }
  function systemDark() { return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches; }
  function applyTheme(t) {
    var root = document.documentElement;
    if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
  }
  function currentTheme() { return document.documentElement.getAttribute('data-theme') || (systemDark() ? 'dark' : 'light'); }
  function initTheme() {
    var s = getSaved();
    if (s === 'light' || s === 'dark') applyTheme(s);
    $('theme-btn').addEventListener('click', function () {
      var n = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(n); save(n);
    });
  }

  /* Dados */
  // Clique em "Atualizar": ?t=agora fura o cache do GitHub Pages (até 10 min) e do navegador.
  var bust = '';
  function src(name) { return name + bust; }
  function ago(ms) {
    var m = Math.round(ms / 60000);
    if (!isFinite(m) || m < 0) return '';
    if (m < 1) return 'agora há pouco';
    if (m < 60) return 'há ' + m + ' min';
    var h = Math.floor(m / 60), r = m % 60;
    return 'há ' + h + ' h' + (r ? ' ' + r + ' min' : '');
  }
  function load() {
    return fetch(src('data.json'), { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function renderHeader(d) {
    var t = NA;
    if (d.generated_at) {
      var dt = new Date(d.generated_at);
      if (!isNaN(dt)) t = dt.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) + ' (' + ago(Date.now() - dt.getTime()) + ')';
    }
    $('updated').textContent = 'Última atualização: ' + t;
    var b = $('banner');
    var ageH = d.generated_at ? (Date.now() - new Date(d.generated_at).getTime()) / 36e5 : NaN;
    var msgs = [];
    if (d.run_status && d.run_status !== 'ok') {
      msgs.push('Atenção (' + d.run_status + '): ' + (d.status_note || 'A última execução não foi totalmente bem-sucedida.'));
    }
    if (!isNaN(ageH) && ageH > 5) {
      msgs.push('Dados com ' + Math.round(ageH) + ' h: o radar pode estar parado. Veja a aba Actions do repositório.');
    }
    if (msgs.length) { b.textContent = msgs.join(' '); b.hidden = false; } else { b.hidden = true; }
    if (d.disclaimer) $('disclaimer').textContent = d.disclaimer;
  }

  /* Corte de lucro do config.json (lucro líquido acima de 100% do valor gasto); vale também para dados antigos em cache. */
  function shownItems() {
    var cfg = state.data.config || {};
    var cut = isNum(cfg.min_net_margin) ? cfg.min_net_margin : 1;
    return (state.data.items || []).filter(function (i) {
      return isNum(i.net_margin) && i.net_margin > cut && i['class'] !== 'EVITAR';
    });
  }

  function renderTabs() {
    var d = state.data, items = shownItems();
    var tabs = $('tabs');
    tabs.textContent = '';
    var cats = [{ key: 'all', label: 'Todas' }].concat(d.categories || []);
    cats.forEach(function (c) {
      var n = c.key === 'all' ? items.length : items.filter(function (i) { return i.category === c.key; }).length;
      var b = el('button', 'tab');
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', String(state.cat === c.key));
      b.appendChild(document.createTextNode(c.label));
      b.appendChild(el('span', 'n', '(' + n + ')'));
      b.addEventListener('click', function () { state.cat = c.key; renderTabs(); renderGrid(); });
      tabs.appendChild(b);
    });
  }

  /* Só a média dos anúncios mais baratos (até 10); o menor anúncio sozinho nunca aparece. */
  function avgStat(dl, i) {
    var n = isNum(i.resale_avg_n) && i.resale_avg_n > 0 ? i.resale_avg_n : 10;
    stat(dl, 'Média dos ' + n + ' menores anúncios',
      isNum(i.resale_avg_low) ? robux(i.resale_avg_low) : ('resale_avg_n' in i ? 'sem anúncios' : 'na próxima coleta'));
  }
  function stat(dl, label, value) {
    var d = el('div');
    d.appendChild(el('dt', null, label));
    d.appendChild(el('dd', null, value));
    dl.appendChild(d);
  }

  var CLS_LABEL = { 'COMPRAR-AGORA': 'COMPRAR AGORA', 'OBSERVAR': 'OBSERVAR', 'EVITAR': 'EVITAR' };

  function card(i) {
    var c = el('article', 'card');
    var head = el('div', 'card-head');
    var url = safeUrl(i.thumbnail);
    function fallback() {
      var f = el('div', 'thumb', 'Sem foto');
      return f;
    }
    var th;
    if (url) {
      th = el('img', 'thumb');
      th.alt = '';
      th.loading = 'lazy';
      th.referrerPolicy = 'no-referrer';
      th.src = url;
      th.addEventListener('error', function () { if (th.parentNode) th.parentNode.replaceChild(fallback(), th); });
    } else th = fallback();
    head.appendChild(th);

    var info = el('div', 'head-info');
    var link = safeUrl(i.url);
    var name = i.name || 'Sem nome';
    if (link) {
      var a = el('a', 'name', name);
      a.href = link; a.target = '_blank'; a.rel = 'noopener noreferrer';
      info.appendChild(a);
    } else info.appendChild(el('span', 'name', name));
    var cr = el('div', 'creator', 'por ' + (i.creator_name || NA));
    if (i.creator_verified) { var v = el('span', 'verified', '✓ verificado'); cr.appendChild(v); }
    info.appendChild(cr);
    var bw = el('div');
    var bd = el('span', 'badge ' + (CLS_LABEL[i['class']] ? i['class'] : 'none'), CLS_LABEL[i['class']] || NA);
    bw.appendChild(bd);
    if (i.tipo === 'revenda') bw.appendChild(el('span', 'badge tipo-revenda', 'Compra na revenda · trava 7 dias'));
    bw.appendChild(el('span', 'score', 'Score ' + num(i.score)));
    info.appendChild(bw);
    head.appendChild(info);
    c.appendChild(head);

    var sp = window.RadarCharts && RadarCharts.sparkline(i.spark);
    var spRow = el('div', 'spark-row');
    if (sp) { spRow.appendChild(sp); spRow.appendChild(el('span', 'spark-cap', 'preço de revenda (30 dias)')); }
    else spRow.appendChild(el('span', 'spark-cap', 'Sem histórico de vendas'));
    c.appendChild(spRow);
    var ct = i.creator_track;
    var storeTxt = 'Loja sem histórico';
    if (ct && typeof ct === 'object' && isNum(ct.with_resale) && isNum(ct.pct_above_price)) {
      storeTxt = 'Loja: ' + num(Math.round(ct.with_resale * ct.pct_above_price)) + ' de ' + num(ct.with_resale) +
        ' limiteds acima do preço · retenção mediana ' + (isNum(ct.median_retention) ? margin(ct.median_retention) : NA);
    }
    c.appendChild(el('p', 'store-line', storeTxt));

    var stock = el('div', 'stock');
    var rem = isNum(i.units_remaining) ? num(i.units_remaining) : NA;
    var tot = isNum(i.total_quantity) ? num(i.total_quantity) : NA;
    stock.appendChild(document.createTextNode('Restantes: ' + rem + '/' + tot + ' · ' + pct(i.pct_sold) + ' vendido'));
    var bar = el('div', 'bar');
    bar.setAttribute('role', 'progressbar');
    bar.setAttribute('aria-label', 'Percentual vendido');
    bar.setAttribute('aria-valuemin', '0'); bar.setAttribute('aria-valuemax', '100');
    var p = isNum(i.pct_sold) ? Math.max(0, Math.min(100, i.pct_sold)) : 0;
    if (isNum(i.pct_sold)) bar.setAttribute('aria-valuenow', String(p));
    var fill = el('i'); fill.style.width = p + '%';
    bar.appendChild(fill);
    stock.appendChild(bar);
    c.appendChild(stock);

    var dl = el('dl', 'stats');
    stat(dl, 'Preço', robux(i.price));
    stat(dl, 'RAP', robux(i.rap));
    avgStat(dl, i);
    stat(dl, 'Lucro líquido', robux(i.net_profit));
    stat(dl, 'Margem', margin(i.net_margin));
    stat(dl, 'ETA p/ esgotar', eta(i.eta_hours));
    stat(dl, 'Volume 7d', num(i.volume_7d));
    stat(dl, 'Volume 30d', num(i.volume_30d));
    stat(dl, 'Retenção', isNum(i.retention) ? margin(i.retention) : NA);
    var tr = trendInfo(i.trend, i.change_7d);
    stat(dl, 'Tendência', tr.text);
    dl.lastChild.lastChild.className = 'trend ' + tr.cls;
    c.appendChild(dl);

    var det = el('details');
    det.appendChild(el('summary', null, 'Motivos e o que invalidaria'));
    function list(title, arr) {
      det.appendChild(el('h3', null, title));
      var ul = el('ul');
      if (Array.isArray(arr) && arr.length) arr.forEach(function (t) { ul.appendChild(el('li', null, String(t))); });
      else ul.appendChild(el('li', null, NA));
      det.appendChild(ul);
    }
    list('Motivos', i.reasons);
    list('O que invalidaria', i.invalidators);
    c.appendChild(det);
    var cu = catalogUrl(i);
    if (cu) {
      var act = el('div', 'card-actions');
      act.appendChild(buyBtn(i, 'primary'));
      act.appendChild(linkBtn('Acompanhar', issueUrl({ acao: 'Adicionar', item: cu, nome: i.name, preco: null, qtd: 1 })));
      c.appendChild(act);
    }
    return c;
  }

  function sorted(arr) {
    var k = state.sort;
    var asc = (k === 'units_remaining' || k === 'eta_hours');
    return arr.slice().sort(function (a, b) {
      var x = a[k], y = b[k];
      var nx = !isNum(x), ny = !isNum(y);
      if (nx && ny) return 0;
      if (nx) return 1;
      if (ny) return -1;
      return asc ? x - y : y - x;
    });
  }

  function renderGrid() {
    var items = shownItems().filter(function (i) {
      return (state.cat === 'all' || i.category === state.cat) && (!state.cls || i['class'] === state.cls);
    });
    items = sorted(items);
    var g = $('grid');
    g.textContent = '';
    items.forEach(function (i) { g.appendChild(card(i)); });
    $('empty').hidden = items.length > 0;
    $('count').textContent = items.length + (items.length === 1 ? ' item' : ' itens');
  }

  function renderLaunches(d) {
    var items = (d && d.items) || [];
    var sec = $('launches'), ul = $('launch-list');
    if (!items.length) { sec.hidden = true; return; }
    var labels = {};
    ((state.data && state.data.categories) || []).forEach(function (c) { labels[c.key] = c.label; });
    ul.textContent = '';
    items.slice(0, 5).forEach(function (i) {
      var li = el('li');
      var found = i.found_at ? new Date(i.found_at) : null;
      if (found && !isNaN(found) && Date.now() - found.getTime() < 864e5) li.className = 'fresh';
      var href = safeUrl(i.url);
      var a = el(href ? 'a' : 'span', null, i.name || 'Item sem nome');
      if (href) { a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; }
      li.appendChild(a);
      var stock = isNum(i.total_quantity) ? num(i.units_remaining) + '/' + num(i.total_quantity) + ' restantes' : 'estoque ' + NA;
      var when = found && !isNaN(found) ? found.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : NA;
      li.appendChild(el('span', 'launch-meta', [labels[i.category] || i.category || NA, robux(i.price), stock,
        i.off_sale ? 'fora de venda' : 'à venda', 'visto em ' + when].join(' · ')));
      if (catalogUrl(i)) li.appendChild(buyBtn(i, 'small'));
      ul.appendChild(li);
    });
    sec.hidden = false;
  }

  function loadLaunches() {
    return fetch(src('launches.json'), { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { state.launches = d; renderLaunches(d); })
      .catch(function () {});
  }


  /* Carteira */
  function loadCart() {
    return fetch(src('carteira.json'), { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) return null;
      return r.json();
    }).catch(function () { return null; });
  }

  function sumBox(label, value, cls) {
    var b = el('div', 'sum');
    b.appendChild(el('div', 'k', label));
    b.appendChild(el('div', 'v' + (cls ? ' ' + cls : ''), value));
    return b;
  }

  function cartCard(i) {
    var c = el('article', 'card');
    var head = el('div', 'card-head');
    var url = safeUrl(i.thumbnail), th;
    function fb() { return el('div', 'thumb', 'Sem foto'); }
    if (url) {
      th = el('img', 'thumb'); th.alt = ''; th.loading = 'lazy'; th.referrerPolicy = 'no-referrer'; th.src = url;
      th.addEventListener('error', function () { if (th.parentNode) th.parentNode.replaceChild(fb(), th); });
    } else th = fb();
    head.appendChild(th);
    var info = el('div', 'head-info');
    var link = safeUrl(i.url), name = i.name || 'Sem nome';
    if (link) { var a = el('a', 'name', name); a.href = link; a.target = '_blank'; a.rel = 'noopener noreferrer'; info.appendChild(a); }
    else info.appendChild(el('span', 'name', name));
    info.appendChild(el('div', 'creator', 'por ' + (i.creator_name || NA)));
    var tracking = !isNum(i.avg_paid);
    if (tracking) info.appendChild(el('span', 'tag', 'Só acompanhando'));
    head.appendChild(info);
    c.appendChild(head);

    var lots = Array.isArray(i.lots) ? i.lots : [];
    if (lots.length) {
      var ul = el('ul', 'lots');
      lots.forEach(function (l) {
        var t = num(l.quantidade) + ' un. a ' + (isNum(l.preco_pago) ? robux(l.preco_pago) : 'sem preço (só acompanhando)');
        if (l.comprado_em) t += ' · ' + l.comprado_em;
        if (l.nota) t += ' · ' + l.nota;
        ul.appendChild(el('li', null, t));
      });
      c.appendChild(ul);
    }

    var stockTxt = i.is_off_sale === true && isNum(i.units_remaining) && i.units_remaining === 0 ? 'esgotado'
      : (isNum(i.units_remaining) ? num(i.units_remaining) : NA) + '/' + (isNum(i.total_quantity) ? num(i.total_quantity) : NA);
    if (isNum(i.units_remaining) && i.units_remaining === 0) stockTxt = 'esgotado';

    var tr = trendInfo(i.trend, i.change_7d);
    var dl = el('dl', 'stats');
    stat(dl, 'Preço de loja', robux(i.original_price));
    stat(dl, 'Preço médio pago', tracking ? NA : robux(i.avg_paid));
    stat(dl, 'RAP', robux(i.rap));
    avgStat(dl, i);
    stat(dl, 'Restantes', stockTxt);
    stat(dl, 'Quantidade', isNum(i.quantity) ? num(i.quantity) : NA);
    stat(dl, 'Valor hoje', robux(i.value_now));
    if (!tracking) {
      stat(dl, 'Lucro/prejuízo', robux(i.pnl) + ' (' + sgnPct(i.pnl_pct) + ')');
      dl.lastChild.lastChild.className = sgnClass(i.pnl);
      dl.lastChild.lastChild.textContent = isNum(i.pnl) ? signed(i.pnl, robux) + (isNum(i.pnl_pct) ? ' (' + sgnPct(i.pnl_pct) + ')' : '') : NA;
      stat(dl, 'Empata com RAP', robux(i.breakeven_rap));
    }
    stat(dl, 'Retenção', isNum(i.retention) ? margin(i.retention) : NA);
    stat(dl, 'Tendência', tr.text);
    dl.lastChild.lastChild.className = 'trend ' + tr.cls;
    stat(dl, 'Variação 7d / 30d', sgnPct(i.change_7d) + ' / ' + sgnPct(i.change_30d));
    stat(dl, 'Dias com o item', isNum(i.days_held) ? num(i.days_held) : NA);
    c.appendChild(dl);

    c.appendChild(window.RadarCharts ? RadarCharts.itemChart(i) : el('p', 'chart-empty', 'Ainda sem histórico de vendas'));

    var cu = catalogUrl(i);
    if (cu) {
      var act = el('div', 'card-actions');
      if (tracking) {
        var ib = el('button', 'btn primary', 'Informar preço');
        ib.type = 'button';
        ib.addEventListener('click', function () { openBuy(i); });
        act.appendChild(ib);
      }
      act.appendChild(linkBtn('Remover', issueUrl({ acao: 'Remover', item: cu, nome: i.name, preco: null, qtd: 1 }), 'danger'));
      c.appendChild(act);
    }
    return c;
  }

  function renderCart() {
    var d = state.cart;
    var items = d && Array.isArray(d.items) ? d.items : [];
    var sum = $('cart-summary'), grid = $('cart-grid');
    grid.textContent = '';
    sum.textContent = '';
    $('cart-empty').hidden = items.length > 0;
    sum.hidden = !items.length;
    $('cart-count').textContent = items.length ? items.length + (items.length === 1 ? ' item' : ' itens') : '';
    if (!items.length) return;
    var t = d.totals || {};
    sum.appendChild(sumBox('Custo total', robux(t.cost)));
    sum.appendChild(sumBox('Valor hoje (RAP ou média dos 10 menores anúncios, o mais baixo)', robux(t.value_now)));
    sum.appendChild(sumBox('Lucro/prejuízo', signed(t.pnl, robux), sgnClass(t.pnl)));
    sum.appendChild(sumBox('Lucro/prejuízo %', sgnPct(t.pnl_pct), sgnClass(t.pnl_pct)));
    items.forEach(function (i) { grid.appendChild(cartCard(i)); });
  }

  function parseItem(v) {
    v = String(v || '').trim();
    var m = /^(\d{3,})$/.exec(v) || /roblox\.com\/(?:[a-z-]+\/)?(?:catalog|library)\/(\d+)/i.exec(v) || /roblox\.com\/bundles\/(\d+)/i.exec(v);
    return m ? m[1] : null;
  }

  function todayLocal() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  /* Procura o item nos dados já carregados (radar, lançamentos, carteira) para preencher nome e preço de loja. */
  function knownItem(id) {
    var lists = [state.data && state.data.items, state.launches && state.launches.items, state.cart && state.cart.items];
    for (var k = 0; k < lists.length; k++) {
      var arr = Array.isArray(lists[k]) ? lists[k] : [];
      for (var j = 0; j < arr.length; j++) if (arr[j] && String(arr[j].asset_id) === String(id)) return arr[j];
    }
    return null;
  }
  function showItemHint(i) {
    var h = $('af-found');
    if (!i) { h.hidden = true; h.textContent = ''; return; }
    h.textContent = (i.name || 'Item ' + i.asset_id) + (isNum(i.price) ? ' · preço de loja ' + robux(i.price) : '');
    h.hidden = false;
  }
  /* Botão "Comprei": abre o formulário da carteira já preenchido com o item e o preço de loja. */
  function openBuy(i) {
    var f = $('add-form');
    setView('carteira', true);
    $('af-more').open = true;
    $('af-error').hidden = true;
    $('af-item').value = catalogUrl(i);
    $('af-price').value = isNum(i.price) ? String(i.price) : '';
    $('af-qty').value = '1';
    $('af-date').value = todayLocal();
    showItemHint(i);
    f.scrollIntoView({ block: 'start' });
    var p = $('af-price');
    p.focus();
    try { p.select(); } catch (e) {}
  }
  function buyBtn(i, cls) {
    var b = el('button', 'btn ' + (cls || ''), 'Comprei');
    b.type = 'button';
    b.setAttribute('aria-label', 'Comprei ' + (i.name || 'este item') + ': cadastrar na carteira');
    b.addEventListener('click', function () { openBuy(i); });
    return b;
  }

  function initForm() {
    var f = $('add-form'), err = $('af-error');
    if (!$('af-date').value) $('af-date').value = todayLocal();
    $('af-item').addEventListener('input', function () {
      var id = parseItem(this.value), i = id ? knownItem(id) : null;
      showItemHint(i);
      if (i && isNum(i.price) && $('af-price').value.trim() === '') $('af-price').value = String(i.price);
    });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var id = parseItem($('af-item').value);
      if (!id) { err.textContent = 'Informe o link do catálogo (roblox.com/catalog/…) ou apenas o número do item.'; err.hidden = false; return; }
      var pv = $('af-price').value.trim(), price = null;
      if (pv !== '') {
        price = Number(pv);
        if (!/^\d+$/.test(pv) || !isFinite(price)) { err.textContent = 'Preço pago: use um número inteiro de Robux (ex.: 120).'; err.hidden = false; return; }
      }
      var q = parseInt($('af-qty').value, 10);
      if (!isFinite(q) || q < 1 || q > 100) { err.textContent = 'A quantidade precisa ser de 1 a 100.'; err.hidden = false; return; }
      err.hidden = true;
      var known = knownItem(id);
      var href = issueUrl({ acao: 'Adicionar', item: 'https://www.roblox.com/catalog/' + id, nome: (known && known.name) || id, preco: price, qtd: q, data: $('af-date').value });
      window.open(href, '_blank', 'noopener,noreferrer');
    });
  }

  /* Visões */
  function setView(v, persist) {
    if (v !== 'carteira') v = 'radar';
    state.view = v;
    $('view-radar').hidden = v !== 'radar';
    $('view-carteira').hidden = v !== 'carteira';
    ['radar', 'carteira'].forEach(function (k) {
      var b = $('vt-' + k);
      b.setAttribute('aria-selected', String(k === v));
      b.tabIndex = k === v ? 0 : -1;
    });
    if (persist) {
      try { localStorage.setItem('radar-view', v); } catch (e) {}
      try { history.replaceState(null, '', v === 'carteira' ? '#carteira' : location.pathname + location.search); } catch (e) {}
    }
  }
  function initViews() {
    var saved = null;
    try { saved = localStorage.getItem('radar-view'); } catch (e) {}
    setView(location.hash === '#carteira' ? 'carteira' : (location.hash === '#radar' ? 'radar' : saved), false);
    ['radar', 'carteira'].forEach(function (k) {
      $('vt-' + k).addEventListener('click', function () { setView(k, true); });
    });
    $('views').addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { var k = state.view === 'radar' ? 'carteira' : 'radar'; setView(k, true); $('vt-' + k).focus(); }
    });
    window.addEventListener('hashchange', function () {
      if (location.hash === '#carteira') setView('carteira', false); else if (location.hash === '#radar') setView('radar', false);
    });
  }

  function refresh(first) {
    loadLaunches();
    loadCart().then(function (c) {
      var key = c && Array.isArray(c.items) ? (c.generated_at || '') + '|' + c.items.length : 'vazio';
      if (state.cart !== undefined && key === state.cartKey) return;
      state.cart = c; state.cartKey = key;
      renderCart();
    });
    return load().then(function (d) {
      var changed = !state.data || state.data.generated_at !== d.generated_at || state.data.run_status !== d.run_status;
      state.data = d; state.loadFailed = false;
      renderHeader(d);
      if (changed || first) { renderTabs(); renderGrid(); }
    }).catch(function () {
      state.loadFailed = true;
      if (!first && state.data) return; // mantém os dados já exibidos se a rede cair
      $('updated').textContent = 'Não foi possível carregar os dados.';
      var b = $('banner');
      b.textContent = 'Não foi possível carregar data.json. Verifique a conexão e tente novamente.';
      b.hidden = false;
    });
  }

  // Próxima coleta agendada: radar.yml roda aos 17 min das horas pares (UTC).
  function nextRun() {
    var n = new Date(), d = new Date(n.getTime());
    d.setUTCMinutes(17, 0, 0);
    if (d.getUTCHours() % 2) d.setUTCHours(d.getUTCHours() + 1);
    if (d <= n) d.setUTCHours(d.getUTCHours() + 2);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
  function initRefresh() {
    var btn = $('refresh-btn'), msg = $('refresh-msg');
    $('run-link').href = 'https://github.com/' + repoSlug() + '/actions/workflows/radar.yml';
    btn.addEventListener('click', function () {
      if (btn.disabled) return;
      var before = state.data && state.data.generated_at;
      btn.disabled = true; btn.classList.add('spin');
      bust = '?t=' + Date.now();
      refresh(false).then(function () {
        if (state.loadFailed) msg.textContent = 'Sem conexão: não consegui buscar a lista.';
        else if (state.data.generated_at !== before) msg.textContent = 'Lista atualizada com a coleta mais recente.';
        else msg.textContent = 'Você já está vendo a coleta mais recente. A próxima automática sai por volta das ' + nextRun() + '; para não esperar, use “Rodar coleta agora” e toque em ↻ depois de alguns minutos.';
        msg.hidden = false;
      }).then(function () { bust = ''; btn.disabled = false; btn.classList.remove('spin'); });
    });
  }

  /* Instalar como app. Chrome/Android: usa o aviso de instalação do navegador quando ele aparece.
     Sem esse aviso (outro navegador, link aberto dentro de outro app, iPhone) mostra o passo manual. */
  function initInstall() {
    var btn = $('install-btn'), msg = $('install-msg'), prompt = null;
    var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
    if (standalone) return;
    var ua = navigator.userAgent || '';
    var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
    var inApp = /FBAN|FBAV|Instagram|Line\/|Discord|GitHub|; wv\)|WhatsApp|Telegram/i.test(ua);
    function manual() {
      if (ios) return 'No iPhone: abra no Safari, toque em Compartilhar (□↑) e em “Adicionar à Tela de Início”.';
      if (inApp) return 'Você abriu o site dentro de outro app. Toque em ⋮ → “Abrir no Chrome” e depois em “Instalar app”.';
      return 'No Chrome: toque em ⋮ (canto de cima) → “Instalar app” ou “Adicionar à tela inicial”. Se não aparecer, o app já pode estar instalado: procure “Radar UGC” na lista de apps.';
    }
    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      prompt = e;
      btn.hidden = false;
    });
    window.addEventListener('appinstalled', function () {
      prompt = null; btn.hidden = true;
      msg.textContent = 'App instalado. Abra pelo ícone “Radar UGC”.'; msg.hidden = false;
    });
    btn.addEventListener('click', function () {
      if (prompt) {
        var p = prompt; prompt = null;
        p.prompt();
        p.userChoice.then(function (r) { if (r.outcome !== 'accepted') { prompt = null; msg.textContent = manual(); msg.hidden = false; } });
        return;
      }
      msg.textContent = manual();
      msg.hidden = !msg.hidden;
    });
    // Se o Chrome não oferecer a instalação em alguns segundos, o botão mostra o passo manual.
    setTimeout(function () { btn.hidden = false; }, ios || inApp ? 0 : 3000);
  }

  function init() {
    initTheme();
    initInstall();
    initRefresh();
    initViews();
    initForm();
    $('class-filter').addEventListener('change', function (e) { state.cls = e.target.value; renderGrid(); });
    $('sort').addEventListener('change', function (e) { state.sort = e.target.value; renderGrid(); });
    refresh(true);
    // Atualiza sozinho enquanto o app está aberto (a coleta roda a cada 2 h no GitHub).
    setInterval(function () { if (!document.hidden) refresh(false); }, 5 * 60 * 1000);
    // Mantém o "há X min" do topo em dia entre uma busca e outra.
    setInterval(function () { if (!document.hidden && state.data) renderHeader(state.data); }, 60 * 1000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) refresh(false); });
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function () {
        navigator.serviceWorker.register('sw.js').catch(function () {});
      });
    }
  }
  init();
})();
