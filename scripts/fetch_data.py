#!/usr/bin/env python3
"""공공데이터포털 상가(상권)정보 + 행정안전부 행정동 주민등록인구를 받아
build.py 가 읽는 extract.txt / pop.txt 를 만든다. (GitHub Actions에서 실행)
사용: python scripts/fetch_data.py work/   → work/extract.txt, work/pop.txt, work/version.json
"""
import csv, io, json, re, sys, time, zipfile, os
import requests

OUT = sys.argv[1] if len(sys.argv) > 1 else 'work'
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
BASE = "https://www.data.go.kr"; PK = "15083033"; DETAIL = f"{BASE}/data/{PK}/fileData.do"

def get_retry(url, tries=4, **kw):
    # 공공데이터 서버가 잠깐 안 받는 경우가 있어 몇 번 다시 시도한다
    for i in range(tries):
        try:
            r = S.get(url, **kw); r.raise_for_status(); return r
        except Exception as e:
            if i == tries - 1: raise
            print('다시 시도', i + 1, url, e, flush=True); time.sleep(30 * (i + 1))

def latest_store_version():
    html = get_retry(DETAIL, timeout=60).text
    print("data.go.kr 페이지", len(html), flush=True)
    detail_pk = next(p for p in re.findall(r"fn_fileDataDown\(\s*'%s'\s*,\s*'([^']*)'" % PK, html) if p.strip())
    r = S.post(f"{BASE}/tcs/dss/selectFileDataDownload.do?recommendDataYn=Y", data={"publicDataPk": PK, "publicDataDetailPk": detail_pk},
               headers={"X-Requested-With": "XMLHttpRequest", "Referer": DETAIL}, timeout=60).json()
    nm = r["dataSetFileDetailInfo"]["dataNm"]
    return re.search(r"(\d{8})", nm).group(1), r["atchFileId"], str(r["fileDetailSn"]), nm

def download_store(atch, sn, nm):
    url = f"{BASE}/cmm/cmm/fileDownload.do?atchFileId={atch}&fileDetailSn={sn}&dataNm={requests.utils.quote(nm)}"
    buf = io.BytesIO()
    with S.get(url, headers={"Referer": DETAIL}, stream=True, timeout=900) as r:
        r.raise_for_status()
        for ch in r.iter_content(1 << 20): buf.write(ch)
    data = buf.getvalue()
    assert data[:4] == b"PK\x03\x04" and len(data) > 100_000_000, f"bad zip {len(data)}"
    return zipfile.ZipFile(io.BytesIO(data))

