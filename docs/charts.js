/* Gráficos em SVG inline (sem bibliotecas; funciona offline). ES5. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var NA = '—';
  var nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) e.setAttribute(k, String(attrs[k]));
    return e;
  }
  function hEl(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function parseDate(s) { var t = typeof s === 'string' ? Date.parse(s) : NaN; return isNaN(t) ? null : t; }
  function fmtDate(t) { return new Date(t).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit', timeZone: 'UTC' }); }
  function fmtShort(t) { return new Date(t).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', timeZone: 'UTC' }); }
  function compact(v) {
    if (!isNum(v)) return NA;
    if (Math.abs(v) >= 1000) return nf.format(Math.round(v)).replace(/\s/g, '');
    return nf.format(Math.round(v * 10) / 10);
  }

  /* Mini-gráfico do card do radar: spark = [[data, preço], ...] */
  function sparkline(spark) {
    var pts = [];
    (Array.isArray(spark) ? spark : []).forEach(function (p) {
      if (Array.isArray(p) && isNum(p[1])) pts.push(p[1]);
    });
    if (pts.length < 2) return null;
    var W = 120, H = 32, pad = 3;
    var min = Math.min.apply(null, pts), max = Math.max.apply(null, pts);
    var span = max - min || 1;
    var d = pts.map(function (v, i) {
      var x = pad + (W - 2 * pad) * i / (pts.length - 1);
      var y = H - pad - (H - 2 * pad) * (v - min) / span;
      return (i ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
    }).join(' ');
    var up = pts[pts.length - 1] >= pts[0];
    var s = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, 'class': 'spark ' + (up ? 'up' : 'down'), role: 'img',
      preserveAspectRatio: 'none' });
    s.setAttribute('aria-label', 'Preço dos últimos ' + pts.length + ' dias com venda: de ' + compact(pts[0]) + ' a ' + compact(pts[pts.length - 1]));
    s.appendChild(svgEl('path', { d: d, 'class': 'spark-line', fill: 'none' }));
    return s;
  }

  var PERIODS = [{ k: '7', label: '7d', days: 7 }, { k: '30', label: '30d', days: 30 }, { k: '90', label: '90d', days: 90 }, { k: 'all', label: 'Tudo', days: null }];

  /* Gráfico completo de um item da carteira. Devolve um elemento <div>. */
  function itemChart(item) {
    var wrap = hEl('div', 'chart');
    var series = item && item.series || {};
    var chart = [];
    (Array.isArray(series.chart) ? series.chart : []).forEach(function (p) {
      var t = Array.isArray(p) ? parseDate(p[0]) : null;
      if (t != null && isNum(p[1])) chart.push({ t: t, price: p[1], vol: isNum(p[2]) ? p[2] : null });
    });
    chart.sort(function (a, b) { return a.t - b.t; });
    if (!chart.length) {
      wrap.appendChild(hEl('p', 'chart-empty', 'Ainda sem histórico de vendas'));
      return wrap;
    }
    var tracked = [];
    (Array.isArray(series.tracked) ? series.tracked : []).forEach(function (p) {
      var t = Array.isArray(p) ? parseDate(p[0]) : null;
      if (t != null && isNum(p[1])) tracked.push({ t: t, rap: p[1] });
    });

    var period = chart.length > 30 ? '90' : 'all';
    var idx = -1;

    var bar = hEl('div', 'chart-periods');
    bar.setAttribute('role', 'group');
    bar.setAttribute('aria-label', 'Período do gráfico');
    var box = hEl('div', 'chart-box');
    var tip = hEl('div', 'chart-tip');
    tip.hidden = true;
    tip.setAttribute('role', 'status');
    var legend = hEl('p', 'chart-legend');
    var btns = {};
    PERIODS.forEach(function (p) {
      var b = hEl('button', 'chip', p.label);
      b.type = 'button';
      b.addEventListener('click', function () { period = p.k; idx = -1; draw(); });
      btns[p.k] = b;
      bar.appendChild(b);
    });
    wrap.appendChild(bar);
    wrap.appendChild(box);
    wrap.appendChild(legend);

    function draw() {
      PERIODS.forEach(function (p) { btns[p.k].setAttribute('aria-pressed', String(p.k === period)); });
      var per = PERIODS.filter(function (p) { return p.k === period; })[0];
      var last = chart[chart.length - 1].t;
      var from = per.days ? last - per.days * 864e5 : -Infinity;
      var pts = chart.filter(function (p) { return p.t >= from; });
      var trk = tracked.filter(function (p) { return p.t >= from; });
      box.textContent = '';
      var hasPaid = isNum(item.avg_paid), hasBe = isNum(item.breakeven_rap);
      var W = 640, H = 280, L = 46, R = 10, T = 12, B = 26;
      var pw = W - L - R, ph = H - T - B;
      var vals = pts.map(function (p) { return p.price; }).concat(trk.map(function (p) { return p.rap; }));
      if (hasPaid) vals.push(item.avg_paid);
      if (hasBe) vals.push(item.breakeven_rap);
      var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
      if (max === min) { max += 1; min -= 1; }
      var padv = (max - min) * 0.06;
      min = Math.max(0, min - padv); max += padv;
      var t0 = pts[0].t, t1 = pts[pts.length - 1].t;
      if (trk.length) { t0 = Math.min(t0, trk[0].t); t1 = Math.max(t1, trk[trk.length - 1].t); }
      var tspan = t1 - t0 || 1;
      function X(t) { return L + pw * (t - t0) / tspan; }
      function Y(v) { return T + ph * (1 - (v - min) / (max - min)); }
      var maxVol = 0;
      pts.forEach(function (p) { if (p.vol != null && p.vol > maxVol) maxVol = p.vol; });

      var svg = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, 'class': 'chart-svg', role: 'img' });
      svg.setAttribute('aria-label', 'Gráfico de preço de revenda de ' + (item.name || 'item') + ', ' + pts.length + ' dias com venda');
      // grade + eixo de preço (mín/máx)
      [min + padv, max - padv].forEach(function (v) {
        svg.appendChild(svgEl('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), 'class': 'c-grid' }));
        var tx = svgEl('text', { x: L - 6, y: Y(v) + 4, 'class': 'c-axis', 'text-anchor': 'end' });
        tx.textContent = compact(v);
        svg.appendChild(tx);
      });
      // eixo de datas (4 rótulos)
      for (var k = 0; k < 4; k++) {
        var t = t0 + tspan * k / 3;
        var anchor = k === 0 ? 'start' : (k === 3 ? 'end' : 'middle');
        var dx = svgEl('text', { x: X(t), y: H - 8, 'class': 'c-axis', 'text-anchor': anchor });
        dx.textContent = fmtShort(t);
        svg.appendChild(dx);
      }
      // barras de volume (discretas, 22% da altura)
      if (maxVol > 0) {
        var bw = Math.max(1.5, Math.min(14, pw / Math.max(pts.length, 1) * 0.7));
        pts.forEach(function (p) {
          if (!p.vol) return;
          var h = (ph * 0.22) * p.vol / maxVol;
          svg.appendChild(svgEl('rect', { x: X(p.t) - bw / 2, y: T + ph - h, width: bw, height: Math.max(h, 1), 'class': 'c-vol' }));
        });
      }
      // linhas de referência
      function refLine(v, cls, label) {
        svg.appendChild(svgEl('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), 'class': cls }));
        var tx = svgEl('text', { x: W - R - 2, y: Y(v) - 4, 'class': 'c-reflabel ' + cls, 'text-anchor': 'end' });
        tx.textContent = label + ' ' + compact(v);
        svg.appendChild(tx);
      }
      if (hasPaid) refLine(item.avg_paid, 'c-paid', 'Pago');
      if (hasBe) refLine(item.breakeven_rap, 'c-be', 'Empata');
      // linha de preço
      var d = pts.map(function (p, i) { return (i ? 'L' : 'M') + X(p.t).toFixed(1) + ' ' + Y(p.price).toFixed(1); }).join(' ');
      svg.appendChild(svgEl('path', { d: d, 'class': 'c-line', fill: 'none' }));
      if (pts.length < 40) pts.forEach(function (p) { svg.appendChild(svgEl('circle', { cx: X(p.t), cy: Y(p.price), r: 2.5, 'class': 'c-dot' })); });
      // pontos do RAP coletado
      trk.forEach(function (p) { svg.appendChild(svgEl('circle', { cx: X(p.t), cy: Y(p.rap), r: 3.5, 'class': 'c-rap' })); });
      // cursor
      var cross = svgEl('line', { y1: T, y2: T + ph, 'class': 'c-cross' });
      var cdot = svgEl('circle', { r: 5, 'class': 'c-curs' });
      cross.style.display = 'none'; cdot.style.display = 'none';
      svg.appendChild(cross); svg.appendChild(cdot);
      box.appendChild(svg);
      box.appendChild(tip);

      function show(i) {
        if (i < 0 || i >= pts.length) { tip.hidden = true; cross.style.display = 'none'; cdot.style.display = 'none'; return; }
        idx = i;
        var p = pts[i], x = X(p.t);
        cross.setAttribute('x1', x); cross.setAttribute('x2', x); cross.style.display = '';
        cdot.setAttribute('cx', x); cdot.setAttribute('cy', Y(p.price)); cdot.style.display = '';
        tip.textContent = fmtDate(p.t) + ' · preço ' + compact(p.price) + ' ⏣ · volume ' + (p.vol == null ? NA : compact(p.vol));
        tip.hidden = false;
        var frac = x / W;
        tip.style.left = Math.max(0, Math.min(100, frac * 100)) + '%';
        tip.style.transform = 'translateX(' + (frac > 0.6 ? '-100%' : frac < 0.4 ? '0' : '-50%') + ')';
      }
      function nearest(ev) {
        var r = svg.getBoundingClientRect();
        if (!r.width) return -1;
        var x = (ev.clientX - r.left) / r.width * W;
        var best = -1, bd = Infinity;
        pts.forEach(function (p, i) { var dd = Math.abs(X(p.t) - x); if (dd < bd) { bd = dd; best = i; } });
        return best;
      }
      svg.addEventListener('pointermove', function (ev) { show(nearest(ev)); });
      svg.addEventListener('pointerdown', function (ev) { show(nearest(ev)); });
      svg.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse') show(-1); });
      box.tabIndex = 0;
      box.setAttribute('aria-label', 'Gráfico interativo: use as setas esquerda e direita para ver cada dia');
      box.onkeydown = function (ev) {
        var n = idx < 0 ? (ev.key === 'ArrowLeft' ? pts.length - 1 : 0) : idx + (ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0);
        if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') { ev.preventDefault(); show(Math.max(0, Math.min(pts.length - 1, n))); }
        else if (ev.key === 'Escape') show(-1);
      };

      var lg = ['Linha: preço médio diário na revenda', 'Barras: volume'];
      if (hasPaid) lg.push('Tracejado: preço médio pago');
      if (hasBe) lg.push('Pontilhado: RAP para empatar');
      if (trk.length) lg.push('Pontos: RAP coletado');
      legend.textContent = lg.join(' · ');
    }
    draw();
    return wrap;
  }

  window.RadarCharts = { sparkline: sparkline, itemChart: itemChart };
})();
