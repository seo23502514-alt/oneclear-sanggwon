# 원클리어 카페 상권분석

동네·지하철역·매장·건물 이름으로 검색하면 반경 안 카페·빵집·디저트, 업종 구성, 주민 대비 카페 수, 관공서·시니어클럽 운영 매장, 손익 계산을 보여 주는 사이트입니다. 서울은 상권별 커피 매출·유동인구·직장인구도 함께 나옵니다.

- 사이트: https://seo23502514-alt.github.io/oneclear-sanggwon/
- 카페 개업·폐업 레이더: https://seo23502514-alt.github.io/oneclear-sanggwon/radar/ (지자체 인허가 데이터, `docs/radar/`)
- 카페 장비 시각가이드: https://seo23502514-alt.github.io/oneclear-sanggwon/equipment/ (매장 조건별 장비 구성 분석 + 장비 사전, `docs/equipment/`)
- 카페 입찰 레이더: https://seo23502514-alt.github.io/oneclear-sanggwon/bids/ (나라장터 오픈API 매일 2회 + 관공서·온비드 공고 매일 검색, `docs/bids/`)
- 매일 밤 9시 3분(상권진단)과 10시 13분(개폐업 레이더, 한국 시간)에 GitHub가 공공데이터를 확인해 새 자료가 있으면 자동으로 갱신합니다. 입찰 레이더는 매일 오전 6시 47분·오후 1시 47분(나라장터)과 오전 7시 23분(관공서·온비드)에 갱신합니다.

## 지도 키 넣기
`docs/config.js` 파일을 열고 연필(편집) 버튼을 눌러 `NAVER_CLIENT_ID` 또는 `KAKAO_JS_KEY`에 키를 붙여 넣은 뒤 Commit changes를 누르세요.
(네이버 클라우드 플랫폼 Maps의 Web 서비스 URL에는 `https://seo23502514-alt.github.io` 를 등록합니다.)

## 데이터 출처
- 소상공인시장진흥공단 상가(상권)정보 (공공데이터포털, 분기)
- 행정안전부 주민등록 인구통계 (월)
- 통계청 전국사업체조사 — 행정동별 사업체 종사자 수 (SGIS 오픈API, 연 1회)
- 서울시 상권분석서비스 — 상권별 추정매출·유동인구·직장인구 (서울 열린데이터광장 OpenAPI, 분기)
- 국가철도공단 도시철도 역사정보 (철도데이터포털)
- 지방행정 인허가 데이터 — 휴게음식점·제과점 개업·폐업 (개폐업 레이더)
- 조달청 나라장터 입찰공고정보서비스 (입찰 레이더)

## 저장소 비밀값 (Settings → Secrets and variables → Actions)
| 이름 | 쓰는 곳 | 받는 곳 |
|---|---|---|
| `SGIS_KEY`, `SGIS_SECRET` | 동네 직장인(종사자) 수 | 통계청 SGIS 인증키발급센터 (서비스 ID / 보안 Key) |
| `SEOUL_KEY` | 서울 상권 매출·유동인구·직장인구 | 서울 열린데이터광장 Open API 인증키 |
| `G2B_KEY` | 입찰 레이더 나라장터 공고 | 공공데이터포털 (아래 참고) |

키가 없거나 해당 사이트가 응답하지 않으면 그 자료만 이전 값을 그대로 쓰고 나머지는 계속 갱신됩니다.

## 입찰 레이더 인증키 넣기 (한 번만)
1. 공공데이터포털(data.go.kr)에서 「조달청_나라장터 입찰공고정보서비스」 활용신청 (자동 승인)
2. 마이페이지 → 개발계정 → 일반 인증키(Encoding 또는 Decoding) 복사
3. 이 저장소 Settings → Secrets and variables → Actions → New repository secret → 이름 `G2B_KEY`, 값에 키 붙여 넣기
4. Actions → 「카페 입찰 레이더 매일 갱신」 → Run workflow (처음 한 번은 한 달 치를 받습니다)