MAJ = ['음식','소매','수리·개인','과학·기술','교육','시설관리·임대','예술·스포츠','부동산','숙박','보건의료']
BR = [re.compile(x, re.I) for x in [r'메가커피|메가엠지씨|메가MGC','컴포즈','이디야','스타벅스','빽다방','투썸','더벤티','공차','할리스','파스쿠찌','커피빈','엔제리너스','폴바셋','매머드','텐퍼센트','하삼동']]
SUB = {'빵/도넛': 0, '아이스크림/빙수': 1, '토스트/샌드위치/샐러드': 2, '편의점': 3}
SW = {'빵/도넛', '아이스크림/빙수', '떡/한과'}
# 관공서·시니어·공공 운영 매장 추정 규칙 (상호명·건물명)
#  - 시니어·장애인·자활·복지관: 상호명에 운영 단서가 있으면 카페·빵집뿐 아니라 식당·반찬가게·세탁소도 포함
#    (건물명 단서는 카페·빵집만. 아파트 이름의 '실버·은빛'은 쓰지 않음)
#  - 관공서·공공시설: 건물명이 관공서·도서관 등이거나, 상호명에 기관 이름이 있을 때만 (○○시청점·법원점처럼 근처라 붙인 이름은 제외)
#    일반 프랜차이즈 입점 매장과 대학 시설은 뺀다
_G = r'(?:구청|시청|군청|(?<!충청)도청(?!주))(?!각|소년)|(?:정부|합동|복합|종합|통합|행정|북부|남부|동부|서부|[가-힣]{1,4}[시군구도])청사(?!포)'
_LOC = r'\s*(?:앞|옆|역|길|로\d|[삼사오]거리|입구|맞은편|건너|부근|근처|정문점|후문점|본점|\d*호?점|지점|\s\S{1,6}점$)'   # 상호명 뒤에 붙으면 '근처라 붙인 이름'
_BEND = r'(?=$|[\s\d(]|본관|별관|신관|민원|청사|내|동$|구내|정문|후문|안내|부속)'          # 건물명이 기관 이름으로 끝날 때
_GSUP = re.compile(r'구내|직원|복지|후생|운영위원회|노동조합|공무원|매점|민원')  # 시청·구청 이름만 있을 때 기관 운영으로 보는 단서
# 매장이 아닌 곳: 단체 사무실, 요양·재가 기관, 복지용구점, 학교 매점 조합, 경로당
NOT_STORE = re.compile(r'(?:협회|(?<!복)지회|지부|연합회|연맹|상조)$|재가|요양|복지용구|보장구|주간보호|주야간|방문간호|방문요양|시니어케어|토탈케어|케어센터|경로당|학교.*협동조합|교회')
_APT = re.compile(r'아파트|빌라|빌$|빌\d|타운|하이츠|팰리스|맨션|오피스텔|스위트|센트|뷰|타워|프라자|플라자|빌딩|시티|캐슬|자이|힐스|푸르지오|래미안|e편한|SK|엘가|상가')
PUB_RULES = [
    # (이름, 상호명 규칙, 건물명 규칙, 엄격 여부)
    ('시니어·노인일자리',
     re.compile(r'시니어클럽|시니어클립|노인(?:복지|종합|문화|건강|일자리|취업|인력|회|지회|요양)|경로식당|어르신|시니어|청춘카페|카페청춘|청춘드림|인생플러스|실버[카까]페|[카까]페실버|은빛[카까]페|실버인력'),
     re.compile(r'시니어클럽|노인(?:복지|종합|문화|건강|일자리|취업|인력|회|지회|요양)|경로당|어르신'), False),
    ('장애인·자활·사회적경제',
     re.compile(r'장애인|보호작업장|직업재활|근로사업장|아이갓에브리씽|아이갓에브리띵|I ?GOT ?EVERYTHING|굿윌|자활(?!어)|사회적협동조합|사회적기업|마을기업|꿈앤카페', re.I),
     re.compile(r'장애인|보호작업장|직업재활|자활(?!어)'), False),
    ('복지관·복지시설',
     re.compile(r'복지관|사회복지|복지센터|가족센터|여성회관|여성센터|건강가정|청소년상담'),
     re.compile(r'복지관|복지회관|복지센터|가족센터|여성회관|여성센터|건강가정'), True),
    ('관공서 안 매장',
     re.compile(_G + r'|행정복지센터|주민센터|읍사무소|면사무소|동사무소|보건소|교육청|교육지원청|경찰서|경찰청|소방서|세무서|(?:지방|가정|고등|행정|대)법원|등기소|고용센터|국민연금|건강보험공단|우체국|국회|(?<!협)의회(?!상)'),
     re.compile(_G + r'|행정복지센터|주민센터|읍사무소|면사무소|동사무소|보건소|교육청|교육지원청|경찰서|경찰청|소방서|세무서|법원|등기소|고용센터|국민연금|건강보험공단|우체국|국회|의회'), True),
    ('공공 문화·체육시설',
     re.compile(r'(?:시립|구립|군립|도립|국립|공립)\S{0,8}(?:도서관|미술관|박물관|과학관|수목원)|청소년수련관|청소년문화의집|평생학습|휴양림'),
     re.compile(r'도서관|미술관|박물관|과학관|문화센터|문화회관|예술회관|시민회관|구민회관|군민회관|문화의전당|체육센터|국민체육|체육문화|문화체육|청소년수련관|청소년센터|청소년문화|평생학습|휴양림|수목원'), True),
]
FRANCHISE = re.compile(r'메가커피|메가엠지씨|메가MGC|컴포즈|이디야|스타벅스|빽다방|투썸|더벤티|공차|할리스|파스쿠찌|커피빈|엔제리너스|엔젤리너스|폴바셋|매머드|메머드|텐퍼센트|하삼동|시나본|백억커피|포트캔|읍천리|맥켄지|커피니|트리플에이|일마지오|온어스|카페베네|커피에반하다|감성커피|요거프레소|바나프레소|커피나무|탐앤탐스|셀렉토|커피베이|토프레소|그라찌에|카페봄봄|쥬씨|블루샥|하이오|더리터|빈스빈스|드롭탑|커피스미스|달콤커피|파리바게|뚜레쥬르|던킨|배스킨|베스킨|설빙|크리스피|무인|커피명가|카페051|마노핀|커피스토리|전광수|테라로사|블루보틀|커피랑도서관|본죽|써브웨이|베러먼데이|달리는커피', re.I)
NOT_PUBLIC = re.compile(r'대학|캠퍼스|후생복지|학생복지|시청각|[가-힣]대\s?(제\d)?복지관|[가-힣]대점|가톨릭대|협의회|도서관앞|커피도서관|만화|스터디')
def pub_tag(name, bldg, cafe_like):
    """매장이 관공서·시니어 등에서 운영하는 곳으로 보이면 분류 이름을, 아니면 None."""
    if NOT_STORE.search(name): return None
    if name.endswith('복지회') and not re.search(r'경찰|소방|청|공무원|직원', name): return None  # 기관 구내매장을 운영하는 복지회만 남김
    bldg = '' if (bldg and _APT.search(bldg)) else (bldg or '')
    for tag, nrx, brx, strict in PUB_RULES:
        hit = False
        bhit = bool(bldg) and (any(re.match(_BEND, bldg[m.end():]) for m in brx.finditer(bldg)) if strict else bool(brx.search(bldg)))
        for m in nrx.finditer(name):
            if strict and re.match(_LOC, name[m.end():]) and not bhit: continue  # 'X시청점' 같은 위치 이름
            if strict and not bhit and re.fullmatch(_G, m.group(0)) and not _GSUP.search(name): continue  # 이름에 '시청'만 있는 일반 가게
            hit = True; break
        if not hit and cafe_like:
            if bhit and FRANCHISE.search(name): return None  # 건물만 보고 잡힌 프랜차이즈 입점 매장
            hit = bhit
        if not hit: continue
        if strict and (FRANCHISE.search(name) or NOT_PUBLIC.search(name) or NOT_PUBLIC.search(bldg)): return None
        return tag
    return None
