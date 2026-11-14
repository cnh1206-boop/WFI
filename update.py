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
  prompt = """전 세계 2차전지, 반도체, 거시경제, 환율·원자재 산업과 관련된 최신 핵심 외신 소식을 6~8가지 선정해서 한국어로 브리핑해줘.
반드시 아래 JSON 배열 형식으로만 응답해줘. 마크다운 백틱(```json)이나 다른 설명 텍스트는 절대 포함하지 마.

[
  {
    "id": 1,
    "title": "핵심 뉴스 제목",
    "category": "반드시 다음 4개 중 하나만 정확히 입력: 2차전지·소재, 반도체·AI, 세계증시·경제, 환율·금리·원자재",
    "keyword": "반드시 다음 4개 중 가장 관련 깊은 것 하나만 정확히 입력: 미국FOMC, 리튬반등, HBM4, 유럽CBAM",
    "region": "미국, 유럽, 아시아, 글로벌 중 택1",
    "media": "Bloomberg, Reuters, WSJ, FT, CNBC 중 택1",
    "date": "오늘",
    "summary1": "첫 번째 핵심 요약 문장",
    "summary2": "두 번째 핵심 요약 문장",
    "summary3": "세 번째 핵심 요약 문장",
    "insight": "이 뉴스가 시장 및 관련 산업(배터리/반도체/증시)에 미치는 핵심 시사점 1~2문장",
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

    # 각 항목에 고유 id 및 기본값 보정 (필터/스크랩 오류 방지)
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
