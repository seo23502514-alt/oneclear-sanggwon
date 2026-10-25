#!/usr/bin/env python3
"""지방행정 인허가 전국 파일(식품_휴게음식점, 식품_일반음식점)을 받아
카페 개업·폐업 레이더의 docs/radar/data.js 를 다시 만든다. (GitHub Actions에서 실행)

사용: python radar-tools/build_radar.py docs/radar/data.js [--dry]
  --dry : 파일을 쓰지 않고 요약만 출력
기존 data.js 의 시·도/시·군·구 경계(prov, muni)는 그대로 가져다 쓴다.
"""
import csv, io, json, os, re, sys, time
from datetime import date, datetime, timedelta, timezone
import requests
from pyproj import Transformer

OUT = sys.argv[1] if len(sys.argv) > 1 else 'docs/radar/data.js'
DRY = '--dry' in sys.argv
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
FILE = "https://file.localdata.go.kr"

SIDO = ['서울', '경기', '인천', '부산', '대구', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남광주', '경북', '경남', '제주', '기타']
SI = {s: i for i, s in enumerate(SIDO)}
SMAP = {'서울특별시': '서울', '서울시': '서울', '경기도': '경기', '인천광역시': '인천', '부산광역시': '부산', '대구광역시': '대구', '대전광역시': '대전',
        '울산광역시': '울산', '세종특별자치시': '세종', '강원특별자치도': '강원', '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
        '전북특별자치도': '전북', '전라북도': '전북', '전남광주통합특별시': '전남광주', '전라남도': '전남광주', '광주광역시': '전남광주',
        '경상북도': '경북', '경상남도': '경남', '제주특별자치도': '제주', '제주도': '제주'}
BRANDS = [('메가MGC커피', r'메가\s?엠지씨|메가커피|MEGA\s?MGC'), ('컴포즈커피', r'컴포즈'), ('빽다방', r'빽다방'), ('이디야커피', r'이디야'),
          ('스타벅스', r'스타벅스'), ('투썸플레이스', r'투썸'), ('할리스', r'할리스'), ('파스쿠찌', r'파스쿠찌'), ('엔제리너스', r'엔[제젤]리너스'),
          ('커피빈', r'커피빈'), ('폴바셋', r'폴\s?바셋'), ('더벤티', r'더벤티'), ('매머드커피', r'매머드'), ('우지커피', r'우지커피'),
          ('텐퍼센트커피', r'텐퍼센트'), ('바나프레소', r'바나프레소'), ('하삼동커피', r'하삼동'), ('커피베이', r'커피베이'), ('요거프레소', r'요거프레소'),
          ('공차', r'공차'), ('디저트39', r'디저트\s?39'), ('카페인중독', r'카페인중독'), ('봉명동내커피', r'봉명동내커피'), ('만랩커피', r'만랩커피'),
          ('1리터 계열', r'아임일리터|카페일리터|1리터|더리터'), ('해쉬커피', r'해쉬커피'), ('청자다방', r'청자다방'), ('카페16온스', r'16온스'),
          ('커피니', r'커피니'), ('던킨', r'던킨'), ('카페봄봄', r'봄봄'), ('쓰리엑스라지', r'쓰리엑스라지'), ('퐁치커피', r'퐁치커피'),
          ('차백도', r'차백도'), ('콩카페', r'콩카페'), ('이지브루잉', r'이지브루잉'), ('백억커피', r'백억커피'), ('하이오커피', r'하이오커피'),
          ('쥬씨', r'쥬씨'), ('읍천리382', r'읍천리'), ('카페아이갓에브리씽', r'아이갓에브리씽'), ('카페051', r'카페051'), ('달콤커피', r'달콤커피'),
          ('탐앤탐스', r'탐앤탐스'), ('그라츠커피랩', r'그라츠커피'), ('카페게이트', r'카페게이트'), ('셀렉토커피', r'셀렉토'),
          ('커피에반하다', r'커피에\s?반하다'), ('감성커피', r'감성커피'), ('빈스빈스', r'빈스빈스'), ('떠기다방', r'떠기다방'), ('지지고', r'지지고'),
          ('잇샌드', r'잇샌드'), ('스트릿1988', r'스트릿\s?1988'), ('위캔커피', r'위캔커피'), ('에브리커피', r'에브리커피'),
          ('히떼 로스터리', r'히떼\s?로스터리|HYTTE'), ('커피명가', r'커피명가'), ('빙동댕', r'빙동댕'), ('갈바트카페', r'갈바트'),
          ('니어블루', r'니어블루'), ('카페홈즈', r'카페홈즈'), ('컵오브커피', r'컵오브커피')]
BRANDS = [(b, re.compile(p, re.I)) for b, p in BRANDS]
SEN = re.compile(r'시니어클럽|시니어카페|노인복지|노인인력|실버카페|청춘카페|어르신')
BRANCH = re.compile(r'(\S+)\s*\(?[^\s()]{1,12}점\)?\s*$')
NOTB = re.compile(r'(본점|상점|전문점|백화점)\)?$')
TMP = re.compile(r'한시적|축제|마켓|부스|플리|야시장|총회|박람회|페스티벌|행사|장터')
NAMEC = re.compile(r'카페|커피|cafe|coffee|까페|에스프레소|로스터', re.I)
AL = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-./:;<=>?@[]^_`{}~'


def classify(n):
    if SEN.search(n): return 3, ''
    for b, p in BRANDS:
        if p.search(n): return 1, b
    if BRANCH.search(n) and not NOTB.search(n): return 2, ''
    return 0, ''


def enc(a):
    return ''.join(AL[v] if v < len(AL) else "'" + base36(v) + "'" for v in a)


def base36(n):
    s = ''
    while True:
        n, r = divmod(n, 36); s = '0123456789abcdefghijklmnopqrstuvwxyz'[r] + s
        if n == 0: return s


def get_retry(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = S.get(url, **kw); r.raise_for_status(); return r
        except Exception as e:
            if i == tries - 1: raise
            print('다시 시도', i + 1, url, e, flush=True); time.sleep(20 * (i + 1))


def open_csv(kind):
    """kind: rest_cafes / general_restaurants. 줄 단위 텍스트 스트림을 돌려준다."""
    info = f"{FILE}/file/{kind}/info"
    # 공공데이터포털 상세 페이지를 거쳐 들어온 것처럼 Referer 를 붙인다 (바로 열면 403)
    get_retry("https://www.data.go.kr/data/15006730/fileData.do", timeout=60)
    ri = S.get(info, headers={"Referer": "https://www.data.go.kr/"}, timeout=60)
    print(f'::notice::{kind} 안내 페이지 {ri.status_code} {ri.url}', flush=True)
    S.get(f"{FILE}/file/validate/download-count", headers={"Referer": info}, timeout=60)
    r = S.get(f"{FILE}/file/download/{kind}/info", headers={"Referer": info}, stream=True, timeout=1800)
    print(f'::notice::{kind} 다운로드 응답 {r.status_code} {r.headers.get("content-type")} {r.headers.get("content-length")}', flush=True)
    r.raise_for_status()
    ct = r.headers.get('content-type', '')
    print(kind, r.status_code, ct, r.headers.get('content-length'), flush=True)
    assert 'csv' in ct, f'{kind}: CSV가 아닌 응답 {ct}'
    path = os.path.join(os.environ.get('RUNNER_TEMP', '/tmp'), kind + '.csv')
    size = 0
    with open(path, 'wb') as fo:
        for ch in r.iter_content(1 << 20): fo.write(ch); size += len(ch)
    r.close()
    print(f'::notice::{kind} 받음 {size:,} 바이트', flush=True)
    assert size > 50_000_000, f'{kind}: 파일이 너무 작음 {size}'
    return open(path, encoding='cp949', errors='replace', newline='')


def main():
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).date()
    END = today.isoformat()
    this_monday = today - timedelta(days=today.weekday())
    NW = 104
    w0 = this_monday - timedelta(weeks=NW - 1)
    NM = (today.year - 2015) * 12 + today.month
    pm = date(today.year if today.month > 1 else today.year - 1, today.month - 1 if today.month > 1 else 12, 1)
    P0 = pm.isoformat()   # 지난달 1일부터 가게 점·목록

    def widx(d):
        try: t = date(int(d[:4]), int(d[5:7]), int(d[8:10]))
        except Exception: return -1
        i = (t - w0).days // 7
        return i if 0 <= i < NW else -1

    def midx(d):
        try: i = (int(d[:4]) - 2015) * 12 + int(d[5:7]) - 1
        except Exception: return -1
        return i if 0 <= i < NM else -1

    ST = [[{'m': [0] * (NM * 2), 'w': [0] * (NW * 2)} for _ in range(4)] for _ in SIDO]
    STOCK = [[0, 0, 0, 0] for _ in SIDO]
    AREA, BR, PTS, SENL = {}, {}, [], []
    maxD = ''
    cnt = {'rows': 0, 'cafe': 0}

    def add(pd, cd, st, name, s, sgg, x, y):
        nonlocal maxD
        cnt['cafe'] += 1
        si = SI.get(s, 16)
        t, brand = classify(name)
        try: life = (date.fromisoformat(cd) - date.fromisoformat(pd)).days if pd and cd else 99
        except Exception: life = 99
        tmp = bool(TMP.search(name)) or life <= 14
        active = bool(re.search(r'영업|정상', st))
        if t == 3: SENL.append([pd, cd, 1 if active else 0, name, s, sgg, x, y, 1 if tmp else 0])
        if tmp: return
        if pd and pd <= END and pd > maxD: maxD = pd
        key = s + ' ' + sgg
        A = AREA.setdefault(key, {'m': [0] * (NM * 2), 'w': [0] * (NW * 2), 'sx': 0.0, 'sy': 0.0, 'n': 0, 'stock': 0})
        B = None
        if brand: B = BR.setdefault(brand, {'m': [0] * (NM * 2), 'w': [0] * (NW * 2), 'stock': 0, 'ss': [0] * len(SIDO)})
        used = False
        for d, k in ((pd, 0), (cd, 1)):
            if not d or d > END: continue
            mi, wi = midx(d), widx(d)
            if mi >= 0:
                ST[si][t]['m'][mi * 2 + k] += 1; A['m'][mi * 2 + k] += 1
                if B: B['m'][mi * 2 + k] += 1
                used = True
            if wi >= 0:
                ST[si][t]['w'][wi * 2 + k] += 1; A['w'][wi * 2 + k] += 1
                if B: B['w'][wi * 2 + k] += 1
        if active:
            STOCK[si][t] += 1; A['stock'] += 1; used = True
            if B: B['stock'] += 1; B['ss'][si] += 1
        if used and x and y:
            try: A['sx'] += float(x); A['sy'] += float(y); A['n'] += 1
            except ValueError: pass
        if (P0 <= pd <= END) or (cd and P0 <= cd <= END):
            PTS.append([pd, cd, name, si, sgg, x, y, t, brand])

    def run(kind, keep):
        f = open_csv(kind)
        rd = csv.reader(f)
        head = next(rd); I = {h.strip(): i for i, h in enumerate(head)}
        need = ['업태구분명', '사업장명', '도로명주소', '지번주소', '인허가일자', '폐업일자', '영업상태명', '좌표정보(X)', '좌표정보(Y)']
        miss = [k for k in need if k not in I]
        assert not miss, f'{kind}: 열 이름이 바뀜 {miss}'
        n0 = cnt['cafe']
        for row in rd:
            cnt['rows'] += 1
            if len(row) < len(head): continue
            up = row[I['업태구분명']]; name = row[I['사업장명']].strip()
            if not keep(up, name): continue
            addr = (row[I['도로명주소']] or row[I['지번주소']] or '').strip(); p = addr.split()
            s = SMAP.get(p[0] if p else '', '기타')
            p1 = p[1] if len(p) > 1 else ''; p2 = p[2] if len(p) > 2 else ''
            sgg = p1 + (' ' + p2 if p1.endswith('시') and p2.endswith('구') else '')
            add(row[I['인허가일자']], row[I['폐업일자']], row[I['영업상태명']], name, s, '세종시' if s == '세종' else sgg,
                row[I['좌표정보(X)']].strip(), row[I['좌표정보(Y)']].strip())
        print(kind, '카페', cnt['cafe'] - n0, '누적 행', cnt['rows'], flush=True)

    run('rest_cafes', lambda up, nm: up in ('커피숍', '다방', '전통찻집') or ('기타' in up and bool(NAMEC.search(nm))))
    run('general_restaurants', lambda up, nm: ('까페' in up or '커피숍' in up) and '라이브' not in up and '키즈' not in up)

    tr = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)

    def ll(x, y):
        try: x, y = float(x), float(y)
        except (TypeError, ValueError): return None, None
        lon, lat = tr.transform(x, y)
        if not (32.5 < lat < 39.5 and 124 < lon < 132.5): return None, None
        return round(lat, 5), round(lon, 5)

    old = open(OUT, encoding='utf-8').read()
    od = json.loads(old[old.index('=') + 1:].rstrip().rstrip(';'))
    areas = []
    for k, A in AREA.items():
        lat, lon = ll(A['sx'] / A['n'], A['sy'] / A['n']) if A['n'] else (None, None)
        areas.append([k, lat, lon, A['stock'], enc(A['m']), enc(A['w'])])
    out = {
        'maxD': maxD, 'w0': w0.isoformat(), 'pt0': P0,
        'st': [[[enc(x['m']), enc(x['w'])] for x in r] for r in ST],
        'stock': STOCK, 'areas': areas,
        'brands': [[b, B['stock'], B['ss'], enc(B['m']), enc(B['w'])] for b, B in BR.items()],
        'pts': [[p[0], p[1], p[2], p[3], p[4], *ll(p[5], p[6]), p[7], p[8]] for p in PTS],
        'sen': [[s[0], s[1], s[2], s[3], s[4], s[5], *ll(s[6], s[7]), s[8]] for s in SENL],
        'prov': od['prov'], 'muni': od['muni'],
    }
    tot = sum(map(sum, STOCK)); old_tot = sum(map(sum, od['stock']))
    print(f'::notice::기준일 {maxD} · 영업 중 {old_tot:,} → {tot:,} · 시·군·구 {len(areas)} · 브랜드 {len(BR)} · 가게 점 {len(PTS)} · 시니어 {len(SENL)}', flush=True)
    assert maxD >= od.get('maxD', ''), '기준일이 예전보다 이릅니다'
    assert 0.85 <= tot / max(1, old_tot) <= 1.15, '영업 중 카페 수가 15% 넘게 바뀌어 멈춥니다'
    if DRY:
        print('dry run: 파일을 쓰지 않습니다'); return
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    with open(OUT, 'w', encoding='utf-8') as f: f.write('window.CAFE_DATA=' + s + ';\n')
    with open(os.environ.get('GITHUB_ENV', os.devnull), 'a') as f: f.write(f'RADAR_DATE={maxD}\n')
    print('저장', OUT, len(s), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # GitHub 실행 화면 위쪽(Annotations)에 바로 보이도록
        print(f'::error::{type(e).__name__}: {str(e)[:400]}', flush=True)
        raise
