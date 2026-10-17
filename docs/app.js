(function () {
  'use strict';
  var NA = '—';
  var CUR = '⏣';
  var state = { data: null, cat: 'all', cls: '', sort: 'score' };
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
  function safeUrl(u) { return typeof u === 'string' && /^https?:\/\//i.test(u) ? u : null; }

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
  function load() {
    return fetch('data.json', { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function renderHeader(d) {
    var t = NA;
    if (d.generated_at) {
      var dt = new Date(d.generated_at);
      if (!isNaN(dt)) t = dt.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
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

  function renderTabs() {
    var d = state.data, items = d.items || [];
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
    bw.appendChild(el('span', 'score', 'Score ' + num(i.score)));
    info.appendChild(bw);
    head.appendChild(info);
    c.appendChild(head);

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
    stat(dl, 'Menor revenda', robux(i.lowest_resale));
    stat(dl, 'Lucro líquido', robux(i.net_profit));
    stat(dl, 'Margem', margin(i.net_margin));
    stat(dl, 'ETA p/ esgotar', eta(i.eta_hours));
    stat(dl, 'Volume 7d', num(i.volume_7d));
    stat(dl, 'Volume 30d', num(i.volume_30d));
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
    var items = (state.data.items || []).filter(function (i) {
      return (state.cat === 'all' || i.category === state.cat) && (!state.cls || i['class'] === state.cls);
    });
    items = sorted(items);
    var g = $('grid');
    g.textContent = '';
    items.forEach(function (i) { g.appendChild(card(i)); });
    $('empty').hidden = items.length > 0;
    $('count').textContent = items.length + (items.length === 1 ? ' item' : ' itens');
  }

  function init() {
    initTheme();
    $('class-filter').addEventListener('change', function (e) { state.cls = e.target.value; renderGrid(); });
    $('sort').addEventListener('change', function (e) { state.sort = e.target.value; renderGrid(); });
    load().then(function (d) {
      state.data = d;
      renderHeader(d); renderTabs(); renderGrid();
    }).catch(function () {
      $('updated').textContent = 'Não foi possível carregar os dados.';
      var b = $('banner');
      b.textContent = 'Não foi possível carregar data.json. Verifique a conexão e tente novamente.';
      b.hidden = false;
    });
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function () {
        navigator.serviceWorker.register('sw.js').catch(function () {});
      });
    }
  }
  init();
})();
