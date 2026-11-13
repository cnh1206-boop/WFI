import json
import os
from google import genai
import requests

# 1. Gemini 클라이언트 초기화
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


def fetch_news():
  # 여기에 뉴스를 가져오는 로직이 들어갑니다.
  # 예시로 간단한 글로벌 경제/반도체/배터리 관련 프롬프트를 구성해 Gemini에 요청합니다.
  prompt = (
      "전 세계 경제, 반도체, 배터리 산업과 관련된 최신 핵심 소식을 3~5가지"
      " 요약해서 마크다운 형식으로 JSON 구조에 맞게 작성해줘."
  )

  try:
    print("Gemini API 호출 시작...")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    print("Gemini API 호출 완료!")
    return response.text
  except Exception as e:
    print(f"API 호출 중 오류 발생: {e}")
    return "뉴스를 불러오는 중 오류가 발생했습니다."


def main():
  print("뉴스 업데이트 스크립트 실행 중...")
  news_content = fetch_news()

  # 결과를 구조화된 JSON 데이터로 저장
  data = {"content": news_content}

  with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

  print("news.json 파일 저장 완료!")


if __name__ == "__main__":
  main()
