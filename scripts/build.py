#!/usr/bin/env python3
"""원클리어 상권분석 데이터 빌드.
사용: python3 build.py <extract.txt> <pop.txt> <stations.json> <page.html> <outdir>
 - extract.txt : extract.js 결과(gzip 해제한 텍스트, #VER/#ROWS/#DONG/#CAFES/#GRID/#SWEET/#LM/#BLD 섹션)
 - pop.txt     : pop.js 결과 'POP|YYYY-MM|code8,pop,hh;...|END'
 - stations.json: 지금 사이트에 올라가 있는 stations.json (역은 연 1회만 바뀜)
 - page.html   : 지금 사이트 cafe-market.html (날짜·숫자 문구만 바꿔서 outdir/cafe-market.html로 저장)
"""
import json, math, collections, os, re, sys, shutil

ext, popf, stf, page, out = sys.argv[1:6]
raw = open(ext, encoding='utf-8').read()
sec, cur = {}, None
for line in raw.split('\n'):
    if line.startswith('#') and line[1:] in ('VER','ROWS','DONG','CAFES','GRID','SWEET','LM','FOOD','BLD'):
        cur = line[1:]; sec[cur] = []; continue
    if line: sec[cur].append(line)
ver = sec['VER'][0]; rows = int(sec['ROWS'][0])
dong = json.loads(sec['DONG'][0])
m = re.search(r'POP\|(\d{4}-\d{2})\|(.*)\|END', open(popf, encoding='utf-8').read())
popym = m.group(1); pop = {r.split(',')[0]: [int(r.split(',')[1]), int(r.split(',')[2])] for r in m.group(2).split(';')}

if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out + '/t')
sidos = sorted({d[1] for d in dong})
D = []
for d in dong:
    code, s, g, nm, n, la, lo, mj, cafe, f1, sub, br, roads = d
    p = pop.get(code, [0, 0])
    D.append([code, sidos.index(s), g, nm, la, lo, n, mj, cafe, f1, sub, {str(i): v for i, v in enumerate(br) if v}, [[r, c] for r, c in roads if c >= 2], p[0], p[1]])
D.sort(key=lambda x: x[0])
idx = {d[0]: i for i, d in enumerate(D)}
meta = {'v': ver, 'pop': popym, 'sidos': sidos, 'total': sum(d[6] for d in D), 'cafes': sum(d[8] for d in D),
        'mj': [sum(d[7][i] for d in D) for i in range(10)], 'popTotal': sum(d[13] for d in D)}
assert meta['total'] == rows, (meta['total'], rows)
json.dump({'meta': meta, 'd': D}, open(out + '/dongs.json', 'w'), ensure_ascii=False, separators=(',', ':'))

tile = lambda la, lo: f'{math.floor(la*2)}_{math.floor(lo*2)}'
ct = collections.defaultdict(list); names = []
for l in sec['CAFES']:
    code, la, lo, name, b, fl, addr = l.split('\t'); la = float(la); lo = float(lo)
    ct[tile(la, lo)].append([round(la*1e5), round(lo*1e5), name, int(b), fl, addr, code])
    names.append([name, round(la*1e5), round(lo*1e5), 'c', idx.get(code, -1)])
