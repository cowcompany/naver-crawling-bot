import os
import requests
import csv
import datetime
import re
import sys  # ✅ 강제 출력용 추가

print("🚀 [DEBUG] 크롤링 스크립트 실행 시작...", flush=True)  # ✅ 실행 여부 확인용

# 📂 저장 폴더 설정
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 📌 크롤링 날짜 추가 (YYYY-MM-DD 형식)
today_date = datetime.datetime.now().strftime("%Y-%m-%d")

def crawl_lease_properties(page=1):
    """ 전세 매물을 크롤링하는 함수 """
    print(f"🌍 [DEBUG] {page}페이지 크롤링 시작", flush=True)  # ✅ 실행 로그 추가

    url = "https://new.land.naver.com/api/articles/complex/107024"
    params = {
        "realEstateType": "APT",
        "tradeType": "B1",  # 전세
        "page": page,
    }

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    response = requests.get(url, params=params, headers=headers)

    # ✅ 강제 출력
    print(f"📡 [DEBUG] 페이지 {page} 응답 상태 코드: {response.status_code}", flush=True)

    if response.status_code == 200:
        try:
            data = response.json()
            article_count = len(data.get("articleList", []))
            print(f"✅ [DEBUG] 페이지 {page} 데이터 개수: {article_count}", flush=True)
            return data
        except ValueError:
            print(f"❌ JSON 파싱 오류 (페이지 {page})", flush=True)
            return None
    else:
        print(f"❌ HTTP 오류 (페이지 {page}): {response.status_code}", flush=True)
        return None

if __name__ == "__main__":
    print("🚀 [DEBUG] 크롤링 시작...", flush=True)  # ✅ 실행 시작 로그 추가
    all_articles = []
    for page in range(1, 6):
        data = crawl_lease_properties(page)
        if data and "articleList" in data:
            all_articles.extend(data["articleList"])
        else:
            print(f"❌ 페이지 {page}의 데이터가 없습니다.", flush=True)

    print("🔄 [DEBUG] 크롤링 종료. 저장할 데이터 개수:", len(all_articles), flush=True)
