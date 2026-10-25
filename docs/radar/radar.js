(function () {
  "use strict";
  var D = window.CAFE_DATA;
  var $ = function (id) { return document.getElementById(id); };
  var fmt = d3.format(",");
  var sgn = function (v) { return (v > 0 ? "+" : v < 0 ? "−" : "±") + fmt(Math.abs(v)); };
  var pct = d3.format(".0%");
  var css = function (n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); };
  var reduce = function () { return matchMedia("(prefers-reduced-motion: reduce)").matches; };
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  var SIDO = ["서울", "경기", "인천", "부산", "대구", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남광주", "경북", "경남", "제주", "기타"];
  var SI = {}; SIDO.forEach(function (s, i) { SI[s] = i; });
  var LONG = { "서울": "서울특별시", "경기": "경기도", "인천": "인천광역시", "부산": "부산광역시", "대구": "대구광역시", "대전": "대전광역시", "울산": "울산광역시", "세종": "세종특별자치시", "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도", "전북": "전북특별자치도", "전남광주": "전남광주통합특별시", "경북": "경상북도", "경남": "경상남도", "제주": "제주특별자치도" };
  var GEO = { "서울특별시": "서울", "경기도": "경기", "인천광역시": "인천", "부산광역시": "부산", "대구광역시": "대구", "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "강원도": "강원", "충청북도": "충북", "충청남도": "충남", "전라북도": "전북", "전라남도": "전남광주", "광주광역시": "전남광주", "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주" };
  var TNAME = ["개인 카페", "프랜차이즈", "체인 추정", "시니어·복지"];
  var AL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-./:;<=>?@[]^_`{}~";
  var AIX = {}; for (var a = 0; a < AL.length; a++) AIX[AL[a]] = a;
  function dec(s) { var out = []; for (var i = 0; i < s.length; i++) { if (s[i] === "'") { var j = s.indexOf("'", i + 1); out.push(parseInt(s.slice(i + 1, j), 36)); i = j; } else out.push(AIX[s[i]]); } return out; }

  var MAXD = D.maxD;
  var DAY = 864e5, W0 = Date.parse((D.w0 || "2024-10-28") + "T00:00:00Z"), PT0 = D.pt0 || "2026-09-01";
  var NM = 0, NW = 0;
  var PT0_TXT = PT0.slice(0, 4) + "년 " + (+PT0.slice(5, 7)) + "월";
  var ST = D.st.map(function (r) { return r.map(function (x) { return { m: dec(x[0]), w: dec(x[1]) }; }); });
  NM = ST[0][0].m.length / 2; NW = ST[0][0].w.length / 2;
  var AREAS = D.areas.map(function (a) { return { name: a[0], sido: a[0].split(" ")[0], short: a[0].split(" ").slice(1).join(" "), lat: a[1], lon: a[2], s: a[3], m: dec(a[4]), w: dec(a[5]) }; })
    .filter(function (a) { return a.sido !== "기타" && (a.s > 0 || a.m.some(function (v) { return v > 0; })); });
  var AREA_BY = {}; AREAS.forEach(function (a) { AREA_BY[a.name] = a; });
  var BRANDS = D.brands.map(function (b) { return { name: b[0], s: b[1], ss: b[2], m: dec(b[3]), w: dec(b[4]) }; });
  var PTS = D.pts.map(function (p, i) { return { i: i, pd: p[0], cd: p[1], name: p[2], sido: SIDO[p[3]], area: p[4], lat: p[5], lon: p[6], t: p[7], brand: p[8] }; });
  var SEN = D.sen.map(function (s, i) { return { i: i, pd: s[0], cd: s[1], act: s[2], name: s[3], sido: s[4], area: s[5], lat: s[6], lon: s[7], tmp: s[8], t: 3 }; });
  var TOTAL_STOCK = D.stock.reduce(function (s, r) { return s + r.reduce(function (x, y) { return x + y; }, 0); }, 0);
  $("ledeStock").textContent = fmt(TOTAL_STOCK);
  $("ptSince").textContent = PT0_TXT;
  $("srcDate").textContent = MAXD.slice(0, 4) + "년 " + (+MAXD.slice(5, 7)) + "월 " + (+MAXD.slice(8)) + "일";

  // ---------- 기간 ----------
  function iso(t) { return new Date(t).toISOString().slice(0, 10); }
  function md(d) { return (+d.slice(5, 7)) + "/" + (+d.slice(8, 10)); }
  var UNITS = {
    w: { n: NW, base: "w", name: "주", span: function (i) { return [iso(W0 + i * 7 * DAY), iso(W0 + (i * 7 + 6) * DAY)]; },
      label: function (i) { var s = UNITS.w.span(i); return s[0].slice(0, 4) + "년 " + md(s[0]) + "–" + md(s[1]); },
      short: function (i) { return md(UNITS.w.span(i)[0]); }, cols: function (i) { return [i]; }, yoy: 52 },
    m: { n: NM, base: "m", name: "달", span: function (i) { var y = 2015 + Math.floor(i / 12), m = i % 12; return [iso(Date.UTC(y, m, 1)), iso(Date.UTC(y, m + 1, 0))]; },
      label: function (i) { return (2015 + Math.floor(i / 12)) + "년 " + (i % 12 + 1) + "월"; },
      short: function (i) { return (i % 12 === 0 ? String(2015 + i / 12).slice(2) + "." : "") + (i % 12 + 1); }, cols: function (i) { return [i]; }, yoy: 12 },
    q: { n: Math.ceil(NM / 3), base: "m", name: "분기", span: function (i) { var y = 2015 + Math.floor(i / 4), q = i % 4; return [iso(Date.UTC(y, q * 3, 1)), iso(Date.UTC(y, q * 3 + 3, 0))]; },
      label: function (i) { return (2015 + Math.floor(i / 4)) + "년 " + (i % 4 + 1) + "분기"; },
      short: function (i) { return String(2015 + Math.floor(i / 4)).slice(2) + "Q" + (i % 4 + 1); },
      cols: function (i) { return [i * 3, i * 3 + 1, i * 3 + 2].filter(function (x) { return x < NM; }); }, yoy: 4 },
    y: { n: Math.ceil(NM / 12), base: "m", name: "해", span: function (i) { return [(2015 + i) + "-01-01", (2015 + i) + "-12-31"]; },
      label: function (i) { return (2015 + i) + "년"; }, short: function (i) { return String(2015 + i); },
      cols: function (i) { return d3.range(i * 12, Math.min(NM, i * 12 + 12)); }, yoy: 1 }
  };
  var SHOW = { w: 52, m: 48, q: 48, y: 12 };
  function isPartial(u, i) { return UNITS[u].span(i)[1] > MAXD; }
  function maxIdx(u) { var i = UNITS[u].n - 1; while (i > 0 && UNITS[u].span(i)[0] > MAXD) i--; return i; }
  function lastFull(u) { var i = maxIdx(u); while (i > 0 && isPartial(u, i)) i--; return i; }

  var state = { unit: "w", idx: lastFull("w"), sido: "", area: "", type: "all", kind: "all", q: "", sen: "1", show: { open: true, close: true } };

  function sumCols(arr, cols) { var o = 0, c = 0; cols.forEach(function (j) { o += arr[j * 2] || 0; c += arr[j * 2 + 1] || 0; }); return [o, c]; }
  function scopeSidos() { return state.sido ? [SI[state.sido]] : d3.range(SIDO.length); }
  function types() { return state.type === "all" ? [0, 1, 2, 3] : [+state.type]; }
  function stVal(u, i, sids, ts) {
    var U = UNITS[u], cols = U.cols(i), o = 0, c = 0;
    sids.forEach(function (si) { ts.forEach(function (t) { var v = sumCols(ST[si][t][U.base], cols); o += v[0]; c += v[1]; }); });
    return [o, c];
  }
  function areaVal(a, u, i) { var U = UNITS[u]; return sumCols(a[U.base], U.cols(i)); }
  function brandVal(b, u, i) { var U = UNITS[u]; return sumCols(b[U.base], U.cols(i)); }
  function scopeVal(u, i) { return state.area ? areaVal(AREA_BY[state.area], u, i) : stVal(u, i, scopeSidos(), types()); }
  function scopeName() { return state.area ? state.area.replace(state.sido + " ", LONG[state.sido] + " ") : state.sido ? LONG[state.sido] : "전국"; }
  function inPer(d, sp) { return d && d >= sp[0] && d <= sp[1]; }

  // ---------- 주소(#) ----------
  function writeHash() {
    var h = "#" + state.unit + state.idx + (state.sido ? "-" + state.sido : "") + (state.area ? "-" + state.area.split(" ").slice(1).join("_") : "");
    try { history.replaceState(null, "", h); } catch (e) { /* 주소 바꾸기가 막힌 환경 */ }
  }
  function readHash() {
    var h = decodeURIComponent(location.hash.slice(1)); if (!h) return;
    var m = h.match(/^([wmqy])(\d+)(?:-([^-]+))?(?:-(.+))?$/); if (!m) return;
    state.unit = m[1]; state.idx = Math.min(+m[2], maxIdx(m[1]));
    if (m[3] && SI[m[3]] != null && m[3] !== "기타") state.sido = m[3];
    if (m[4]) { var nm = state.sido + " " + m[4].replace(/_/g, " "); if (AREA_BY[nm]) state.area = nm; }
  }

  // ---------- 지역 고르기 ----------
  var sidoSel = $("sidoSel"), sggSel = $("sggSel");
  [["", "전국"]].concat(SIDO.slice(0, 16).map(function (s) { return [s, LONG[s]]; })).forEach(function (x) { var o = el("option", null, x[1]); o.value = x[0]; sidoSel.appendChild(o); });
  function fillSgg() {
    sggSel.innerHTML = "";
    var o = el("option", null, state.sido ? "시·군·구 전체" : "시·도를 먼저 고르세요"); o.value = ""; sggSel.appendChild(o);
    sggSel.disabled = !state.sido;
    if (!state.sido) return;
    AREAS.filter(function (a) { return a.sido === state.sido; }).sort(function (x, y) { return x.short.localeCompare(y.short, "ko"); })
      .forEach(function (a) { var op = el("option", null, a.short); op.value = a.name; sggSel.appendChild(op); });
  }
  sidoSel.onchange = function () { setScope(sidoSel.value, ""); };
  sggSel.onchange = function () { setScope(state.sido, sggSel.value); };
  var QUICK = [["", "", "전국"], ["서울", "", "서울"], ["경기", "", "경기"], ["경기", "경기 광명시", "광명시"], ["서울", "서울 강남구", "강남구"], ["부산", "", "부산"], ["제주", "", "제주"]];
  QUICK.forEach(function (q) { var b = el("button", "chip-btn", q[2]); b.type = "button"; b.onclick = function () { setScope(q[0], q[1]); }; $("quick").appendChild(b); });
  function markQuick() { var bs = $("quick").querySelectorAll("button"); QUICK.forEach(function (q, k) { bs[k].setAttribute("aria-pressed", q[0] === state.sido && q[1] === state.area); }); }

  // ---------- 기간·유형 컨트롤 ----------
  var perSel = $("perSel");
  function fillPeriods() {
    var U = UNITS[state.unit]; perSel.innerHTML = "";
    for (var i = maxIdx(state.unit); i >= 0; i--) { var o = el("option", null, U.label(i) + (isPartial(state.unit, i) ? " (진행 중)" : "")); o.value = i; perSel.appendChild(o); }
    perSel.value = state.idx;
  }
  function setIdx(i) { state.idx = Math.max(0, Math.min(maxIdx(state.unit), i)); perSel.value = state.idx; render(); }
  perSel.onchange = function () { setIdx(+perSel.value); };
  $("prevBtn").onclick = function () { setIdx(state.idx - 1); };
  $("nextBtn").onclick = function () { setIdx(state.idx + 1); };
  function pressed(segId, attr, val) { $(segId).querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset[attr] === val); }); }
  $("unitSeg").querySelectorAll("button").forEach(function (b) {
    b.onclick = function () {
      var sp = UNITS[state.unit].span(state.idx); state.unit = b.dataset.u; pressed("unitSeg", "u", state.unit);
      var U = UNITS[state.unit], target = sp[1] < MAXD ? sp[1] : MAXD, k = -1;
      for (var i = 0; i < U.n; i++) if (U.span(i)[0] <= target) k = i;
      state.idx = (k < 0 || isPartial(state.unit, k)) ? lastFull(state.unit) : k;
      fillPeriods(); render();
    };
  });
  $("typeSeg").querySelectorAll("button").forEach(function (b) { b.onclick = function () { state.type = b.dataset.t; pressed("typeSeg", "t", state.type); render(); }; });
  $("kindSeg").querySelectorAll("button").forEach(function (b) { b.onclick = function () { state.kind = b.dataset.k; pressed("kindSeg", "k", state.kind); renderList(); MAP.restyle(); }; });
  $("senSeg").querySelectorAll("button").forEach(function (b) { b.onclick = function () { state.sen = b.dataset.s; pressed("senSeg", "s", state.sen); renderSenior(); }; });
  $("listQ").oninput = function (e) { state.q = e.target.value.trim().toLowerCase(); renderList(); };
  $("showOpen").onchange = function (e) { state.show.open = e.target.checked; MAP.restyle(); };
  $("showClose").onchange = function (e) { state.show.close = e.target.checked; MAP.restyle(); };

  // ---------- 지도 공통 ----------
  var mapBox = document.querySelector(".map-box");
  var provNet = {}, provMax = 1, curPts = [];
  function computeMap() {
    provNet = {};
    for (var si = 0; si < 16; si++) { var v = stVal(state.unit, state.idx, [si], types()); provNet[SIDO[si]] = { o: v[0], c: v[1], n: v[0] - v[1] }; }
    provMax = Math.max(1, d3.max(Object.keys(provNet), function (k) { return Math.abs(provNet[k].n); }));
  }
  function provColor(s) {
    var v = provNet[s]; if (!v || v.n === 0) return css("--land");
    var t = Math.min(1, Math.abs(v.n) / provMax);
    return d3.interpolateRgb(css("--land"), v.n > 0 ? css("--good") : css("--bad"))(0.12 + 0.5 * t);
  }
  function ptsInPeriod() {
    var sp = UNITS[state.unit].span(state.idx); if (sp[1] < PT0) return null;
    var out = [];
    PTS.forEach(function (p) {
      if (inPer(p.pd, sp)) out.push(Object.assign({}, p, { k: 1, d: p.pd, key: p.i + "o" }));
      if (inPer(p.cd, sp)) out.push(Object.assign({}, p, { k: 0, d: p.cd, key: p.i + "c" }));
    });
    return out;
  }
  function ptVisible(p) {
    return (p.k ? state.show.open : state.show.close) && (state.kind === "all" || String(p.k) === state.kind) && (state.type === "all" || String(p.t) === state.type);
  }
  function kindLabel(p) { return p.t === 1 ? (p.brand || "프랜차이즈") : TNAME[p.t]; }
  function links(p) {
    var q = ((LONG[p.sido] || p.sido) + " " + p.area + " " + p.name).replace(/\(.*?\)/g, " ").replace(/\s+/g, " ").trim(), e = encodeURIComponent;
    var L = [["네이버지도", "N", "https://map.naver.com/p/search/" + e(q)]];
    L.push(["카카오맵", "K", p.lat != null ? "https://map.kakao.com/link/map/" + e(p.name.replace(/,/g, " ")) + "," + p.lat + "," + p.lon : "https://map.kakao.com/?q=" + e(q)]);
    L.push(["구글지도", "G", "https://www.google.com/maps/search/?api=1&query=" + e(q)]);
    return L;
  }
  function showTip(box, tipEl, x, y, title, rows, sub) {
    tipEl.innerHTML = ""; tipEl.appendChild(el("div", "t", title)); if (sub) tipEl.appendChild(el("div", "hint", sub));
    rows.forEach(function (r) { var d = el("div"); d.appendChild(el("span", null, r[0] + " ")); d.appendChild(el("span", "n", r[1])); tipEl.appendChild(d); });
    var rc = box.getBoundingClientRect(); tipEl.style.opacity = 1;
    var lx = x - rc.left + 14, ly = y - rc.top + 14;
    if (lx + tipEl.offsetWidth > rc.width - 8) lx = x - rc.left - tipEl.offsetWidth - 14;
    if (ly + tipEl.offsetHeight > rc.height - 8) ly = y - rc.top - tipEl.offsetHeight - 14;
    tipEl.style.left = Math.max(4, lx) + "px"; tipEl.style.top = Math.max(4, ly) + "px";
  }
  function hideTip(tipEl) { tipEl.style.opacity = 0; }
  var mapTip = $("tip");
  function provRows(s) { var v = provNet[s]; return [["새로 연", fmt(v.o)], ["문 닫은", fmt(v.c)], ["순증", sgn(v.n)]]; }
  function perSub() { return UNITS[state.unit].label(state.idx) + (state.type === "all" ? "" : " · " + TNAME[+state.type]); }
  function sidoBounds(s) {
    if (s === "경북") return [[35.6, 128.0], [37.2, 129.6]];
    var a = 90, b = 180, c = -90, d = -180;
    function walk(x) { if (typeof x[0] === "number") { b = Math.min(b, x[0]); d = Math.max(d, x[0]); a = Math.min(a, x[1]); c = Math.max(c, x[1]); } else x.forEach(walk); }
    D.prov.features.forEach(function (f) { if (GEO[f.properties.name] === s) walk(f.geometry.coordinates); });
    return [[a, b], [c, d]];
  }

  var pop = $("pop");
  function showPop(p) {
    pop.innerHTML = "";
    var top = el("div", "pop-top"); top.appendChild(el("b", null, p.name));
    var x = el("button", "x", "×"); x.type = "button"; x.setAttribute("aria-label", "닫기"); x.onclick = function () { pop.hidden = true; }; top.appendChild(x);
    pop.appendChild(top);
    var st = p.k === 1 ? "새로 연 날 " + p.d.replace(/-/g, ".") : p.k === 0 ? "문 닫은 날 " + p.d.replace(/-/g, ".") : (p.tmp ? "단기 운영" : p.act ? "운영 중" : "폐업") + " · " + p.pd.replace(/-/g, ".") + " 개업";
    pop.appendChild(el("div", "hint", (LONG[p.sido] || p.sido) + " " + p.area));
    pop.appendChild(el("div", null, st + " · " + kindLabel(p)));
    var lk = el("div", "poplinks");
    links(p).forEach(function (l, k) { var a = el("a", k === 0 ? "nv" : null, l[0] + " ↗"); a.href = l[2]; a.target = "_blank"; a.rel = "noopener"; lk.appendChild(a); });
    pop.appendChild(lk);
    pop.hidden = false;
  }
  function focusPoint(p) {
    showPop(p);
    if (p.lat != null) MAP.toPoint(p.lat, p.lon, true);
    mapBox.scrollIntoView({ behavior: reduce() ? "auto" : "smooth", block: "nearest" });
  }

  // ---------- 그린 지도 (키 없이) ----------
  function makeDrawnMap() {
    var svg = d3.select("#drawMap"), svgEl = $("drawMap");
    var g = svg.append("g"), gProv = g.append("g"), gMuni = g.append("g"), gPt = g.append("g");
    var W = 400, H = 500, k = 1;
    var proj = d3.geoMercator(), path = d3.geoPath(proj);
    function fit() { W = svgEl.clientWidth || 400; H = svgEl.clientHeight || 500; svg.attr("viewBox", "0 0 " + W + " " + H); proj.fitExtent([[12, 12], [W - 12, H - 12]], { type: "MultiPoint", coordinates: [[124.6, 33.1], [130.0, 38.65]] }); }
    fit();
    var zoom = d3.zoom().scaleExtent([1, 60]).on("zoom", function (e) { g.attr("transform", e.transform); k = e.transform.k; restyle(); });
    svg.call(zoom).on("dblclick.zoom", null);
    function zoomTo(x0, y0, x1, y1, maxK) {
      var s = Math.min(maxK || 40, 0.85 / Math.max((x1 - x0) / W, (y1 - y0) / H));
      svg.transition().duration(reduce() ? 0 : 650).call(zoom.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(s).translate(-(x0 + x1) / 2, -(y0 + y1) / 2));
    }
    function restyle() {
      gPt.selectAll("circle").attr("r", function (p) { return (p.t === 3 ? 2 : 1) * (k > 6 ? 4.5 : 3) / Math.sqrt(k); })
        .attr("stroke-width", function (p) { return (p.t === 1 || p.t === 3 ? 1.8 : 0.8) / k; })
        .style("display", function (p) { return ptVisible(p) ? null : "none"; })
        .attr("opacity", function (p) { return (!state.sido || p.sido === state.sido) ? 0.95 : 0.2; });
      gProv.selectAll("path").attr("stroke-width", 1 / k).attr("fill-opacity", function (f) { return (!state.sido || GEO[f.properties.name] === state.sido) ? 1 : 0.5; });
      gMuni.selectAll("path").attr("stroke-width", 0.6 / k).style("display", k > 2.2 ? null : "none");
    }
    $("zIn").onclick = function () { svg.transition().duration(250).call(zoom.scaleBy, 1.6); };
    $("zOut").onclick = function () { svg.transition().duration(250).call(zoom.scaleBy, 1 / 1.6); };
    $("zReset").onclick = function () { setScope("", ""); };
    return {
      draw: function () {
        gProv.selectAll("path").data(D.prov.features).join("path").attr("class", "prov").attr("d", path)
          .attr("fill", function (f) { return provColor(GEO[f.properties.name]); })
          .on("click", function (e, f) { setScope(GEO[f.properties.name], ""); })
          .on("mousemove", function (e, f) { var s = GEO[f.properties.name]; showTip(mapBox, mapTip, e.clientX, e.clientY, LONG[s], provRows(s), perSub()); })
          .on("mouseleave", function () { hideTip(mapTip); });
        gMuni.selectAll("path").data(D.muni.features).join("path").attr("class", "muni").attr("d", path);
        gPt.selectAll("circle").data(curPts.filter(function (p) { return p.lat != null; }), function (p) { return p.key; }).join("circle").attr("class", "pt")
          .attr("cx", function (p) { return proj([p.lon, p.lat])[0]; }).attr("cy", function (p) { return proj([p.lon, p.lat])[1]; })
          .attr("fill", function (p) { return p.k ? css("--good") : css("--bad"); })
          .classed("fr", function (p) { return p.t === 1; }).classed("sn", function (p) { return p.t === 3; })
          .on("click", function (e, p) { e.stopPropagation(); focusPoint(p); })
          .on("mousemove", function (e, p) { showTip(mapBox, mapTip, e.clientX, e.clientY, p.name, [[p.k ? "새로 연 날" : "문 닫은 날", md(p.d)], ["유형", kindLabel(p)]]); })
          .on("mouseleave", function () { hideTip(mapTip); });
        restyle();
      },
      restyle: restyle,
      toScope: function () {
        if (state.area) { var a = AREA_BY[state.area]; if (a && a.lat != null) { this.toPoint(a.lat, a.lon, false); return; } }
        if (!state.sido) { svg.transition().duration(reduce() ? 0 : 500).call(zoom.transform, d3.zoomIdentity); return; }
        var bb = sidoBounds(state.sido), p0 = proj([bb[0][1], bb[0][0]]), p1 = proj([bb[1][1], bb[1][0]]);
        zoomTo(p0[0], p1[1], p1[0], p0[1]);
      },
      toPoint: function (lat, lon, close) { var q = proj([lon, lat]), r = close ? 4 : 14; zoomTo(q[0] - r, q[1] - r, q[0] + r, q[1] + r, close ? 45 : 22); },
      resize: function () { fit(); svg.call(zoom.transform, d3.zoomIdentity); }
    };
  }

  // ---------- 네이버 지도 ----------
  function makeNaverMap() {
    var N = naver.maps, box = $("naverMap");
    box.hidden = false; $("drawMap").style.display = "none"; $("zoombar").hidden = true;
    $("mapHint").textContent = "시·도를 누르면 그 지역으로, 점을 누르면 가게 정보";
    var KB = new N.LatLngBounds(new N.LatLng(33.0, 124.8), new N.LatLng(38.7, 130.0));
    var map = new N.Map(box, {
      center: new N.LatLng(36.2, 127.8), zoom: 7, minZoom: 6, scaleControl: true, logoControl: true, mapDataControl: false,
      mapTypeControl: true, mapTypeControlOptions: { style: N.MapTypeControlStyle.BUTTON, position: N.Position.TOP_LEFT },
      zoomControl: true, zoomControlOptions: { position: N.Position.TOP_RIGHT }
    });
    map.fitBounds(KB);
    var dataOk = true;
    try {
      map.data.addGeoJson(D.prov, false);
      map.data.addListener("click", function (e) { setScope(GEO[e.feature.getProperty("name")], ""); });
      map.data.addListener("mouseover", function (e) {
        var s = GEO[e.feature.getProperty("name")], o = e.offset || e.point, rc = box.getBoundingClientRect();
        if (o) showTip(mapBox, mapTip, rc.left + o.x, rc.top + o.y, LONG[s], provRows(s), perSub());
      });
      map.data.addListener("mouseout", function () { hideTip(mapTip); });
    } catch (err) { dataOk = false; }
    function style(f) {
      var s = GEO[f.getProperty("name")];
      return { fillColor: provColor(s), fillOpacity: (!state.sido || state.sido === s) ? 0.42 : 0.12, strokeColor: "#5C6A63", strokeOpacity: 0.6, strokeWeight: 1, clickable: true };
    }
    var markers = [];
    function icon(p) {
      var s = p.t === 3 ? 16 : 11, bc = p.t === 1 ? "#18221E" : p.t === 3 ? "#F0B429" : "#fff", bw = p.t === 3 ? 3 : 2;
      return { content: '<div style="width:' + s + "px;height:" + s + "px;border-radius:50%;box-sizing:border-box;border:" + bw + "px solid " + bc + ";background:" + (p.k ? "#1F7A4D" : "#B3362B") + ';box-shadow:0 0 2px rgba(0,0,0,.55);cursor:pointer"></div>', anchor: new N.Point(s / 2, s / 2) };
    }
    function restyle() {
      if (dataOk) map.data.setStyle(style);
      markers.forEach(function (m) { m.setVisible(ptVisible(m.__p)); });
    }
    return {
      draw: function () {
        markers.forEach(function (m) { m.setMap(null); });
        markers = curPts.filter(function (p) { return p.lat != null; }).map(function (p) {
          var m = new N.Marker({ map: map, position: new N.LatLng(p.lat, p.lon), title: p.name, icon: icon(p), zIndex: p.t === 3 ? 30 : p.t === 1 ? 20 : 10 });
          m.__p = p;
          N.Event.addListener(m, "click", function () { showPop(p); });
          return m;
        });
        restyle();
      },
      restyle: restyle,
      toScope: function () {
        if (state.area) { var a = AREA_BY[state.area]; if (a && a.lat != null) { map.morph(new N.LatLng(a.lat, a.lon), 12); return; } }
        if (!state.sido) { map.fitBounds(KB); return; }
        var bb = sidoBounds(state.sido); map.fitBounds(new N.LatLngBounds(new N.LatLng(bb[0][0], bb[0][1]), new N.LatLng(bb[1][0], bb[1][1])));
      },
      toPoint: function (lat, lon, close) { map.morph(new N.LatLng(lat, lon), close ? 17 : 12); },
      resize: function () { N.Event.trigger(map, "resize"); }
    };
  }

  // ---------- 리포트 ----------
  function setDelta(id, cur, prev, goodUp, label) {
    var e = $(id);
    if (prev == null) { e.textContent = label || ""; e.className = "c hint"; return; }
    var d = cur - prev; e.textContent = "이전 " + UNITS[state.unit].name + "보다 " + sgn(d);
    e.className = "c " + (d === 0 ? "flat" : (d > 0) === goodUp ? "up" : "down");
  }
  function stockFor(ts) {
    if (state.area) return AREA_BY[state.area].s;
    return scopeSidos().reduce(function (s, si) { return s + ts.reduce(function (x, t) { return x + D.stock[si][t]; }, 0); }, 0);
  }
  function renderReport() {
    var u = state.unit, i = state.idx, U = UNITS[u], partial = isPartial(u, i);
    $("placeSub").textContent = U.label(i) + (partial ? " · " + md(MAXD) + "까지 집계" : "") + (state.type !== "all" && !state.area ? " · " + TNAME[+state.type] : "");
    $("placeName").textContent = scopeName();
    var v = scopeVal(u, i), pv = i > 0 && !partial ? scopeVal(u, i - 1) : null;
    $("kOpen").textContent = fmt(v[0]); $("kClose").textContent = fmt(v[1]);
    var n = v[0] - v[1]; $("kNet").textContent = sgn(n); $("kNet").className = "v num " + (n > 0 ? "good" : n < 0 ? "bad" : "");
    setDelta("kOpenC", v[0], pv && pv[0], true, partial ? "진행 중인 " + U.name : "");
    setDelta("kCloseC", v[1], pv && pv[1], false, partial ? "진행 중인 " + U.name : "");
    setDelta("kNetC", n, pv && pv[0] - pv[1], true, "");
    var stock = stockFor(types());
    $("kStock").textContent = fmt(stock);
    $("kStockC").textContent = state.area ? "모든 유형 · 현재 기준" : state.type === "all" ? "현재 기준" : "전체 " + fmt(stockFor([0, 1, 2, 3])) + "곳 중 " + pct(stock / Math.max(1, stockFor([0, 1, 2, 3])));
    renderSummary(v, pv);
    renderMix();
  }
  function renderSummary(v, pv) {
    var u = state.unit, i = state.idx, U = UNITS[u], n = v[0] - v[1];
    $("sumEyebrow").textContent = "요약 · " + U.label(i);
    $("sumTitle").textContent = v[0] + v[1] === 0 ? "이 기간에는 신고된 개업·폐업이 없습니다."
      : n > 0 ? scopeName() + "에서 문 연 카페가 닫은 곳보다 " + fmt(n) + "곳 많았습니다."
      : n < 0 ? scopeName() + "에서 문 닫은 카페가 연 곳보다 " + fmt(-n) + "곳 많았습니다."
      : scopeName() + "에서는 연 만큼 닫았습니다.";
    var tags = $("sumTags"); tags.innerHTML = "";
    function tag(t, c) { tags.appendChild(el("span", "tag " + (c || ""), t)); }
    if (n > 0) tag("늘어나는 중", "good"); else if (n < 0) tag("줄어드는 중", "bad"); else tag("제자리");
    if (!state.area) {
      var sids = scopeSidos(), fr = stVal(u, i, sids, [1]), all = stVal(u, i, sids, [0, 1, 2, 3]);
      if (all[0] > 0) tag("새로 연 곳 중 프랜차이즈 " + pct(fr[0] / all[0]), "roast");
    }
    if (isPartial(u, i)) tag("진행 중인 " + U.name);
    var pts = $("sumPoints"); pts.innerHTML = "";
    function li(t) { pts.appendChild(el("li", null, t)); }
    if (pv) {
      var d = v[0] - pv[0];
      li("이전 " + U.name + "(" + U.label(i - 1) + ")보다 새로 연 곳이 " + (d === 0 ? "같았습니다" : fmt(Math.abs(d)) + "곳 " + (d > 0 ? "많았습니다" : "적었습니다")) + ". 문 닫은 곳은 " + fmt(pv[1]) + " → " + fmt(v[1]) + "곳.");
    }
    var j = i - U.yoy;
    if (u !== "y" && j >= 0 && !isPartial(u, i)) {
      var yv = scopeVal(u, j);
      li("작년 같은 " + U.name + "(" + U.label(j) + ")에는 " + fmt(yv[0]) + "곳이 열고 " + fmt(yv[1]) + "곳이 닫았습니다(순증 " + sgn(yv[0] - yv[1]) + ").");
    }
    if (!state.area) {
      var rows = AREAS.filter(function (a) { return !state.sido || a.sido === state.sido; }).map(function (a) { var x = areaVal(a, u, i); return { a: a, n: x[0] - x[1] }; });
      var lo = d3.least(rows, function (r) { return r.n; }), hi = d3.greatest(rows, function (r) { return r.n; });
      if (lo && lo.n < 0) li("가장 많이 줄어든 곳은 " + lo.a.name + "(" + sgn(lo.n) + "), 가장 많이 늘어난 곳은 " + (hi && hi.n > 0 ? hi.a.name + "(" + sgn(hi.n) + ")" : "없습니다") + ".");
      else if (hi && hi.n > 0) li("가장 많이 늘어난 곳은 " + hi.a.name + "(" + sgn(hi.n) + ")입니다.");
    }
    if (!state.sido) {
      var bs = BRANDS.map(function (b) { var x = brandVal(b, u, i); return { b: b, o: x[0], c: x[1] }; });
      var bo = d3.greatest(bs, function (r) { return r.o; }), bc = d3.greatest(bs, function (r) { return r.c; });
      if (bo && bo.o > 0) li("가장 많이 연 브랜드는 " + bo.b.name + "(" + fmt(bo.o) + "곳)" + (bc && bc.c > 0 ? ", 가장 많이 닫은 브랜드는 " + bc.b.name + "(" + fmt(bc.c) + "곳)" : "") + "입니다.");
    }
  }
  function renderMix() {
    var u = state.unit, i = state.idx, sids = scopeSidos(), body = $("mixBody"); body.innerHTML = "";
    [1, 2, 0, 3].forEach(function (t) {
      var v = stVal(u, i, sids, [t]), s = sids.reduce(function (x, si) { return x + D.stock[si][t]; }, 0), n = v[0] - v[1];
      var tr = el("tr"); if (state.type === String(t)) tr.className = "me";
      tr.appendChild(el("td", null, TNAME[t]));
      [[fmt(v[0])], [fmt(v[1])], [sgn(n), n > 0 ? "good" : n < 0 ? "bad" : ""], [fmt(s)]].forEach(function (c) { tr.appendChild(el("td", "r " + (c[1] || ""), c[0])); });
      body.appendChild(tr);
    });
    $("mixNote").textContent = state.area ? "유형별 표는 " + LONG[state.sido] + " 전체 기준입니다." : "영업 중은 현재 기준입니다.";
  }

  // ---------- 추이 ----------
  var trendTip = $("trendTip");
  function renderTrend() {
    var u = state.unit, U = UNITS[u], svgEl = $("trend"), box = svgEl.parentNode;
    var last = maxIdx(u), first = Math.max(0, last - SHOW[u] + 1);
    var rows = d3.range(first, last + 1).map(function (i) { var v = scopeVal(u, i); return { i: i, o: v[0], c: v[1], n: v[0] - v[1], partial: isPartial(u, i) }; });
    var unitName = { w: "주별", m: "월별", q: "분기별", y: "연별" }[u];
    $("trendTitle").textContent = unitName + " 추이 · " + scopeName() + (state.type !== "all" && !state.area ? " · " + TNAME[+state.type] : "");
    var done = rows.filter(function (r) { return !r.partial; }), tO = d3.sum(done, function (r) { return r.o; }), tC = d3.sum(done, function (r) { return r.c; });
    $("trendSub").textContent = U.label(first) + " ~ " + U.label(last) + " · 끝난 기간 합계 새로 연 곳 " + fmt(tO) + " · 문 닫은 곳 " + fmt(tC) + " · 순증 " + sgn(tO - tC);
    var sv = d3.select(svgEl); sv.selectAll("*").remove();
    var w = svgEl.clientWidth || 700, h = svgEl.clientHeight || 260; sv.attr("viewBox", "0 0 " + w + " " + h);
    var m = Math.max(1, d3.max(rows, function (r) { return Math.max(r.o, r.c); }));
    var y = d3.scaleLinear([-m, m], [h - 24, 10]).nice();
    var probe = sv.append("text").attr("font-size", 11).attr("font-family", css("--font-data")).text(fmt(Math.round(y.domain()[1])));
    var ml = Math.ceil(probe.node().getComputedTextLength()) + 10; probe.remove();
    var x = d3.scaleBand(rows.map(function (r) { return r.i; }), [ml, w - 4]).paddingInner(rows.length > 40 ? 0.15 : 0.25);
    var bw = Math.min(26, x.bandwidth()), off = (x.bandwidth() - bw) / 2, step = x.step(), pad = step * x.paddingInner() / 2;
    var tk = y.ticks(4);
    sv.append("g").selectAll("line").data(tk).join("line").attr("x1", ml).attr("x2", w - 4).attr("y1", y).attr("y2", y).attr("stroke", function (t) { return t === 0 ? css("--ink") : css("--line"); }).attr("stroke-opacity", function (t) { return t === 0 ? 0.6 : 1; });
    sv.append("g").selectAll("text").data(tk).join("text").attr("x", ml - 6).attr("y", y).attr("dy", ".32em").attr("text-anchor", "end").attr("font-size", 11).attr("font-family", css("--font-data")).attr("fill", css("--muted")).text(function (t) { return fmt(Math.abs(t)); });
    var selR = rows.find(function (r) { return r.i === state.idx; });
    if (selR) sv.append("rect").attr("x", x(selR.i) - pad).attr("width", step).attr("y", 4).attr("height", h - 22).attr("rx", 4).attr("fill", css("--signal-soft"));
    var probe2 = sv.append("text").attr("font-size", 11).text(U.short(last)); var lw = probe2.node().getComputedTextLength() + 8; probe2.remove();
    var every = Math.max(1, Math.ceil(lw / step));
    sv.append("g").selectAll("text").data(rows.filter(function (r, j) { return (rows.length - 1 - j) % every === 0; })).join("text")
      .attr("x", function (r) { return x(r.i) + x.bandwidth() / 2; }).attr("y", h - 6).attr("text-anchor", "middle").attr("font-size", 11)
      .attr("fill", function (r) { return r.i === state.idx ? css("--ink") : css("--muted"); }).attr("font-weight", function (r) { return r.i === state.idx ? 700 : 400; })
      .text(function (r) { return U.short(r.i); });
    var gg = sv.append("g").selectAll("g").data(rows).join("g").attr("opacity", function (r) { return r.partial ? 0.4 : 1; });
    var rx = Math.min(3, bw / 2);
    gg.append("rect").attr("x", function (r) { return x(r.i) + off; }).attr("width", bw).attr("y", function (r) { return y(r.o); }).attr("height", function (r) { return Math.max(0, y(0) - y(r.o)); }).attr("rx", rx).attr("fill", css("--good"));
    gg.append("rect").attr("x", function (r) { return x(r.i) + off; }).attr("width", bw).attr("y", y(0)).attr("height", function (r) { return Math.max(0, y(-r.c) - y(0)); }).attr("rx", rx).attr("fill", css("--bad"));
    gg.append("circle").attr("cx", function (r) { return x(r.i) + x.bandwidth() / 2; }).attr("cy", function (r) { return y(r.n); }).attr("r", Math.min(3.5, Math.max(1.5, bw / 3))).attr("fill", css("--ink")).attr("stroke", css("--sheet"));
    sv.append("g").selectAll("rect").data(rows).join("rect").attr("x", function (r) { return x(r.i) - pad; }).attr("width", step).attr("y", 0).attr("height", h).attr("fill", "transparent").style("cursor", "pointer")
      .on("mousemove", function (e, r) { showTip(box, trendTip, e.clientX, e.clientY, U.label(r.i) + (r.partial ? " (진행 중)" : ""), [["새로 연", fmt(r.o)], ["문 닫은", fmt(r.c)], ["순증", sgn(r.n)]]); })
      .on("mouseleave", function () { hideTip(trendTip); })
      .on("click", function (e, r) { setIdx(r.i); });
  }

  // ---------- 목록·표 ----------
  function nameCell(p) {
    var td = el("td"); td.appendChild(document.createTextNode(p.name));
    var ml = el("span", "minilinks");
    links(p).forEach(function (l) { var a = el("a", null, l[1]); a.href = l[2]; a.target = "_blank"; a.rel = "noopener"; a.title = l[0]; a.onclick = function (e) { e.stopPropagation(); }; ml.appendChild(a); });
    td.appendChild(ml); return td;
  }
  function renderList() {
    var body = $("listBody"); body.innerHTML = "";
    var sp = UNITS[state.unit].span(state.idx);
    if (sp[1] < PT0) {
      $("listCount").textContent = "";
      $("listNote").textContent = "가게 목록은 " + PT0_TXT + " 이후 기간에서 볼 수 있습니다. 기간을 최근으로 바꿔 보세요.";
      return;
    }
    var rs = curPts.filter(function (p) {
      return (!state.sido || p.sido === state.sido) && (!state.area || (p.sido + " " + p.area) === state.area) && (state.kind === "all" || String(p.k) === state.kind) &&
        (state.type === "all" || String(p.t) === state.type) && (!state.q || p.name.toLowerCase().indexOf(state.q) >= 0);
    }).sort(function (a, b) { return b.d.localeCompare(a.d) || a.name.localeCompare(b.name, "ko"); });
    var nO = rs.filter(function (p) { return p.k; }).length;
    $("listCount").textContent = fmt(rs.length) + "곳 · 새로 연 곳 " + fmt(nO) + " · 문 닫은 곳 " + fmt(rs.length - nO);
    var frag = document.createDocumentFragment();
    rs.slice(0, 500).forEach(function (p) {
      var tr = el("tr", "clickable"); tr.appendChild(nameCell(p));
      var b = el("td"); b.appendChild(el("span", "badge " + (p.k ? "o" : "c"), p.k ? "새로 연" : "문 닫은")); tr.appendChild(b);
      var k = el("td"); k.appendChild(el("span", "kindtxt" + (p.t === 1 ? " fr" : p.t === 3 ? " sn" : ""), kindLabel(p))); tr.appendChild(k);
      tr.appendChild(el("td", null, p.sido + " " + p.area));
      tr.appendChild(el("td", "r", md(p.d)));
      tr.onclick = function () { focusPoint(p); };
      frag.appendChild(tr);
    });
    body.appendChild(frag);
    $("listNote").textContent = rs.length > 500 ? "최근 500곳만 보여 줍니다. 지역을 좁히거나 상호로 찾아보세요." : rs.length ? "" : "조건에 맞는 가게가 없습니다.";
  }
  $("areaSort").onchange = renderAreas; $("areaQ").oninput = renderAreas;
  function renderAreas() {
    var u = state.unit, i = state.idx, q = $("areaQ").value.trim(), sort = $("areaSort").value;
    $("areaTitle").textContent = "시·군·구 순위 · " + UNITS[u].label(i);
    var rs = AREAS.filter(function (a) { return (!state.sido || a.sido === state.sido) && (!q || a.name.indexOf(q) >= 0); })
      .map(function (a) { var v = areaVal(a, u, i); return { a: a, o: v[0], c: v[1], n: v[0] - v[1] }; })
      .filter(function (r) { return r.o + r.c > 0 || q || sort === "stock"; });
    var by = { netAsc: function (x, y) { return x.n - y.n; }, netDesc: function (x, y) { return y.n - x.n; }, open: function (x, y) { return y.o - x.o; }, close: function (x, y) { return y.c - x.c; }, stock: function (x, y) { return y.a.s - x.a.s; } }[sort];
    rs.sort(function (x, y) { return by(x, y) || x.a.name.localeCompare(y.a.name, "ko"); });
    var body = $("areaBody"); body.innerHTML = ""; var frag = document.createDocumentFragment();
    rs.forEach(function (r) {
      var tr = el("tr", "clickable" + (r.a.name === state.area ? " me" : ""));
      tr.appendChild(el("td", null, state.sido ? r.a.short : r.a.name));
      [[fmt(r.o)], [fmt(r.c)], [sgn(r.n), r.n > 0 ? "good" : r.n < 0 ? "bad" : ""], [fmt(r.a.s)]].forEach(function (c) { tr.appendChild(el("td", "r " + (c[1] || ""), c[0])); });
      tr.onclick = function () { setScope(r.a.sido, r.a.name); window.scrollTo({ top: 0, behavior: reduce() ? "auto" : "smooth" }); };
      frag.appendChild(tr);
    });
    body.appendChild(frag);
  }
  $("brandSort").onchange = renderBrands;
  function renderBrands() {
    var u = state.unit, i = state.idx, six = state.sido ? SI[state.sido] : -1, sort = $("brandSort").value;
    $("brandTitle").textContent = "프랜차이즈 브랜드 · " + UNITS[u].label(i);
    $("brandStockTh").textContent = state.sido ? "총매장수 (" + state.sido + ")" : "총매장수";
    $("brandNote").textContent = "총매장수는 지금 영업 중인 매장" + (state.sido ? "(" + LONG[state.sido] + ")" : "(전국)") + "입니다. 새로 연·문 닫은 숫자는 선택한 기간의 전국 기준입니다. 본사 발표 매장 수와는 조금 다를 수 있습니다.";
    var rs = BRANDS.map(function (b) { var v = brandVal(b, u, i); return { b: b, s: six >= 0 ? b.ss[six] : b.s, o: v[0], c: v[1], n: v[0] - v[1] }; })
      .filter(function (r) { return r.s > 0 || r.o + r.c > 0; });
    var by = { stock: function (x, y) { return y.s - x.s; }, open: function (x, y) { return y.o - x.o; }, close: function (x, y) { return y.c - x.c; }, net: function (x, y) { return y.n - x.n; } }[sort];
    rs.sort(function (x, y) { return by(x, y) || y.s - x.s; });
    var mx = d3.max(rs, function (r) { return r.s; }) || 1, body = $("brandBody"); body.innerHTML = "";
    rs.forEach(function (r) {
      var tr = el("tr"); tr.appendChild(el("td", null, r.b.name));
      var sc = el("td", "r"); var bar = el("span", "sbar"); bar.style.width = Math.round(70 * r.s / mx) + "px"; sc.appendChild(bar); sc.appendChild(document.createTextNode(fmt(r.s))); tr.appendChild(sc);
      [[fmt(r.o)], [fmt(r.c)], [sgn(r.n), r.n > 0 ? "good" : r.n < 0 ? "bad" : ""]].forEach(function (c) { tr.appendChild(el("td", "r " + (c[1] || ""), c[0])); });
      body.appendChild(tr);
    });
  }
  function renderSenior() {
    var scope = SEN.filter(function (s) { return (!state.sido || s.sido === state.sido) && (!state.area || (s.sido + " " + s.area) === state.area); });
    var real = scope.filter(function (s) { return !s.tmp; }), act = real.filter(function (s) { return s.act; });
    var y = MAXD.slice(0, 4), y1 = String(+y - 1);
    var k = $("senKpis"); k.innerHTML = "";
    [["지금 운영 중", act.length], [y + "년 새로 연", real.filter(function (s) { return s.pd.slice(0, 4) === y; }).length], [y1 + "년 새로 연", real.filter(function (s) { return s.pd.slice(0, 4) === y1; }).length], ["지금까지 문 닫은", real.length - act.length]].forEach(function (x) {
      var d = el("div", "kpi"); d.appendChild(el("span", "k", x[0])); var v = el("span", "v num", fmt(x[1])); d.appendChild(v); k.appendChild(d);
    });
    var rs = scope.filter(function (s) { return state.sen === "all" || (state.sen === "t" ? s.tmp : !s.tmp && String(s.act) === state.sen); })
      .sort(function (a, b) { return b.pd.localeCompare(a.pd); });
    var body = $("senBody"); body.innerHTML = "";
    if (!rs.length) { var tr0 = el("tr"); var td0 = el("td", "hint", "해당하는 카페가 없습니다."); td0.colSpan = 5; tr0.appendChild(td0); body.appendChild(tr0); return; }
    rs.forEach(function (s) {
      var tr = el("tr", "clickable"); tr.appendChild(nameCell(s));
      var b = el("td"); b.appendChild(el("span", "badge " + (s.tmp ? "x" : s.act ? "o" : "c"), s.tmp ? "단기 운영" : s.act ? "운영 중" : "폐업")); tr.appendChild(b);
      tr.appendChild(el("td", null, s.sido + " " + s.area));
      tr.appendChild(el("td", "r", s.pd.replace(/-/g, ".")));
      tr.appendChild(el("td", "r", s.cd ? s.cd.replace(/-/g, ".") : "–"));
      tr.onclick = function () { focusPoint(s); };
      body.appendChild(tr);
    });
  }

  // ---------- 전체 흐름 ----------
  var MAP = null;
  function drawMap() {
    computeMap();
    var pp = ptsInPeriod(); curPts = pp || [];
    var note = $("mapNote"); note.hidden = !!pp;
    if (!pp) note.textContent = "가게 점은 " + PT0_TXT + " 이후 기간에만 있습니다. 지금은 시·도 색만 보입니다.";
    MAP.draw();
  }
  function render() {
    drawMap(); renderReport(); renderTrend(); renderList(); renderAreas(); renderBrands();
    $("prevBtn").disabled = state.idx <= 0; $("nextBtn").disabled = state.idx >= maxIdx(state.unit);
    writeHash();
  }
  function setScope(sido, area) {
    state.sido = sido || ""; state.area = area || "";
    sidoSel.value = state.sido; fillSgg(); sggSel.value = state.area; markQuick();
    pop.hidden = true;
    MAP.toScope(); MAP.restyle();
    renderReport(); renderTrend(); renderList(); renderAreas(); renderBrands(); renderSenior();
    writeHash();
  }

  var inited = false, drawnMade = null;
  function resetMap() { MAP = null; var b = $("naverMap"); b.innerHTML = ""; b.hidden = true; $("drawMap").style.display = ""; $("zoombar").hidden = false; }
  function start(useNaver) {
    if (MAP) return;
    try { MAP = useNaver ? makeNaverMap() : (drawnMade = drawnMade || makeDrawnMap()); }
    catch (e) { resetMap(); MAP = drawnMade = drawnMade || makeDrawnMap(); }
    $("rampSw").style.background = "linear-gradient(90deg," + css("--bad") + "," + css("--land") + "," + css("--good") + ")";
    if (!inited) { readHash(); }
    pressed("unitSeg", "u", state.unit);
    sidoSel.value = state.sido; fillSgg(); sggSel.value = state.area; markQuick();
    fillPeriods(); render(); renderSenior();
    if (state.sido || state.area) MAP.toScope();
    if (inited) return;
    inited = true;
    var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { MAP.resize(); render(); }, 200); });
    var rethemed = function () { $("rampSw").style.background = "linear-gradient(90deg," + css("--bad") + "," + css("--land") + "," + css("--good") + ")"; render(); };
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", rethemed);
  }

  // 네이버 지도 키가 있으면 네이버 지도, 없거나 인증에 실패하면 그린 지도
  var cfg = window.OC_CONFIG || {};
  if (!cfg.NAVER_CLIENT_ID) { start(false); return; }
  var tried = false;
  function fallbackNote(why) {
    var n = $("mapNote"); n.hidden = false; n.innerHTML = "";
    n.appendChild(document.createTextNode("네이버 지도를 " + why + " 대신 기본 지도로 보여 드립니다. "));
    var a = el("a", null, "다시 불러오기"); a.href = location.href; a.onclick = function (e) { e.preventDefault(); location.reload(); }; n.appendChild(a);
  }
  function upgradeToNaver() {
    // 기본 지도로 먼저 띄웠는데 네이버 지도가 늦게 도착한 경우
    if (MAP && MAP === drawnMade) { MAP = null; $("drawMap").style.display = "none"; $("mapNote").hidden = true; }
    start(true);
  }
  function loadNaver(param) {
    var s = document.createElement("script"), done = false;
    window.navermap_authFailure = function () {
      if (done) return; done = true;
      if (MAP && MAP !== drawnMade) resetMap();
      if (param === "ncpKeyId" && !tried) { tried = true; loadNaver("ncpClientId"); return; }
      start(false); fallbackNote("인증하지 못해");
    };
    s.src = "https://oapi.map.naver.com/openapi/v3/maps.js?" + param + "=" + encodeURIComponent(cfg.NAVER_CLIENT_ID);
    s.onload = function () { if (!done && window.naver && naver.maps) upgradeToNaver(); };
    s.onerror = function () { if (!MAP) { start(false); fallbackNote("불러오지 못해(네트워크나 광고 차단 확인)"); } };
    document.head.appendChild(s);
  }
  loadNaver("ncpKeyId");
  setTimeout(function () { if (!MAP) { start(false); fallbackNote("불러오는 데 오래 걸려"); } }, 15000);
})();
