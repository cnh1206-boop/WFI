import json
import os
from google import genai
from google.genai import types

# 1. Gemini 클라이언트 초기화
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


def fetch_news():
  # 대시보드 카드 형태로 바로 렌더링할 수 있도록 JSON 구조 지정
  prompt = (
      "전 세계 경제, 반도체, 배터리 산업과 관련된 최신 핵심 소식을 3~5가지 선정해줘. "
      "반드시 아래 JSON 배열 형식으로만 응답해줘. 마크다운 백틱(```json)이나 다른 설명 텍스트는 절대 포함하지 마."
      '\n\n[\n  {\n    "title": "뉴스 제목",\n    "category": "반도체·AI 또는 2차전지·소재 중 택1",\n    "summary": "핵심 요약 내용",\n    "time": "방금 전",\n    "source": "Bloomberg 등 언론사"\n  }\n]'
  )

  try:
    print("Gemini API 호출 시작...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    print("Gemini API 호출 완료!")
    # 응답받은 JSON 문자열을 파이썬 객체로 파싱
    return json.loads(response.text)
  except Exception as e:
    print(f"API 호출 중 오류 발생: {e}")
    return []


def main():
  print("뉴스 업데이트 스크립트 실행 중...")
  news_list = fetch_news()

  # 프론트엔드에서 읽기 쉬운 구조로 저장
  data = {"articles": news_list}

  with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

  print("news.json 파일 저장 완료!")


if __name__ == "__main__":
  main()
