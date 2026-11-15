from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

import yfinance as yf

KST = timezone(timedelta(hours=9))
with open("holdings.json", encoding="utf-8") as holdings_file:
    HOLDINGS = json.load(holdings_file)["holdings"]
MARKETS = [
    {"name": "S&P 500", "symbol": "^GSPC", "region": "미국"},
    {"name": "NASDAQ 종합", "symbol": "^IXIC", "region": "미국"},
    {"name": "미국 10년물 국채금리", "symbol": "^TNX", "region": "미국", "currency": "PERCENT"},
    {"name": "필라델피아 반도체지수", "symbol": "^SOX", "region": "미국"},
    {"name": "다우존스", "symbol": "^DJI", "region": "미국"},
    {"name": "코스피", "symbol": "^KS11", "region": "한국"},
    {"name": "코스닥", "symbol": "^KQ11", "region": "한국"},
    {"name": "니케이 225", "symbol": "^N225", "region": "일본"},
    {"name": "항셍", "symbol": "^HSI", "region": "홍콩"},
    {"name": "유로스톡스 50", "symbol": "^STOXX50E", "region": "유럽"},
]
DART_ETF_CODES = {"453850", "364980", "0131V0", "493810", "0177N0"}


def now_kst():
    return datetime.now(KST)


def fetch_json(url, params=None):
    if params:
        url = url + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "WFI-Portfolio-Briefing/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_quote(item):
    try:
        history = yf.Ticker(item["symbol"]).history(period="5d", interval="1d", auto_adjust=False)
        closes = history["Close"].dropna()
        if closes.empty:
            raise ValueError("시세 데이터 없음")
        price = float(closes.iloc[-1])
        previous = float(closes.iloc[-2]) if len(closes) > 1 else price
        return {
            **item,
            "price": round(price, 4),
            "change": round(price - previous, 4),
            "change_percent": round((price - previous) / previous * 100, 4) if previous else 0,
            "currency": item.get("currency") or ("USD" if item["market"] == "US" else "POINTS" if item["market"] == "INDEX" else "KRW"),
            "as_of": str(closes.index[-1].date()),
            "error": None,
        }
    except Exception as exc:
        print(f'시세 조회 실패: {item["name"]} ({item["symbol"]}): {exc}')
        return {
            **item, "price": None, "change": None, "change_percent": None,
            "currency": item.get("currency") or ("USD" if item["market"] == "US" else "POINTS" if item["market"] == "INDEX" else "KRW"),
            "as_of": None, "error": str(exc),
        }


def fetch_market_indices():
    return [fetch_quote({**item, "ticker": item["symbol"], "market": "INDEX"}) for item in MARKETS]


def clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(unescape(value).split())


def fetch_rss(query, limit=5):
    url = "https://news.google.com/rss/search?" + urlencode(
        {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    )
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; WFI-Briefing/1.0)"})
        with urlopen(request, timeout=30) as response:
            root = ET.fromstring(response.read())
        entries = []
        for item in root.findall("./channel/item")[:limit]:
            title = clean_html(item.findtext("title", ""))
            link = item.findtext("link", "").strip()
            source_node = item.find("source")
            source = clean_html(source_node.text if source_node is not None else "Google 뉴스")
            description = clean_html(item.findtext("description", ""))
            published = item.findtext("pubDate", "")
            if title and link:
                entries.append({"title": title, "source_url": link, "source": source,
                                "description": description, "published_at": published})
        return entries
    except Exception as exc:
        print(f"뉴스 RSS 조회 실패 ({query}): {exc}")
        return []


