#!/usr/bin/env python3
"""SGIS 사업체통계 API 시험: 키가 되는지, 최신 연도와 응답 모양을 확인한다. (GitHub Actions에서 수동 실행)"""
import json, os, sys, time
import requests

B = "https://sgisapi.kostat.go.kr/OpenAPI3"
key, sec = os.environ.get("SGIS_KEY", ""), os.environ.get("SGIS_SECRET", "")
print("키 있음:", bool(key), "보안키 있음:", bool(sec))
if not key or not sec: sys.exit("SGIS_KEY / SGIS_SECRET 비밀값이 없습니다")
a = requests.get(f"{B}/auth/authentication.json", params={"consumer_key": key, "consumer_secret": sec}, timeout=30).json()
print("인증:", a.get("errCd"), a.get("errMsg"))
tok = a["result"]["accessToken"]

def get(path, **p):
    p["accessToken"] = tok
    r = requests.get(f"{B}/{path}", params=p, timeout=60).json()
    return r

# 최신 연도 찾기
latest = None
for y in range(time.localtime().tm_year, 2014, -1):
    r = get("stats/company.json", year=str(y))
    print("연도", y, r.get("errCd"), r.get("errMsg"), (r.get("result") or [])[:1])
    if r.get("errCd") == 0 and r.get("result"):
        latest = y; break
print("최신 연도:", latest)
r = get("stats/company.json", year=str(latest), adm_cd="11", low_search="2")
res = r.get("result") or []
print("서울 low_search=2:", r.get("errCd"), len(res), res[:3])
r = get("stats/company.json", year=str(latest), adm_cd="31", low_search="1")
res = r.get("result") or []
print("경기 low_search=1:", r.get("errCd"), len(res), res[:3])
g = next((x for x in res if "광명" in (x.get("adm_nm") or "")), None)
print("광명:", g)
if g:
    r = get("stats/company.json", year=str(latest), adm_cd=g["adm_cd"], low_search="1")
    print("광명 동:", r.get("errCd"), r.get("result"))
r = get("addr/stage.json", cd="31")
print("주소 단계:", r.get("errCd"), (r.get("result") or [])[:3])
