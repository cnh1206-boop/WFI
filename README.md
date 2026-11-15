# WFI 주식 브리핑

GitHub Pages 대시보드는 보유 종목, 세계 주요 지수, 최신 뉴스 원문과 보유기업 공시를 보여줍니다. 보유 종목명과 티커만 공개하며 수량·매입가는 저장하지 않습니다.

## 자동 업데이트

- GitHub Actions가 매일 한국 시간 01시, 04시, 07시, 10시, 13시, 16시, 19시, 22시에 `update.py`를 실행합니다. Actions 탭에서 `Auto Update Portfolio and News`를 열고 **Run workflow**로 수동 실행할 수도 있습니다.
- 종목과 지수 시세는 Yahoo Finance를 통해 가져옵니다. 거래소 휴장일이나 데이터 제공 지연 때는 가장 최근에 제공된 거래일 값이 표시될 수 있습니다.
- 뉴스는 Google News RSS 검색 결과와 원문 링크를 수집합니다. RSS 기사에는 자동 생성한 사실이나 매수·매도 권고를 덧붙이지 않습니다.
- 한국 상장 보유기업의 DART 공시 자동 수집은 선택 사항입니다. 사용하려면 [OpenDART](https://opendart.fss.or.kr/)에서 API 키를 발급받고 저장소의 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `OPEN_DART_API_KEY`로, 값에 발급 키를 입력하세요. 키를 등록하지 않아도 지수·시세·뉴스는 갱신됩니다.

보유 종목 목록은 `holdings.json`에서 수정합니다. 종목을 추가하거나 티커를 변경할 때 Yahoo Finance 심볼도 함께 확인하세요.
