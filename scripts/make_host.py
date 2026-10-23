#!/usr/bin/env python3
"""cafe-market.html(아티팩트용) → host/index.html(원클리어 주소용, 실제 지도) 변환. 사용: python3 make_host.py cafe-market.html host/index.html"""
import sys
s = open(sys.argv[1], encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep('<title>원클리어 카페 상권진단</title>', '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<title>원클리어 카페 상권진단</title>\n<link rel="stylesheet" href="leaflet/leaflet.css">')
rep('<div class="wrap">', '</head>\n<body>\n<div class="wrap">')
rep('<canvas id="localMap" role="img" aria-label="선택한 동네 주변 가게와 카페 위치"></canvas>', '<canvas id="localMap" role="img" aria-label="선택한 동네 주변 가게와 카페 위치"></canvas>\n          <div id="satMap" style="position:absolute;inset:0;z-index:4"></div>')
rep('    lastDraw = [cafes, grid, sweets, labels];', '    lastDraw = [cafes, grid, sweets, labels];\n    if (window.OCMAP && window.OCMAP.ready) { window.OCMAP.draw(state, cafes, sweets, ST); return; }')
rep('  function pxToLatLon(cx, cy) {', '''  window.OC_pickAt = function (lat, lon) { if (!DB) return; state.lat = lat; state.lon = lon; pickHere(); };
  window.OC_kind = function (c) { return c.t === "c" ? (c.b >= 0 ? BRANDS[c.b] : c.ds ? "디저트 카페" : "개인 카페") : SKIND[c.k] + (c.b >= 0 ? " · " + SBRANDS[c.b] : ""); };
  window.OC_links = function (c) { var dd = CODE[c.code]; return linksFor(c.name, c.la, c.lo, c.name + " " + (dd ? dd[2] : "") + " " + c.addr); };
  window.OC_redraw = function () { if (lastDraw) drawMap(lastDraw[0], lastDraw[1], lastDraw[2], lastDraw[3]); };
  function pxToLatLon(cx, cy) {''')
rep('''    var ll = pxToLatLon(e.clientX, e.clientY);
    state.lat = ll[0]; state.lon = ll[1];
''', '''    var ll = pxToLatLon(e.clientX, e.clientY);
    state.lat = ll[0]; state.lon = ll[1];
    pickHere();
  });
  function pickHere() {
''')
rep('''    $("placeName").textContent = state.dong[3] + " 부근";
    analyze();
  });''', '''    $("placeName").textContent = state.dong[3] + " 부근";
    analyze();
  }''')
rep('<span class="hint">휠로 확대·축소, 끌어서 이동, 누르면 그 자리로 다시 분석</span>', '<span class="hint">휠로 확대·축소, 끌어서 이동, 누르면 그 자리로 다시 분석</span>')
s = s.replace('.zoombar { position: absolute;', '.zoombar { display: none; position: absolute;')
s = s.rstrip() + '\n<script src="leaflet/leaflet.js"></script>\n<script src="config.js"></script>\n<script src="satmap.js"></script>\n</body>\n</html>\n'
open(sys.argv[2], 'w', encoding='utf-8').write(s)
print('ok')
