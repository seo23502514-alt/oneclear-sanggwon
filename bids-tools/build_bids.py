"""나라장터 카페 관련 입찰공고 수집 → docs/bids/data.json

조달청 '나라장터 입찰공고정보서비스'(공공데이터포털 오픈API)를 공고명 키워드로 조회합니다.
환경변수 G2B_KEY 에 공공데이터포털 인증키(Encoding·Decoding 둘 다 됨)를 넣어야 합니다.

사용: python bids-tools/build_bids.py docs/bids/data.json [--days N]
"""
import json, os, re, sys, time, urllib.parse
from datetime import datetime, timedelta, timezone

import requests

KST = timezone(timedelta(hours=9))
BASES = [
    "https://apis.data.go.kr/1230000/ad/BidPublicInfoService",   # 차세대 나라장터(2025~)
    "https://apis.data.go.kr/1230000/BidPublicInfoService05",    # 예전 주소(혹시 몰라 두 번째로 시도)
]
OPS = {  # 업무 구분: 검색조건 조회 오퍼레이션
    "물품": "getBidPblancListInfoThngPPSSrch",
    "용역": "getBidPblancListInfoServcPPSSrch",
    "공사": "getBidPblancListInfoCnstwkPPSSrch",
}
# 공고명에 들어가면 가져오는 낱말
KEYWORDS = ["커피", "원두", "카페", "에스프레소", "제빙기", "바리스타", "매점", "자판기", "베이커리", "제과"]
# 걸러 낼 낱말(카페트, 원두막 같은 동음이의)
NOISE = re.compile(r"카페트|카펫|원두막|원두정|제과점\s*위생점검|매점매석|카페인|카페리|키즈\s*카페|규제과학|교복|생리대")
KEEP_DAYS_AFTER_CLOSE = 7     # 마감 뒤 며칠 더 보여 줄지
MAX_AGE_DAYS = 60             # 공고일로부터 최대 보관 일수


def category(title, kind):
    t = title
    if re.search(r"머신|기계|제빙기|에스프레소|그라인더|자판기|장비|기기|냉장|쇼케이스|오븐|블렌더|정수기", t):
        return "장비"
    if re.search(r"운영|위탁|임대|사용\s*허가|사용수익|대부|입점|모집|선정", t):
        return "운영·임대"
    if kind == "공사" or re.search(r"조성|리모델링|인테리어|공사|설치", t):
        return "공사·인테리어"
    if re.search(r"교육|바리스타|강사|과정|양성", t):
        return "교육"
    if re.search(r"원두|커피|차류|음료|티백|시럽|파우더|식자재|재료|베이커리|제과|빵", t):
        return "원두·재료"
    return "기타"


def service_key():
    k = os.environ.get("G2B_KEY", "").strip()
    return urllib.parse.unquote(k) if "%" in k else k


def call(base, op, params):
    for attempt in range(3):
        try:
            r = requests.get(f"{base}/{op}", params=params, timeout=40)
        except requests.RequestException as e:
            err = str(e); time.sleep(3 * (attempt + 1)); continue
        txt = r.text.strip()
        if r.status_code == 404:
            return None, "404"
        if txt.startswith("<"):  # 인증키 오류 등은 XML로 옵니다
            m = re.search(r"<(?:returnAuthMsg|errMsg|resultMsg)>([^<]+)<", txt)
            err = m.group(1) if m else txt[:200]
            if "LIMITED" in err or "TIMEOUT" in err.upper():
                time.sleep(5); continue
            return None, err
        try:
            j = r.json()
        except ValueError:
            err = txt[:200]; time.sleep(2); continue
        resp = j.get("response", j)
        head = resp.get("header", {})
        if str(head.get("resultCode", "00")) not in ("00", "0"):
            return None, f"{head.get('resultCode')} {head.get('resultMsg')}"
        body = resp.get("body", {}) or {}
        items = body.get("items") or []
        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        return (items, int(body.get("totalCount") or 0)), None
    return None, err