for k, v in ct.items(): json.dump(v, open(f'{out}/t/c{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
gt = collections.defaultdict(list)
for l in sec['GRID']:
    a = list(map(int, l.split(','))); gt[f'{math.floor(a[0]/500)}_{math.floor(a[1]/400)}'].append(a)
for k, v in gt.items(): open(f'{out}/t/g{k}.csv', 'w').write('\n'.join(','.join(map(str, r)) for r in v))
KIND = {'빵/도넛': 0, '아이스크림/빙수': 1, '떡/한과': 2}
SB = [r'파리바게|파리 바게', r'뚜레쥬르|뚜레주르', r'던킨', r'크리스피', r'배스킨|베스킨', r'설빙']
bt = collections.defaultdict(list)
for l in sec['SWEET']:
    code, la, lo, nm, sub, fl, addr = l.split('\t')
    if sub not in KIND: continue
    la = float(la); lo = float(lo); b = next((i for i, rx in enumerate(SB) if re.search(rx, nm)), -1)
    bt[tile(la, lo)].append([round(la*1e5), round(lo*1e5), nm, KIND[sub], b, fl, addr, code])
    names.append([nm, round(la*1e5), round(lo*1e5), 'b%d' % KIND[sub], idx.get(code, -1)])
for k, v in bt.items(): json.dump(v, open(f'{out}/t/b{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for l in sec.get('LM', []):
    code, la, lo, nm, sub, addr = l.split('\t')
    names.append([nm, round(float(la)*1e5), round(float(lo)*1e5), 'L:' + sub, idx.get(code, -1)])
json.dump(names, open(out + '/names.json', 'w'), ensure_ascii=False, separators=(',', ':'))
B = []
for l in sec['BLD']:
    sgg, nm, n, la, lo, addr, cafes, code = l.split('\t')
    B.append([nm, round(float(la)*1e5), round(float(lo)*1e5), int(n), int(cafes), idx.get(code, -1), addr])
freq = collections.Counter(b[0] for b in B)
junk = re.compile(r'^(일부|일부호|전체|본관|신관|별관|상가|상가동|주택|단독|빌라|근린생활시설|근생|공장|창고|지하|지상|\d+|[A-Za-z]|.{0,1})$|^\d+[동호층]$|^제?\d+[동호]$')
B = [b for b in B if b[3] >= 3 and not junk.match(b[0].strip()) and freq[b[0]] <= 40]
B.sort(key=lambda x: -x[3])
json.dump(B, open(out + '/buildings.json', 'w'), ensure_ascii=False, separators=(',', ':'))
kt = collections.defaultdict(list)
for nm, la, lo, n, c, di, addr in B:
    if n >= 8: kt[tile(la/1e5, lo/1e5)].append([la, lo, nm, n])
for k, v in kt.items(): json.dump(v, open(f'{out}/t/k{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
# 음식점 (카페·빵집·디저트 제외) — 0.25도 타일
mids, subs = [], []
ft = collections.defaultdict(list)
for l in sec.get('FOOD', []):
    la, lo, nm, mid, sub = l.split('\t'); la = float(la); lo = float(lo)
    if mid not in mids: mids.append(mid)
    if sub not in subs: subs.append(sub)
    ft[f'{math.floor(la*4)}_{math.floor(lo*4)}'].append([round(la*1e5), round(lo*1e5), nm, mids.index(mid), subs.index(sub)])
for k, v in ft.items(): json.dump(v, open(f'{out}/t/r{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
meta['foodMids'] = mids; meta['foodSubs'] = subs
json.dump({'meta': meta, 'd': D}, open(out + '/dongs.json', 'w'), ensure_ascii=False, separators=(',', ':'))
shutil.copy(stf, out + '/stations.json')

# 페이지 문구 날짜·숫자 갱신
h = open(page, encoding='utf-8').read()
y, mo, dd = ver[:4], int(ver[4:6]), int(ver[6:8])
py, pm = popym.split('-')
h = re.sub(r'상가\(상권\)정보 \d{4}년 \d{1,2}월 \d{1,2}일 기준', f'상가(상권)정보 {y}년 {mo}월 {dd}일 기준', h)
h = re.sub(r'주민등록 인구통계 \d{4}년 \d{1,2}월 말 기준', f'주민등록 인구통계 {py}년 {int(pm)}월 말 기준', h)
h = re.sub(r'전국 상가 \d+만 곳', f'전국 상가 {round(rows/10000)}만 곳', h)
open(out + '/cafe-market.html', 'w', encoding='utf-8').write(h)
files = sorted(['dongs.json', 'names.json', 'buildings.json', 'stations.json'] + ['t/' + f for f in os.listdir(out + '/t')])
json.dump(files, open(out + '/_files.json', 'w'))
print(json.dumps({'ver': ver, 'pop': popym, 'stores': rows, 'cafes': meta['cafes'], 'dongs': len(D), 'files': len(files)}, ensure_ascii=False))