def fetch_news():
    searches = [
        ("global stock market today S&P 500 Nasdaq", "세계증시·경제", "글로벌", []),
        ("global markets interest rates currency economy", "세계증시·경제", "글로벌", []),
        ("POSCO Holdings OR POSCO홀딩스 stock news", "보유종목 뉴스", "한국", ["005490"]),
        ("SK hynix OR SK하이닉스 stock news", "보유종목 뉴스", "한국", ["000660"]),
        ("IonQ stock news", "보유종목 뉴스", "미국", ["IONQ"]),
        ("TIGER 2차전지TOP10 OR lithium battery Korea ETF", "보유종목 뉴스", "한국", ["364980"]),
        ("명신산업 OR 선바이오 OR 두산퓨얼셀 news", "보유종목 뉴스", "한국", ["009900", "067370", "336260"]),
        ("미국 우주항공 ETF AI 빅테크 covered call 한국", "보유종목 뉴스", "글로벌", ["0131V0", "493810"]),
    ]
    articles, seen = [], set()
    for query, category, region, related in searches:
        for entry in fetch_rss(query, limit=4):
            if entry["source_url"] in seen:
                continue
            seen.add(entry["source_url"])
            articles.append({
                "id": len(articles) + 1,
                "title": entry["title"],
                "category": category,
                "keyword": "보유종목" if related else "세계시장",
                "region": region,
                "media": entry["source"],
                "date": entry["published_at"] or now_kst().strftime("%Y-%m-%d"),
                "summary1": entry["title"],
                "summary2": entry["description"] or "기사 원문을 열어 세부 내용을 확인하세요.",
                "summary3": "제목과 출처를 기준으로 수집했습니다. 기사 원문에서 사실관계와 맥락을 확인하세요.",
                "insight": "관련 보유 종목 또는 시장 동향 뉴스입니다. 투자 판단 전 원문과 공시를 확인하세요.",
                "source_url": entry["source_url"],
                "related_tickers": related,
                "scraped": False,
            })
    return articles[:30]


def fetch_dart_disclosures():
    api_key = os.getenv("OPEN_DART_API_KEY")
    if not api_key:
        print("OPEN_DART_API_KEY 미설정: 공시 수집을 건너뜁니다.")
        return []
    try:
        corp_url = "https://opendart.fss.or.kr/api/corpCode.xml?" + urlencode({"crtfc_key": api_key})
        request = Request(corp_url, headers={"User-Agent": "WFI-Portfolio-Briefing/1.0"})
        with urlopen(request, timeout=40) as response:
            archive = zipfile.ZipFile(BytesIO(response.read()))
        xml_name = next(name for name in archive.namelist() if name.endswith(".xml"))
        root = ET.fromstring(archive.read(xml_name))
        code_map = {}
        for node in root.findall("list"):
            stock_code = (node.findtext("stock_code") or "").strip()
            corp_code = (node.findtext("corp_code") or "").strip()
            if stock_code and corp_code:
                code_map[stock_code] = corp_code
    except Exception as exc:
        print(f"DART 기업코드 목록 조회 실패: {exc}")
        return []

    start_date = (now_kst() - timedelta(days=14)).strftime("%Y%m%d")
    end_date = now_kst().strftime("%Y%m%d")
    disclosures = []
    for holding in HOLDINGS:
        if holding["market"] != "KR" or holding["ticker"] in DART_ETF_CODES:
            continue
        corp_code = code_map.get(holding["ticker"])
        if not corp_code:
            continue
        try:
            result = fetch_json("https://opendart.fss.or.kr/api/list.json", {
                "crtfc_key": api_key, "corp_code": corp_code,
                "bgn_de": start_date, "end_de": end_date,
                "page_count": 100, "sort": "date", "sort_mth": "desc",
            })
            if result.get("status") not in ("000", "013"):
                print(f'DART 응답: {holding["name"]}: {result.get("message")}')
                continue
            for row in result.get("list", []):
                receipt_no = row.get("rcept_no", "")
                disclosures.append({
                    "company": holding["name"], "ticker": holding["ticker"],
                    "title": row.get("report_nm", ""), "date": row.get("rcept_dt", ""),
                    "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
                    "receipt_no": receipt_no,
                })
            time.sleep(0.15)
        except Exception as exc:
            print(f'DART 공시 조회 실패: {holding["name"]}: {exc}')
    disclosures.sort(key=lambda item: item["date"], reverse=True)
    return disclosures[:50]


def main():
    updated_at = now_kst().strftime("%Y-%m-%d %H:%M KST")
    portfolio = {
        "updated_at": updated_at,
        "indices": fetch_market_indices(),
        "holdings": [fetch_quote(holding) for holding in HOLDINGS],
    }
    news = {"updated_at": updated_at, "articles": fetch_news()}
    dart_key_configured = bool(os.getenv("OPEN_DART_API_KEY"))
    disclosures = {
        "updated_at": updated_at,
        "configured": dart_key_configured,
        "items": fetch_dart_disclosures(),
    }
    for filename, data in (("portfolio.json", portfolio), ("news.json", news),
                           ("disclosures.json", disclosures)):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"{filename} 저장 완료")


if __name__ == "__main__":
    main()
