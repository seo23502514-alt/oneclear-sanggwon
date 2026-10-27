#!/usr/bin/env python3
"""서울시 상권분석서비스 자료가 data.go.kr에서 어떤 파일로 받아지는지 확인 (GitHub Actions에서 수동 실행)"""
import re, io, zipfile, csv, requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
B = "https://www.data.go.kr"
for pk in list(range(15147218, 15147266)) + [15147350, 15147351]:
    try:
        h = S.get(f"{B}/data/{pk}/fileData.do", timeout=40).text
    except Exception as e:
        print(pk, "ERR", e); continue
    t = re.search(r'<title>(.*?)</title>', h, re.S); t = t.group(1).strip() if t else ''
    t2 = re.search(r'class="title"[^>]*>\s*([^<]{4,120})', h); t2 = t2.group(1).strip() if t2 else ''
    if '상권' not in (t + t2): print(pk, '-', t[:60]); continue
    dps = [p for p in re.findall(r"fn_fileDataDown\(\s*'%s'\s*,\s*'([^']*)'" % pk, h) if p.strip()]
    print('\n##', pk, t2 or t, 'files:', len(dps), flush=True)
    for dp in dps[:1]:
        try:
            r = S.post(f"{B}/tcs/dss/selectFileDataDownload.do?recommendDataYn=Y", data={"publicDataPk": str(pk), "publicDataDetailPk": dp},
                       headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"{B}/data/{pk}/fileData.do"}, timeout=40).json()
            info = r.get("dataSetFileDetailInfo", {}); nm = info.get("dataNm"); print('  파일:', nm, info.get('atchFileExtsn'), info.get('fileSize'))
            url = f"{B}/cmm/cmm/fileDownload.do?atchFileId={r['atchFileId']}&fileDetailSn={r['fileDetailSn']}&dataNm={requests.utils.quote(nm or '')}"
            d = S.get(url, headers={"Referer": f"{B}/data/{pk}/fileData.do"}, timeout=120).content
            print('  크기', len(d), d[:4])
            if d[:2] == b'PK':
                z = zipfile.ZipFile(io.BytesIO(d)); print('  zip:', z.namelist()[:5]); d = z.read(z.namelist()[0])
            for enc in ('utf-8-sig', 'cp949'):
                try: txt = d.decode(enc); break
                except Exception: pass
            rows = list(csv.reader(io.StringIO(txt)))
            print('  행', len(rows)); print('  머리', rows[0][:60]); print('  예', rows[1][:60])
            qs = sorted({r[0] for r in rows[1:] if r})[-3:]; print('  분기 끝', qs)
            if any('서비스_업종' in c for c in rows[0]):
                i = [k for k, c in enumerate(rows[0]) if '서비스_업종_코드_명' in c]
                if i: print('  업종 예', sorted({r[i[0]] for r in rows[1:] if r})[:80])
        except Exception as e:
            print('  ERR', e)
