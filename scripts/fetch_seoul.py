#!/usr/bin/env python3
"""서울시 상권분석서비스(서울 열린데이터광장 OpenAPI) → docs/seoul.json

서울 1,650개 상권마다
  - 커피-음료 추정매출 (최신 분기, 전분기, 전년 같은 분기), 결제 건수, 주말 매출, 시간대·연령대 매출
  - 유동인구 (최신 분기, 전분기), 시간대·연령대
  - 직장인구, 연령대
  - 상권 위치(중심점), 자치구·행정동, 면적
을 모은다. 키(SEOUL_KEY)가 없으면 아무것도 하지 않는다.

사용: python scripts/fetch_seoul.py docs/seoul.json
변경이 있으면 종료 코드 0과 함께 'SEOUL_CHANGED=1'을 출력한다.
"""
import json, os, sys, time
import requests

OUT = sys.argv[1] if len(sys.argv) > 1 else 'docs/seoul.json'
KEY = os.environ.get('SEOUL_KEY', '').strip()
FORCE = os.environ.get('FORCE') == 'true'
COFFEE = 'CS100010'  # 커피-음료
TM = ['00_06', '06_11', '11_14', '14_17', '17_21', '21_24']
AG = ['10', '20', '30', '40', '50', '60_ABOVE']

def api(svc, s, e, *extra):
    url = f'http://openapi.seoul.go.kr:8088/{KEY}/json/{svc}/{s}/{e}/' + '/'.join(extra)
    for i in range(5):
        try:
            d = requests.get(url, timeout=60).json()
            b = d.get(svc)
            if b is not None: return b.get('list_total_count', 0), b.get('row') or []
            res = d.get('RESULT') or {}
            if res.get('CODE') == 'INFO-200': return 0, []  # 자료 없음
            raise RuntimeError(f'{svc} {res}')
        except Exception as ex:
            if i == 4: raise
            print('다시 시도', svc, s, ex, flush=True); time.sleep(5 * (i + 1))

def fetch_all(svc, *extra):
    total, rows = api(svc, 1, 1000, *extra)
    for s in range(1001, total + 1, 1000):
        rows += api(svc, s, min(s + 999, total), *extra)[1]
    print(svc, extra, total, '줄', flush=True)
    return rows

def prev_q(q, n=1):
    y, k = int(q[:4]), int(q[4])
    for _ in range(n):
        k -= 1
        if k == 0: y -= 1; k = 4
    return f'{y}{k}'

def latest_q(svc):
    t = time.localtime(); q = f'{t.tm_year}{(t.tm_mon - 1) // 3 + 1}'
    for _ in range(8):
        if api(svc, 1, 1, q)[0] > 0: return q
        q = prev_q(q)
    raise RuntimeError(f'{svc} 최근 분기 자료가 없습니다')

def n(x):
    try: return int(round(float(x or 0)))
    except Exception: return 0

def main():
    if not KEY:
        print('SEOUL_KEY 없음: 서울 상권 자료는 건너뜀'); return
    old = {}
    try: old = json.load(open(OUT, encoding='utf-8'))
    except Exception: pass
    q = latest_q('VwsmTrdarSelngQq'); fq = latest_q('VwsmTrdarFlpopQq')
    print('매출 분기', q, '유동인구 분기', fq, flush=True)
    if not FORCE and old.get('q') == q and old.get('fq') == fq:
        print('서울 상권 변경 없음'); return

    # 상권 영역 (중심 좌표는 TM 중부원점 EPSG:5181)
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:5181', 'EPSG:4326', always_xy=True)
    area = {}
    for r in fetch_all('TbgisTrdarRelm'):
        lon, lat = tr.transform(float(r['XCNTS_VALUE']), float(r['YDNTS_VALUE']))
        area[r['TRDAR_CD']] = [r['TRDAR_CD'], r['TRDAR_CD_NM'], r['TRDAR_SE_CD_NM'], round(lat * 1e5), round(lon * 1e5),
                               r['SIGNGU_CD_NM'], r['ADSTRD_CD_NM'], n(r['RELM_AR'])]
    assert len(area) > 1000, len(area)

    def coffee(qq):
        out = {}
        for r in fetch_all('VwsmTrdarSelngQq', qq):
            if r['SVC_INDUTY_CD'] != COFFEE: continue
            out[r['TRDAR_CD']] = r
        return out
    s0, s1, s4 = coffee(q), coffee(prev_q(q)), coffee(prev_q(q, 4))
    f0 = {r['TRDAR_CD']: r for r in fetch_all('VwsmTrdarFlpopQq', fq)}
    f1 = {r['TRDAR_CD']: r for r in fetch_all('VwsmTrdarFlpopQq', prev_q(fq))}
    # 직장인구는 분기 지정이 안 되는 경우가 있어 전부 받아 상권마다 가장 최근 분기를 쓴다
    wk, wq = {}, ''
    for r in fetch_all('VwsmTrdarWrcPopltnQq'):
        c = r['TRDAR_CD']
        if c not in wk or r['STDR_YYQU_CD'] > wk[c]['STDR_YYQU_CD']: wk[c] = r
        wq = max(wq, r['STDR_YYQU_CD'])

    A = []
    for c, a in area.items():
        r = s0.get(c)
        cf = 0
        if r and n(r['THSMON_SELNG_AMT']) > 0:
            p, y = s1.get(c), s4.get(c)
            cf = [n(r['THSMON_SELNG_AMT']), n(r['THSMON_SELNG_CO']),
                  n(p['THSMON_SELNG_AMT']) if p else None, n(y['THSMON_SELNG_AMT']) if y else None,
                  n(r['WKEND_SELNG_AMT']),
                  [n(r[f'TMZON_{t}_SELNG_AMT']) for t in TM], [n(r[f'AGRDE_{g}_SELNG_AMT']) for g in AG]]
        r = f0.get(c)
        fp = 0
        if r:
            p = f1.get(c)
            fp = [n(r['TOT_FLPOP_CO']), n(p['TOT_FLPOP_CO']) if p else None,
                  [n(r[f'TMZON_{t}_FLPOP_CO']) for t in TM], [n(r[f'AGRDE_{g}_FLPOP_CO']) for g in AG]]
        r = wk.get(c)
        wp = [n(r['TOT_WRC_POPLTN_CO']), [n(r[f'AGRDE_{g}_WRC_POPLTN_CO']) for g in AG], r['STDR_YYQU_CD']] if r else 0
        A.append(a + [cf, fp, wp])
    A.sort(key=lambda x: x[0])
    d = {'q': q, 'qp': prev_q(q), 'qy': prev_q(q, 4), 'fq': fq, 'wq': wq, 'updated': time.strftime('%Y-%m-%d'),
         'a': A, 'cols': ['상권코드', '상권명', '구분', '위도1e5', '경도1e5', '자치구', '행정동', '면적㎡',
                          '커피[매출,건수,전분기,전년,주말,시간6,연령6]', '유동[분기,전분기,시간6,연령6]', '직장[총,연령6,분기]']}
    ncf = sum(1 for x in A if x[8])
    print('상권', len(A), '커피 매출 있는 상권', ncf, flush=True)
    assert ncf > 500, ncf
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('SEOUL_CHANGED=1')

if __name__ == '__main__':
    main()
