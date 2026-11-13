import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

# 1. Google News RSS에서 글로벌 핵심 키워드 뉴스 수집
RSS_FEEDS = [
    ("반도체·AI", "HBM4", "글로벌", "https://news.google.com/rss/search?q=semiconductor+AI+HBM+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("2차전지·소재", "리튬반등", "글로벌", "https://news.google.com/rss/search?q=lithium+EV+battery+supply+chain+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("세계증시·경제", "미국FOMC", "미국", "https://news.google.com/rss/search?q=Federal+Reserve+FOMC+stock+market+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("환율·금리·원자재", "유럽CBAM", "글로벌", "https://news.google.com/rss/search?q=macro+economy+interest+rate+commodities+when:1d&hl=en-US&gl=US&ceid=US:en"),
]

raw_articles = []
for category, keyword, region, url in RSS_FEEDS:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item')[:2]:
                title = item.find('title').text
                source_el = item.find('source')
                media = source_el.text if source_el is not None else "Global News"
                raw_articles.append({
                    "category": category,
                    "keyword": keyword,
                    "region": region,
                    "media": media,
                    "raw_title": title
                })
    except Exception as e:
        print(f"RSS fetch error ({category}): {e}")

# 2. Gemini API로 한국어 3줄 요약 및 투자 시사점 생성
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

prompt = f"""
다음은 오늘 수집된 글로벌 경제/산업 주요 외신 헤드라인 목록입니다.
각 기사를 한국 투자자 관점에서 분석하여 반드시 아래 JSON 배열 형식으로만 응답하세요. (마크다운 코드블록 없이 순수 JSON만 출력)

입력 데이터:
{json.dumps(raw_articles, ensure_ascii=False)}

출력 형식 예시:
[
  {{
    "id": 1,
    "title": "자연스러운 한국어 기사 제목",
    "category": "입력된 category 그대로 유지",
    "keyword": "입력된 keyword 그대로 유지",
    "region": "입력된 region 그대로 유지",
    "media": "입력된 media 그대로 유지",
    "date": "오늘 업데이트",
    "summary1": "핵심 요약 첫 번째 줄 (간결한 명사형 종결)",
    "summary2": "핵심 요약 두 번째 줄 (간결한 명사형 종결)",
    "summary3": "핵심 요약 세 번째 줄 (간결한 명사형 종결)",
    "insight": "국내 주식 및 산업에 미치는 핵심 투자 시사점 1문장",
    "scraped": false
  }}
]
"""

response = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt,
)

result_text = response.text.strip()
if result_text.startswith("```json"):
    result_text = result_text[7:]
if result_text.startswith("```"):
    result_text = result_text[3:]
if result_text.endswith("```"):
    result_text = result_text[:-3]

parsed_news = json.loads(result_text.strip())
for idx, item in enumerate(parsed_news, start=1):
    item["id"] = idx

output = {
    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
    "articles": parsed_news
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("news.json successfully updated!")
