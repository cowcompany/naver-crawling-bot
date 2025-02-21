import os
import requests
import csv
import datetime
import re

from google.colab import drive
drive.mount('/content/drive')

# 📂 GitHub Actions 환경에서 저장할 폴더
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 📌 크롤링 날짜 추가 (YYYY-MM-DD 형식)
today_date = datetime.datetime.now().strftime("%Y-%m-%d")

def crawl_lease_properties(page=1):
    """ 전세 매물을 크롤링하는 함수 """
    url = "https://new.land.naver.com/api/articles/complex/107024"
    params = {
        "realEstateType": "APT:PRE:ABYG:JGC",
        "tradeType": "B1",  # 전세
        "tag": "::::::::",
        "rentPriceMin": "0",
        "rentPriceMax": "900000000",
        "priceMin": "0",
        "priceMax": "900000000",
        "areaMin": "0",
        "areaMax": "900000000",
        "oldBuildYears": "",
        "recentlyBuildYears": "",
        "minHouseHoldCount": "",
        "maxHouseHoldCount": "",
        "showArticle": "false",
        "sameAddressGroup": "false",
        "minMaintenanceCost": "",
        "maxMaintenanceCost": "",
        "priceType": "RETAIL",
        "directions": "",
        "page": page,
        "complexNo": "107024",
        "buildingNos": "",
        "areaNos": "",
        "type": "list",
        "order": "rank"
    }

    cookies = {
        "NAC": "7OkBBcg0CXTf",
        "NNB": "VNWULNT7WWJGO",
        "nid_inf": "37537044",
        "NID_AUT": "rvd2DEVgotRe2lvOC6e6gF/MWxjIBoWSs/sRbrwX7ET9yLggY0njNhGcuqz5EgvN",
        "NID_JKL": "iTfl2S7lzH/EWgTBPsv1VKkH092eASi/AR9qBOQMQK0=",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3Mzk1NzAyNzMsImV4cCI6MTczOTU4MTA3M30.89ygvJtcP_W9uZY_2sXji-IKkrkUKuSsfFbBxYZ9FpU",
        "referer": "https://new.land.naver.com/complexes/107024?ms=37.5617871,127.1826662,17&a=APT:PRE:ABYG:JGC&e=RETAIL",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    response = requests.get(url, params=params, cookies=cookies, headers=headers)

    # ✅ 응답 데이터 확인 (디버깅용)
    print(f"페이지 {page} 응답 상태 코드:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print(f"페이지 {page} 데이터 개수:", len(data.get("articleList", [])))  # ✅ 실제 데이터 개수 확인
        return data
    else:
        print("HTTP 오류:", response.status_code)
        return None

# 📌 전세 가격을 숫자로 변환하는 함수
def convert_price_to_number(price_str):
    """
    '5억 8,000' → 580000000
    '6억' → 600000000
    '3억 5,000' → 350000000
    """
    if not price_str:
        return 0

    price_str = price_str.replace(",", "")  # 쉼표 제거
    match = re.match(r"(\d+)억(?:\s*(\d+))?", price_str)

    if match:
        billion = int(match.group(1)) * 100000000  # '5억' → 500000000
        million = int(match.group(2)) * 10000 if match.group(2) else 0  # '8,000' → 80000000
        return billion + million
    return 0

def save_to_csv(article_list, filename):
    """ 전세 매물 데이터를 CSV 파일로 저장하는 함수 """
    fieldnames = [
        "매물번호", "매물명", "유형", "거래유형", "전세가", "전세가(숫자)",
        "전용면적", "공급면적", "방향", "층수", "date"  # 🔹 "특징"과 "태그" 제거
    ]

    with open(filename, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for article in article_list:
            price_str = article.get("dealOrWarrantPrc", "")
            price_num = convert_price_to_number(price_str)  # 🔹 가격 변환 적용

            writer.writerow({
                "매물번호": article.get("articleNo", ""),  # 매물 고유번호
                "매물명": article.get("articleName", ""),  # 매물명
                "유형": article.get("realEstateTypeName", ""),  # 아파트, 오피스텔 등
                "거래유형": article.get("tradeTypeName", ""),  # 매매, 전세, 월세
                "전세가": price_str,  # 🔹 원래 문자 그대로 저장
                "전세가(숫자)": price_num,  # 🔹 변환된 숫자로 저장
                "전용면적": article.get("area1", ""),  # 전용면적
                "공급면적": article.get("area2", ""),  # 공급면적
                "방향": article.get("direction", ""),  # 남향, 동향 등
                "층수": article.get("floorInfo", ""),  # 저/중/고 층 정보
                "date": today_date  # ✅ 날짜 추가
            })

if __name__ == "__main__":
    all_articles = []
    for page in range(1, 6):
        data = crawl_lease_properties(page)
        if data and "articleList" in data:
            all_articles.extend(data["articleList"])
        else:
            print(f"❌ 페이지 {page}의 데이터가 없습니다.")

    today = datetime.datetime.now().strftime("%Y%m%d")
    filename = os.path.join(DATA_FOLDER, f"센텀팰리스_전세_{today_date}.csv")

    # ✅ 데이터가 있을 경우에만 저장
    if all_articles:
        save_to_csv(all_articles, filename)
        print(f"✅ 파일 저장 완료: {filename}")
    else:
        print("❌ 저장할 데이터가 없습니다.")