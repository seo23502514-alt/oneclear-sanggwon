# 원클리어 카페 상권분석

동네·지하철역·매장·건물 이름으로 검색하면 반경 안 카페·빵집·디저트, 업종 구성, 주민 대비 카페 수를 보여 주는 사이트입니다.

- 사이트: https://seo23502514-alt.github.io/oneclear-sanggwon/
- 카페 개업·폐업 레이더: https://seo23502514-alt.github.io/oneclear-sanggwon/radar/ (지자체 인허가 데이터, `docs/radar/`)
- 매주 월요일 밤 9시(한국 시간)에 GitHub가 공공데이터를 확인해 새 자료가 있으면 자동으로 갱신합니다.

## 지도 키 넣기
`docs/config.js` 파일을 열고 연필(편집) 버튼을 눌러 `NAVER_CLIENT_ID` 또는 `KAKAO_JS_KEY`에 키를 붙여 넣은 뒤 Commit changes를 누르세요.
(네이버 클라우드 플랫폼 Maps의 Web 서비스 URL에는 `https://seo23502514-alt.github.io` 를 등록합니다.)

## 데이터 출처
- 소상공인시장진흥공단 상가(상권)정보 (공공데이터포털)
- 행정안전부 주민등록 인구통계
- 국가철도공단 도시철도 역사정보 (철도데이터포털)