PUB_MAJ = {'음식', '소매', '수리·개인'}  # 상호명에 운영 단서가 있을 때 포함하는 업종

LM = re.compile(r'백화점|대형 마트|대형마트|쇼핑|아울렛|면세|종합 병원|종합병원|영화관')

# 원본에서 '카페'로 분류됐지만 상호명으로 보아 다른 업종이 확실한 곳 (부동산·임대·호프·식당·유통 등)
CAFE_WORD = re.compile(r'커피|카페|까페|캬페|cafe|caffe|coffee|다방|찻집|티하우스|티룸|tea|로스터|로스팅|roast|에스프레소|espresso|브루|brew|라운지|디저트|베이커리|bakery|케이크|cake|쥬스|주스|juice|스무디|와플|빙수|젤라또|마카롱|브런치|빵|도넛|말차|버블|요거|토스트|팥|북|보드게임|라떼|latte|쥬씨|설빙|벌툰|스타벅스|투썸|이디야|메가|컴포즈|빽다방|할리스|파스쿠찌|엔제리너스|엔젤리너스|폴바셋|매머드|텐퍼센트|하삼동|더벤티|공차|커피빈|드롭탑|바나프레소|더리터|요아정|탐앤탐스|커피베이|빈스빈스|댄싱컵', re.I)
CAFE_KEEP = re.compile(r'시니어클럽|협동조합|자활|복지|사업단|쉼터|휴게소|키움')  # 사회적경제·기관 운영 카페는 그대로 둔다
NOT_CAFE = re.compile(r'(매니지먼트|엔터테인먼트|가스(?!펠)|(?<!일)상사$|상사주$|(?<!공정)무역(?!투자)|(?<!원)유통|물산|부동산|공인중개|중개사|중개법인|임대|종친회|화수회|건설|건축|인테리어|설비|공업|물류|운수|세무|회계|컨설팅|솔루션|시스템|네트웍|노래연습장|노래궁|노래주점|단란주점|(?<!과)당구|볼링|호프|포차|치킨|김밥|분식|냉면|국밥|돈가스|식당|슈퍼$|슈퍼쉼터|청과|수산|정육|축산|여관|모텔|약국|치과|미용|네일|세탁|사진관|인쇄|광고)', re.I)

