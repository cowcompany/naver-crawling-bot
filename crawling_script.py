import os
import requests
import csv
import datetime
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# 📂 GitHub Actions 환경에서 저장할 폴더
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 📌 크롤링 날짜 추가 (YYYY-MM-DD 형식)
today_date = datetime.datetime.now().strftime("%Y-%m-%d")

def setup_selenium():
    """ Selenium을 이용하여 로그인 후 크롤링 """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 백그라운드 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=options)

    # 네이버 부동산 페이지 접속
    driver.get("https://new.land.naver.com/complexes/107024?ms=37.5617871,127.1826662,17&a=APT:PRE:ABYG:JGC&e=RETAIL")
    time.sleep(5)  # 페이지 로드 대기

    return driver

def crawl_lease_properties(page=1, max_retries=3):
    """ 전세 매물을 크롤링하는 함수 (쿠키 및 재시도 기능 포함) """
    url = "https://new.land.naver.com/api/articles/complex/107024"
    params = {
        "realEstateType": "APT:PRE:ABYG:JGC",
        "tradeType": "B1",
        "page": page,
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://new.land.naver.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    # ✅ 네이버 로그인 쿠키 추가 (개발자 도구에서 최신값 복사)
    cookies = {
        "NNB": "VNWULNT7WWJGO",
        "NID_AUT": "rvd2DEVgotRe2lvOC6e6gF/MWxjIBoWSs/sRbrwX7ET9yLggY0njNhGcuqz5EgvN",
        "NID_JKL": "iTfl2S7lzH/EWgTBPsv1VKkH092eASi/AR9qBOQMQK0=",
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=10)
            print(f"📡 [DEBUG] 페이지 {page} 응답 상태 코드: {response.status_code}", flush=True)

            if response.status_code == 200:
                data = response.json()
                article_count = len(data.get("articleList", []))
                print(f"✅ [DEBUG] 페이지 {page} 데이터 개수: {article_count}", flush=True)
                return data
            elif response.status_code in [401, 403, 504]:
                print(f"⏳ HTTP 오류 (페이지 {page}, 시도 {attempt}/{max_retries}): {response.status_code}. 재시도 중...", flush=True)
                time.sleep(3)  # 3초 대기 후 재시도
            else:
                print(f"❌ HTTP 오류 (페이지 {page}): {response.status_code}", flush=True)
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 실패 (페이지 {page}): {e}", flush=True)
            return None

    print(f"🚨 페이지 {page} 크롤링 실패: 최대 재시도 횟수 초과", flush=True)
    return None

# 📌 전세 가격을 숫자로 변환하는 함수
def convert_price_to_number(price_str):
    """ '5억 8,000' → 580000000, '6억' → 600000000, '3억 5,000' → 350000000 """
    if not price_str:
        return 0

    price_str = price_str.replace(",", "")
    match = re.match(r"(\d+)억(?:\s*(\d+))?", price_str)

    if match:
        billion = int(match.group(1)) * 100000000
        million = int(match.group(2)) * 10000 if match.group(2) else 0
        return billion + million
    return 0

def save_to_csv(article_list, filename):
    """ 전세 매물 데이터를 CSV 파일로 저장하는 함수 """
    fieldnames = [
        "매물번호", "매물명", "유형", "거래유형", "전세가", "전세가(숫자)",
        "전용면적", "공급면적", "방향", "층수", "date"
    ]

    with open(filename, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for article in article_list:
            price_str = article.get("dealOrWarrantPrc", "")
            price_num = convert_price_to_number(price_str)

            writer.writerow({
                "매물번호": article.get("articleNo", ""),
                "매물명": article.get("articleName", ""),
                "유형": article.get("realEstateTypeName", ""),
                "거래유형": article.get("tradeTypeName", ""),
                "전세가": price_str,
                "전세가(숫자)": price_num,
                "전용면적": article.get("area1", ""),
                "공급면적": article.get("area2", ""),
                "방향": article.get("direction", ""),
                "층수": article.get("floorInfo", ""),
                "date": today_date
            })

if __name__ == "__main__":
    print("🚀 [DEBUG] 크롤링 시작...", flush=True)
    
    # ✅ Selenium을 통한 로그인 확인 (옵션)
    driver = setup_selenium()
    
    all_articles = []
    for page in range(1, 6):
        data = crawl_lease_properties(page)
        if data and "articleList" in data:
            all_articles.extend(data["articleList"])
        else:
            print(f"❌ 페이지 {page}의 데이터가 없습니다.", flush=True)

    driver.quit()  # Selenium 브라우저 종료

    filename = os.path.join(DATA_FOLDER, f"센텀팰리스_전세_{today_date}.csv")

    if all_articles:
        save_to_csv(all_articles, filename)
        print(f"✅ 파일 저장 완료: {filename}", flush=True)
    else:
        print("❌ 저장할 데이터가 없습니다.", flush=True)
