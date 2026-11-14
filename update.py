from datetime import datetime, timedelta, timezone
import json
import os
import traceback
from google import genai

client = genai.Client()


def get_kst_now_str():
  kst = timezone(timedelta(hours=9))
  return datetime.now(kst).strftime("%Y-%m-%d %H:%M KST")


def fetch_news():
  prompt = """전 세계 2차전지, 반도체, 거시경제, 환율·원자재 산업의 최신 핵심 뉴스 6건과, 전 세계 주요 경제 유튜버(All-In Podcast, Patrick Boyle, Joseph Carlson, Tom Nash 등) 및 월가 주요 인사(제이미 다이먼, 레이 달리오, 스탠리 드러켄밀러, 캐시 우드, 연준 인사 등)의 최신 발언·시장 전망 3건을 합쳐 총 9건을 선정해서 한국어로 브리핑해줘.

반드시 아래 JSON 배열 형식으로만 응답해줘. 마크다운 백틱(```json)이나 다른 설명 텍스트는 절대 포함하지 마.

[
  {
    "id": 1,
    "title": "핵심 뉴스 제목 (월가·유튜버 발언의 경우 '[인물/채널명] 핵심 발언 요지' 형태로 작성)",
    "category": "반드시 다음 5개 중 하나만 정확히 입력: 2차전지·소재, 반도체·AI, 세계증시·경제, 환율·금리·원자재, 월가·유튜버 인사이트",
    "keyword": "반드시 다음 4개 중 가장 관련 깊은 것 하나만 정확히 입력: 미국FOMC, 리튬반등, HBM4, 유럽CBAM",
    "region": "미국, 유럽, 아시아, 글로벌 중 택1",
    "media": "일반 뉴스는 Bloomberg, Reuters, WSJ, FT, CNBC 중 택1 / 발언 요약은 YouTube, Wall Street, Podcast 중 택1",
    "date": "오늘",
    "summary1": "첫 번째 핵심 요약 문장 (발언 배경 및 핵심 주장)",
    "summary2": "두 번째 핵심 요약 문장 (구체적 근거 수치 또는 언급된 섹터·종목)",
    "summary3": "세 번째 핵심 요약 문장 (향후 전망 및 리스크 요인)",
    "insight": "이 뉴스 또는 발언이 개인 투자자 포트폴리오(반도체·배터리·지수)에 주는 핵심 시사점 1~2문장",
    "scraped": false
  }
]"""

  try:
    print("Gemini API 호출 시작...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    print("Gemini API 호출 완료!")

    text = response.text.strip()
    if text.startswith("```json"):
      text = text[7:]
    if text.startswith("```"):
      text = text[3:]
    if text.endswith("```"):
      text = text[:-3]
    text = text.strip()

    articles = json.loads(text)

    for idx, item in enumerate(articles, start=1):
      item["id"] = idx
      item["scraped"] = False
      item.setdefault("category", "세계증시·경제")
      item.setdefault("keyword", "미국FOMC")
      item.setdefault("region", "글로벌")
      item.setdefault("media", "Bloomberg")
      item.setdefault("date", "오늘")
      item.setdefault("summary1", "세부 내용 요약")
      item.setdefault("summary2", "시장 동향 모니터링 필요")
      item.setdefault("summary3", "관련 밸류체인 영향 주시")
      item.setdefault("insight", "거시경제 및 산업 수급 변화에 유의해야 합니다.")

    return articles
  except Exception as e:
    print("API 호출 중 상세 오류 발생:")
    traceback.print_exc()
    return []


def main():
  print("뉴스 업데이트 스크립트 실행 중...")
  news_list = fetch_news()

  data = {"updated_at": get_kst_now_str(), "articles": news_list}

  with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

  print("news.json 파일 저장 완료!")


if __name__ == "__main__":
  main()