def not_cafe(name, brand):
    if brand >= 0 or CAFE_WORD.search(name) or CAFE_KEEP.search(name): return False
    for m in NOT_CAFE.finditer(name):
        if re.match(r'[^ ]{0,8}점$', name[m.end():]): continue  # '○○유통센터점'처럼 입점 위치를 뜻하는 경우
        return True
    return False

def aggregate(zf):
    agg, grid, bld, cafes, sweets, lms, foods, pubs, rows, nc = {}, {}, {}, [], [], [], [], [], 0, 0
    for info in zf.infolist():
        if not info.filename.lower().endswith('.csv'): continue
        with zf.open(info) as fh:
            rd = csv.reader(io.TextIOWrapper(fh, encoding='utf-8-sig', newline=''))
            H = next(rd); I = {k: H.index(k) for k in ['상호명','지점명','상권업종대분류명','상권업종중분류명','상권업종소분류명','시도명','시군구명','시군구코드','행정동코드','행정동명','도로명','도로명주소','건물명','층정보','경도','위도']}
            for f in rd:
                if not f: continue
                rows += 1
                code = f[I['행정동코드']]; r = agg.get(code)
                if r is None:
                    r = agg[code] = {'s': f[I['시도명']], 'g': f[I['시군구명']], 'd': f[I['행정동명']], 'n': 0, 'la': 0.0, 'lo': 0.0, 'll': 0, 'mj': [0]*10, 'cafe': 0, 'f1': 0, 'sub': [0]*4, 'br': [0]*16, 'rd': {}}
                r['n'] += 1
                try: lo = float(f[I['경도']]); la = float(f[I['위도']])
                except ValueError: lo = la = 0.0
                ok = la > 30 and lo > 120
                if ok: r['la'] += la; r['lo'] += lo; r['ll'] += 1
                cat, sub = f[I['상권업종대분류명']], f[I['상권업종소분류명']]
                mi = MAJ.index(cat) if cat in MAJ else -1
                if mi >= 0: r['mj'][mi] += 1
                if sub in SUB: r['sub'][SUB[sub]] += 1
                nm2 = (f[I['상호명']] + (' ' + f[I['지점명']] if f[I['지점명']] else '')).replace('\t', ' ').replace('\n', ' ').replace('|', ' ')
                addr = ' '.join((f[I['도로명주소']] or '').split(' ')[2:])
                fl = f[I['층정보']] or ''
                b = next((q for q, rx in enumerate(BR) if rx.search(f[I['상호명']])), -1) if sub == '카페' else -1
                if sub == '카페' and not_cafe(nm2, b):
                    sub = '카페 아님'; nc += 1
                if sub == '카페':
                    r['cafe'] += 1
                    if b >= 0: r['br'][b] += 1
                    if fl == '1': r['f1'] += 1
                    road = (f[I['도로명']] or '').split(' ')[-1]
                    if road: r['rd'][road] = r['rd'].get(road, 0) + 1
                    if ok: cafes.append([code, f'{la:.5f}', f'{lo:.5f}', nm2, str(b), fl, addr])
                if not ok: continue
                key = (int(la * 1000 // 1), int(lo * 800 // 1)); g = grid.get(key)
                if g is None: g = grid[key] = [0]*8
                g[0] += 1
                gi = {0: 1, 1: 2, 4: 3, 9: 4, 3: 5, 8: 6, 2: 7}.get(mi)
                if gi: g[gi] += 1
                if cat in PUB_MAJ and sub != '카페 아님':
                    bn0 = (f[I['건물명']] or '').strip(); cl = sub == '카페' or sub in SW
                    tg = pub_tag(nm2, bn0, cl)
                    if tg and not cl and tg in ('관공서 안 매장', '공공 문화·체육시설', '복지관·복지시설') and not re.search(r'구내식당|직원식당|매점|운영위원회|복지회|후생', nm2): tg = None  # 기관 안 일반 식당은 뺀다
                    if tg: pubs.append([code, f'{la:.5f}', f'{lo:.5f}', nm2, sub, tg, bn0, addr, cat])
                if sub in SW: sweets.append([code, f'{la:.5f}', f'{lo:.5f}', nm2, sub, fl, addr])
                elif cat == '음식' and sub not in ('카페', '카페 아님'): foods.append([f'{la:.5f}', f'{lo:.5f}', nm2, f[I['상권업종중분류명']].strip(), sub])
                if LM.search(sub): lms.append([code, f'{la:.5f}', f'{lo:.5f}', nm2, sub, addr])
                bn = (f[I['건물명']] or '').strip()
                if bn:
                    k2 = f[I['시군구코드']] + '|' + bn; b2 = bld.get(k2)
                    if b2 is None: b2 = bld[k2] = [0, 0.0, 0.0, addr, 0, code]
                    b2[0] += 1; b2[1] += la; b2[2] += lo
                    if sub == '카페': b2[4] += 1
    print('카페 아님으로 제외', nc, flush=True)
    return agg, grid, bld, cafes, sweets, lms, foods, pubs, rows

def latest_population():
    S.get("https://jumin.mois.go.kr/statMonth.do", timeout=60)
    t = time.localtime(); y, m = t.tm_year, t.tm_mon
    for back in range(0, 4):
        mm, yy = m - back, y
        while mm <= 0: mm += 12; yy -= 1
        d = {"sltOrgType": "1", "sltOrgLvl1": "A", "sltOrgLvl2": "", "gender": "gender", "genderPer": "genderPer", "generation": "generation",
             "sltUndefType": "", "sltOrderType": "1", "sltOrderValue": "ASC", "category": "month", "state": "3",
             "searchYearStart": str(yy), "searchMonthStart": f"{mm:02d}", "searchYearEnd": str(yy), "searchMonthEnd": f"{mm:02d}"}
        r = S.post("https://jumin.mois.go.kr/downloadExcel2.do?searchYearMonth=month&xlsStats=3", data=d, timeout=300)
        if r.status_code != 200 or len(r.content) < 8000: continue
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        out = []
        rows_all = list(wb.worksheets[0].iter_rows(values_only=True))
        print('주민 통계', yy, mm, len(r.content), 'bytes', len(rows_all), 'rows', rows_all[:4], flush=True)
        for row in rows_all:
            c = str(row[0] or '').strip()
            if re.fullmatch(r'\d{10}', c) and c[5:] != '00000':
                pop = str(row[2] or '0').replace(',', '').strip(); hh = str(row[3] or '0').replace(',', '').strip()
                if pop.isdigit(): out.append(f'{c[:8]},{pop},{hh if hh.isdigit() else 0}')
        if out: return f'{yy}-{mm:02d}', out
    raise RuntimeError('주민등록 인구 통계를 받지 못했습니다')

def fetch_workers(out):
    """통계청 SGIS 사업체통계: 전국 읍면동별 종사자 수(최신 연도). 키가 없거나 실패하면 None (이전 값 유지)."""
    key, sec = os.environ.get('SGIS_KEY', ''), os.environ.get('SGIS_SECRET', '')
    if not key or not sec:
        print('SGIS 키 없음: 종사자 수는 이전 값 유지', flush=True); return None
    B = 'https://sgisapi.kostat.go.kr/OpenAPI3'
    try:
        tok = requests.get(f'{B}/auth/authentication.json', params={'consumer_key': key, 'consumer_secret': sec}, timeout=30).json()['result']['accessToken']
        def get(**p):
            p['accessToken'] = tok
            for _ in range(3):
                try:
                    r = requests.get(f'{B}/stats/company.json', params=p, timeout=60).json()
                    if r.get('errCd') == 0: return r.get('result') or []
                except Exception: pass
                time.sleep(2)
            raise RuntimeError(f'SGIS 실패 {p.get("adm_cd")}')
        year, sidos = None, []
        for y in range(time.localtime().tm_year, 2015, -1):
            sidos = get(year=str(y))
            if sidos: year = y; break
        lines = []
        for sd in sidos:
            sggs = {x['adm_cd']: x['adm_nm'] for x in get(year=str(year), adm_cd=sd['adm_cd'], low_search='1')}
            for x in get(year=str(year), adm_cd=sd['adm_cd'], low_search='2'):
                lines.append('\t'.join([sd['adm_nm'], sggs.get(x['adm_cd'][:5], ''), x['adm_nm'], str(int(x['tot_worker'] or 0)), str(int(x['corp_cnt'] or 0))]))
        open(f'{out}/workers.txt', 'w', encoding='utf-8').write(f'{year}\n' + '\n'.join(lines))
        print('종사자 수', year, len(lines), '곳', flush=True)
        return year
    except Exception as e:
        print('종사자 수 받기 실패, 이전 값 유지:', e, flush=True); return None

if __name__ == '__main__':
    ver, atch, sn, nm = latest_store_version()
    popym, pop = latest_population()
    prev = {}
    try: prev = json.load(open('docs/dongs.json'))['meta']
    except Exception: pass
    force = os.environ.get('FORCE') == 'true'
    wy = fetch_workers(OUT)
    if not force and prev.get('v') == ver and prev.get('pop') == popym and (wy is None or prev.get('wy') == wy):
        print(f'변경 없음: 상가 {ver}, 주민 {popym}')
        json.dump({'changed': False, 'ver': ver, 'pop': popym}, open(f'{OUT}/version.json', 'w')); sys.exit(0)
    open(f'{OUT}/pop.txt', 'w', encoding='utf-8').write(f'POP|{popym}|' + ';'.join(pop) + '|END')
    print('상가 다운로드', nm, flush=True)
    agg, grid, bld, cafes, sweets, lms, foods, pubs, rows = aggregate(download_store(atch, sn, nm))
    dong = [[code, r['s'], r['g'], r['d'], r['n'], round(r['la']/r['ll'], 5) if r['ll'] else None, round(r['lo']/r['ll'], 5) if r['ll'] else None,
             r['mj'], r['cafe'], r['f1'], r['sub'], r['br'], sorted(r['rd'].items(), key=lambda x: -x[1])[:3]] for code, r in agg.items()]
    with open(f'{OUT}/extract.txt', 'w', encoding='utf-8') as w:
        w.write(f'#VER\n{ver}\n#ROWS\n{rows}\n#DONG\n' + json.dumps(dong, ensure_ascii=False) + '\n#CAFES\n')
        w.write('\n'.join('\t'.join(x) for x in cafes) + '\n#GRID\n')
        w.write('\n'.join(f'{k[0]},{k[1]},' + ','.join(map(str, g)) for k, g in grid.items()) + '\n#SWEET\n')
        w.write('\n'.join('\t'.join(x) for x in sweets) + '\n#LM\n' + '\n'.join('\t'.join(x) for x in lms) + '\n#FOOD\n')
        w.write('\n'.join('\t'.join(x) for x in foods) + '\n#PUB\n')
        w.write('\n'.join('\t'.join(x) for x in pubs) + '\n#BLD\n')
        w.write('\n'.join('\t'.join([k.split('|')[0], k.split('|', 1)[1], str(b[0]), f'{b[1]/b[0]:.5f}', f'{b[2]/b[0]:.5f}', b[3], str(b[4]), b[5]]) for k, b in bld.items() if b[0] >= 2))
    json.dump({'changed': True, 'ver': ver, 'pop': popym, 'rows': rows, 'cafes': len(cafes)}, open(f'{OUT}/version.json', 'w'))
    print('완료', ver, popym, rows, len(cafes))