def fetch(key, start, end):
    """start~end(KST) 사이 게시된 공고를 키워드·업무별로 모두 받기. 7일씩 끊어서 조회."""
    out, errors, base_ok = {}, [], None
    chunks, s = [], start
    while s < end:
        e = min(s + timedelta(days=7), end)
        chunks.append((s, e)); s = e
    for kind, op in OPS.items():
        for kw in KEYWORDS:
            for s, e in chunks:
                page = 1
                while True:
                    params = {"serviceKey": key, "type": "json", "numOfRows": 100, "pageNo": page,
                              "inqryDiv": 1, "inqryBgnDt": s.strftime("%Y%m%d%H%M"),
                              "inqryEndDt": e.strftime("%Y%m%d%H%M"), "bidNtceNm": kw}
                    res, err = None, None
                    for base in ([base_ok] if base_ok else BASES):
                        res, err = call(base, op, params)
                        if res is not None:
                            base_ok = base; break
                    if res is None:
                        errors.append(f"{kind}/{kw}: {err}"); break
                    items, total = res
                    for it in items:
                        rec = record(it, kind, kw)
                        if rec:
                            prev = out.get(rec["id"])
                            if prev:  # 같은 공고가 여러 키워드에 걸리면 키워드만 합침
                                prev["kw"] = sorted(set(prev["kw"]) | set(rec["kw"]))
                            else:
                                out[rec["id"]] = rec
                    if page * 100 >= total or not items:
                        break
                    page += 1
                    time.sleep(0.2)
                time.sleep(0.15)
    return out, errors


def num(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def record(it, kind, kw):
    title = (it.get("bidNtceNm") or "").strip()
    cleaned = NOISE.sub("", title)
    if not title or not any(k in cleaned for k in KEYWORDS):  # 카페트·원두막만 걸린 공고는 버림
        return None
    no, ordv = it.get("bidNtceNo") or "", it.get("bidNtceOrd") or "000"
    if not no:
        return None
    price = num(it.get("asignBdgtAmt")) or num(it.get("presmptPrce"))
    url = it.get("bidNtceDtlUrl") or it.get("bidNtceUrl") or ""
    return {
        "id": f"{no}-{ordv}",
        "no": no, "ord": ordv,
        "title": title,
        "org": it.get("ntceInsttNm") or "",
        "demand": it.get("dminsttNm") or "",
        "kind": kind,
        "cat": category(title, kind),
        "type": it.get("ntceKindNm") or "",
        "method": it.get("cntrctCnclsMthdNm") or "",
        "posted": (it.get("bidNtceDt") or "")[:16],
        "close": (it.get("bidClseDt") or "")[:16],
        "open": (it.get("opengDt") or "")[:16],
        "price": price,
        "region": it.get("prtcptPsblRgnNm") or "",
        "url": url,
        "kw": [kw],
        "src": "나라장터",
    }


def parse_dt(s):
    try:
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    except (TypeError, ValueError):
        return None


def main():
    out_path = sys.argv[1]
    days = 3
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    now = datetime.now(KST)
    old = {"items": []}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            old = json.load(f)
    if not old.get("items"):
        days = max(days, 30)  # 처음엔 한 달 치
    key = service_key()
    if not key:
        print("G2B_KEY 가 없습니다. 저장소 Settings → Secrets → Actions 에 G2B_KEY 를 넣어 주세요.")
        sys.exit(2)

    got, errors = fetch(key, now - timedelta(days=days), now)
    print(f"받은 공고 {len(got)}건, 오류 {len(errors)}건")
    for e in errors[:10]:
        print("  ", e)
    if not got and errors and len(errors) >= len(OPS) * len(KEYWORDS):
        print("모든 조회가 실패했습니다. 인증키·활용신청 상태를 확인해 주세요.")
        sys.exit(1)

    first_seen = {it["id"]: it.get("seen", now.strftime("%Y-%m-%d")) for it in old.get("items", [])}
    merged = {it["id"]: it for it in old.get("items", [])}
    for k, rec in got.items():
        rec["seen"] = first_seen.get(k, now.strftime("%Y-%m-%d"))
        merged[k] = rec
    # 같은 공고번호의 이전 차수(정정 전)는 지우기
    latest = {}
    for it in merged.values():
        if it["no"] not in latest or it["ord"] > latest[it["no"]]["ord"]:
            latest[it["no"]] = it
    keep = []
    for it in latest.values():
        close, posted = parse_dt(it.get("close")), parse_dt(it.get("posted"))
        if close and close < now - timedelta(days=KEEP_DAYS_AFTER_CLOSE):
            continue
        if posted and posted < now - timedelta(days=MAX_AGE_DAYS):
            continue
        keep.append(it)
    keep.sort(key=lambda x: (x.get("posted") or ""), reverse=True)
    data = {"updated": now.strftime("%Y-%m-%d %H:%M"), "keywords": KEYWORDS,
            "errors": len(errors), "items": keep}
    if "--dry" in sys.argv:
        print(json.dumps(keep[:5], ensure_ascii=False, indent=1)); return
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장 {len(keep)}건 → {out_path}")


if __name__ == "__main__":
    main()
