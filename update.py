import json
import os
import traceback
from google import genai

# 1. Gemini 클라이언트 초기화 (환경 변수 GEMINI_API_KEY 자동 인식)
client = genai.Client()


def fetch_news():
  prompt = (
      "전 세계 경제, 반도체, 배터리 산업과 관련된 최신 핵심 소식을 3~5가지 선정해줘. "
      "반드시 아래 JSON 배열 형식으로만 응답해줘. 마크다운 백틱이나 다른 설명 텍스트는 절대 포함하지 마."
      '\n\n[\n  {\n    "title": "뉴스 제목",\n    "category": "반도체·AI 또는 2차전지·소재 중 택1",\n    "summary": "핵심 요약 내용",\n    "time": "방금 전",\n    "source": "언론사 이름"\n  }\n]'
  )

  try:
    print("Gemini API 호출 시작...")
    # 확인된 최신 3.5-flash 모델 명시
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    print("Gemini API 호출 완료!")

    # 응답 텍스트 정제 (마크다운 백틱 포함 대비)
    text = response.text.strip()
    if text.startswith("```json"):
      text = text[7:]
    if text.startswith("```"):
      text = text[3:]
    if text.endswith("```"):
      text = text[:-3]
    text = text.strip()

    return json.loads(text)
  except Exception as e:
    print("API 호출 중 상세 오류 발생:")
    traceback.print_exc()
    return []


def main():
  print("뉴스 업데이트 스크립트 실행 중...")
  news_list = fetch_news()

  data = {"articles": news_list}

  with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

  print("news.json 파일 저장 완료!")


if __name__ == "__main__":
  main()
