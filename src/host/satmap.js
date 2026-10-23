(function () {
  "use strict";
  var el = document.getElementById("satMap");
  if (!el) return;
  var cfg = window.OC_CONFIG || {};
  function css(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function colorOf(c) { if (c.t === "f") return css("--food") || "#3A63A8"; return c.t === "c" ? (c.b >= 0 ? css("--roast") : css("--signal")) : c.k === 0 ? css("--amber") : css("--berry"); }
  function zoomFor(r) { return r >= 1000 ? 15 : r >= 500 ? 16 : 17; }
  function popup(c) {
    var links = (window.OC_links ? window.OC_links(c) : []).map(function (l) {
      return '<a href="' + esc(l[3]) + '" target="_blank" rel="noopener">' + esc(l[0]) + "</a>";
    }).join(" · ");
    return "<b>" + esc(c.name) + "</b><br>" + esc(window.OC_kind ? window.OC_kind(c) : "") + " · " + Math.round(c.m) + "m" +
      (c.fl ? " · " + esc(c.fl === "지" ? "지하" : c.fl + "층") : "") + (c.addr ? "<br>" + esc(c.addr) : "") + "<br>" + links;
  }
  var lastKey = "";
  function foodsFor(state, foods) { return state.showFood && foods ? foods.filter(function (c) { return c.m <= state.r * 1.1; }).slice(0, 1500) : []; }

  /* ---------- 카카오 지도 (스카이뷰) ---------- */
  function startKakao() {
    var s = document.createElement("script");
    s.src = "https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=" + encodeURIComponent(cfg.KAKAO_JS_KEY);
    s.onerror = startLeaflet;
    s.onload = function () {
      kakao.maps.load(function () {
        var map = new kakao.maps.Map(el, { center: new kakao.maps.LatLng(37.5665, 126.978), level: 3 });
        map.setMapTypeId(kakao.maps.MapTypeId.HYBRID);
        map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
        var objs = [], info = new kakao.maps.CustomOverlay({ yAnchor: 1.15, zIndex: 10 });
        kakao.maps.event.addListener(map, "click", function (e) { info.setMap(null); window.OC_pickAt && window.OC_pickAt(e.latLng.getLat(), e.latLng.getLng()); });
        window.OCMAP = {
          ready: true,
          focus: function (c) {
            var pos = new kakao.maps.LatLng(c.la, c.lo); map.setLevel(1); map.setCenter(pos);
            var box = document.createElement("div");
            box.style.cssText = "background:#fff;color:#111;font:13px/1.5 sans-serif;padding:8px 10px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:240px";
            box.innerHTML = popup(c); info.setContent(box); info.setPosition(pos); info.setMap(map);
          },
          draw: function (state, cafes, sweets, stations, foods) {
            objs.forEach(function (o) { o.setMap(null); }); objs = []; info.setMap(null);
            var center = new kakao.maps.LatLng(state.lat, state.lon);
            var key = state.lat.toFixed(5) + state.lon.toFixed(5) + state.r;
            if (key !== lastKey) { map.setCenter(center); map.setLevel(state.r >= 1000 ? 5 : state.r >= 500 ? 4 : 3); lastKey = key; }
            var circle = new kakao.maps.Circle({ center: center, radius: state.r, strokeWeight: 2, strokeColor: "#ffffff", strokeStyle: "dash", fillColor: "#ffffff", fillOpacity: 0.08 });
            circle.setMap(map); objs.push(circle);
            foodsFor(state, foods).concat(cafes, sweets).forEach(function (c) {
              var d = document.createElement("div");
              d.style.cssText = (c.t === "f" ? "width:7px;height:7px;border:1px solid #fff;" : "width:11px;height:11px;border:2px solid #fff;") + "cursor:pointer;box-shadow:0 0 2px rgba(0,0,0,.6);background:" + colorOf(c) + ";border-radius:" + (c.t === "c" ? "50%" : "2px") + ";opacity:" + (c.m <= state.r ? 1 : 0.5);
              d.title = c.name;
              d.addEventListener("click", function (ev) {
                ev.stopPropagation();
                var box = document.createElement("div");
                box.style.cssText = "background:#fff;color:#111;font:13px/1.5 sans-serif;padding:8px 10px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:240px";
                box.innerHTML = popup(c);
                info.setContent(box); info.setPosition(new kakao.maps.LatLng(c.la, c.lo)); info.setMap(map);
              });
              var ov = new kakao.maps.CustomOverlay({ position: new kakao.maps.LatLng(c.la, c.lo), content: d, yAnchor: 0.5, xAnchor: 0.5 });
              ov.setMap(map); objs.push(ov);
            });
            var cm = document.createElement("div"); cm.style.cssText = "width:16px;height:16px;border:3px solid #fff;border-radius:50%;background:#111;box-shadow:0 0 3px rgba(0,0,0,.7)";
            var co = new kakao.maps.CustomOverlay({ position: center, content: cm, yAnchor: 0.5, xAnchor: 0.5, zIndex: 5 }); co.setMap(map); objs.push(co);
          }
        };
        hideCanvas(); window.OC_redraw && window.OC_redraw();
      });
    };
    document.head.appendChild(s);
  }

  /* ---------- 네이버 지도 ---------- */
  function startNaver(param) {
    var s = document.createElement("script"), failed = false;
    window.navermap_authFailure = function () {
      if (failed) return; failed = true;
      if (param === "ncpKeyId") { el.innerHTML = ""; startNaver("ncpClientId"); } else { el.innerHTML = ""; startLeaflet(); }
    };
    s.src = "https://oapi.map.naver.com/openapi/v3/maps.js?" + param + "=" + encodeURIComponent(cfg.NAVER_CLIENT_ID);
    s.onerror = function () { startLeaflet(); };
    s.onload = function () {
      if (failed || !window.naver || !naver.maps) return;
      var map = new naver.maps.Map(el, {
        center: new naver.maps.LatLng(37.5665, 126.978), zoom: 16,
        mapTypeControl: true, mapTypeControlOptions: { style: naver.maps.MapTypeControlStyle.BUTTON, position: naver.maps.Position.TOP_LEFT },
        zoomControl: true, zoomControlOptions: { position: naver.maps.Position.TOP_RIGHT }, scaleControl: true, logoControl: true, mapDataControl: true
      });
      var objs = [], info = new naver.maps.InfoWindow({ borderWidth: 0, backgroundColor: "transparent", disableAnchor: true, pixelOffset: new naver.maps.Point(0, -8) });
      naver.maps.Event.addListener(map, "click", function (e) { info.close(); window.OC_pickAt && window.OC_pickAt(e.coord.lat(), e.coord.lng()); });
      window.OCMAP = {
        ready: true,
        focus: function (c) {
          var pos = new naver.maps.LatLng(c.la, c.lo); map.setCenter(pos); map.setZoom(19);
          info.setContent('<div style="background:#fff;color:#111;font:13px/1.5 sans-serif;padding:8px 10px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:240px">' + popup(c) + "</div>");
          info.open(map, pos);
        },
        draw: function (state, cafes, sweets, stations, foods) {
          objs.forEach(function (o) { o.setMap(null); }); objs = []; info.close();
          var center = new naver.maps.LatLng(state.lat, state.lon);
          var key = state.lat.toFixed(5) + state.lon.toFixed(5) + state.r;
          if (key !== lastKey) { map.setCenter(center); map.setZoom(zoomFor(state.r)); lastKey = key; }
          objs.push(new naver.maps.Circle({ map: map, center: center, radius: state.r, strokeColor: css("--signal") || "#0E6B5C", strokeWeight: 2, strokeStyle: "shortdash", fillColor: css("--signal") || "#0E6B5C", fillOpacity: 0.08, clickable: false }));
          foodsFor(state, foods).concat(cafes, sweets).forEach(function (c) {
            var round = c.t === "b" ? "2px" : "50%", op = c.m <= state.r ? 1 : 0.5, sz = c.t === "f" ? 7 : 12, bw = c.t === "f" ? 1 : 2;
            var mk = new naver.maps.Marker({
              map: map, position: new naver.maps.LatLng(c.la, c.lo), title: c.name, zIndex: c.t === "f" ? 1 : c.t === "c" && c.b >= 0 ? 3 : 2,
              icon: { content: '<div style="width:' + sz + 'px;height:' + sz + 'px;border:' + bw + 'px solid #fff;box-shadow:0 0 2px rgba(0,0,0,.55);border-radius:' + round + ';opacity:' + op + ';background:' + colorOf(c) + '"></div>', anchor: new naver.maps.Point(sz / 2 + bw, sz / 2 + bw) }
            });
            naver.maps.Event.addListener(mk, "click", function () {
              info.setContent('<div style="background:#fff;color:#111;font:13px/1.5 sans-serif;padding:8px 10px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:240px">' + popup(c) + "</div>");
              info.open(map, mk);
            });
            objs.push(mk);
          });
          objs.push(new naver.maps.Marker({ map: map, position: center, clickable: false, zIndex: 9,
            icon: { content: '<div style="width:18px;height:18px;border:3px solid #fff;border-radius:50%;background:#111;box-shadow:0 0 3px rgba(0,0,0,.7)"></div>', anchor: new naver.maps.Point(9, 9) } }));
        }
      };
      hideCanvas(); window.OC_redraw && window.OC_redraw();
    };
    document.head.appendChild(s);
  }

  /* ---------- Leaflet + 위성사진 (키 없이) ---------- */
  function startLeaflet() {
    if (!window.L) { el.style.display = "none"; return; }
    var map = L.map(el, { zoomControl: true, attributionControl: true }).setView([37.5665, 126.978], 16);
    var esri = "https://server.arcgisonline.com/ArcGIS/rest/services/";
    var sat = L.layerGroup([
      L.tileLayer(esri + "World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Tiles &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics" }),
      L.tileLayer(esri + "Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, opacity: 0.8 }),
      L.tileLayer(esri + "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19 })
    ]);
    var street = L.tileLayer(esri + "World_Street_Map/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Tiles &copy; Esri" });
    (cfg.START_SATELLITE === false ? street : sat).addTo(map);
    L.control.layers({ "항공사진": sat, "일반지도": street }, null, { position: "topleft" }).addTo(map);
    var layer = L.layerGroup().addTo(map);
    map.on("click", function (e) { window.OC_pickAt && window.OC_pickAt(e.latlng.lat, e.latlng.lng); });
    window.OCMAP = {
      ready: true,
      focus: function (c) { map.setView([c.la, c.lo], 19); L.popup({ offset: [0, -4] }).setLatLng([c.la, c.lo]).setContent(popup(c)).openOn(map); },
      draw: function (state, cafes, sweets, stations, foods) {
        layer.clearLayers();
        foodsFor(state, foods).forEach(function (c) {
          L.circleMarker([c.la, c.lo], { radius: 3, color: "#fff", weight: 1, fillColor: colorOf(c), fillOpacity: c.m <= state.r ? 0.9 : 0.4 }).bindPopup(popup(c)).addTo(layer);
        });
        var key = state.lat.toFixed(5) + state.lon.toFixed(5) + state.r;
        if (key !== lastKey) { map.setView([state.lat, state.lon], zoomFor(state.r)); lastKey = key; }
        L.circle([state.lat, state.lon], { radius: state.r, color: "#fff", weight: 2, dashArray: "6 5", fillColor: "#fff", fillOpacity: 0.08, interactive: false }).addTo(layer);
        (stations || []).forEach(function (s) {
          if (Math.abs(s[2] - state.lat) > 0.02 || Math.abs(s[3] - state.lon) > 0.025) return;
          L.marker([s[2], s[3]], { interactive: false, icon: L.divIcon({ className: "", html: '<span style="background:#111;color:#fff;font:700 12px sans-serif;padding:2px 6px;border-radius:4px;white-space:nowrap">' + esc(s[0]) + '역</span>', iconAnchor: [0, 22] }) }).addTo(layer);
        });
        cafes.concat(sweets).forEach(function (c) {
          var inside = c.m <= state.r;
          var mk = c.t === "c"
            ? L.circleMarker([c.la, c.lo], { radius: c.b >= 0 ? 6 : 5, color: "#fff", weight: 1.5, fillColor: colorOf(c), fillOpacity: inside ? 1 : 0.5 })
            : L.marker([c.la, c.lo], { icon: L.divIcon({ className: "", iconSize: [11, 11], html: '<div style="width:11px;height:11px;border:1.5px solid #fff;background:' + colorOf(c) + ';opacity:' + (inside ? 1 : 0.55) + '"></div>' }) });
          mk.bindPopup(popup(c)).addTo(layer);
        });
        L.circleMarker([state.lat, state.lon], { radius: 7, color: "#fff", weight: 3, fillColor: "#111", fillOpacity: 1, interactive: false }).addTo(layer);
      }
    };
    hideCanvas(); window.OC_redraw && window.OC_redraw();
  }
  function hideCanvas() {
    var cv = document.getElementById("localMap"); if (cv) cv.style.visibility = "hidden";
    var ld = document.getElementById("mapLoading"); if (ld) ld.style.zIndex = "2";
  }
  if (cfg.NAVER_CLIENT_ID) startNaver("ncpKeyId"); else if (cfg.KAKAO_JS_KEY) startKakao(); else startLeaflet();
})();
