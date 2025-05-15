import pandas as pd
from ScsBid.scsbid_client import (
    get_scsbid_amount,
    get_openg_corp_info,
    get_nobid_reason
)

INPUT_FILE = "G:/내 드라이브/업무용/MetaM/g2b/콜센터_입찰정보_20250101_20250201_20250414_155035.csv"
OUTPUT_FILE = "g:/내 드라이브/업무용/MetaM/g2b/콜센터_개찰정보.csv"

# 추가: bidClsfcNo 가져오기 위한 함수
def get_bid_clsfc_no(bidNtceNo):
    """
    입찰분류번호 (bidClsfcNo) 조회
    """
    url = f"http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoServcPPSSrch?serviceKey={BID_API_KEY}"
    params = {
        "pageNo": 1,
        "numOfRows": 1,
        "inqryDiv": 3,
        "type": "json",
        "bidNtceNo": bidNtceNo,
        "inqryBgnDt": "202401010000",
        "inqryEndDt": "202512312359"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        item = response.json().get("response", {}).get("body", {}).get("items", [{}])[0]
        return item.get("bidClsfcNo", "")
    except Exception as e:
        print(f"[입찰분류번호 조회 오류] {bidNtceNo}: {e}")
        return None

# BID_API_KEY가 정의되어야 하므로 이 config import도 필요합니다
from Bid.config import BID_API_KEY
import requests

def main():
    df = pd.read_csv(INPUT_FILE)
    if "입찰공고번호" not in df.columns:
        print("⚠️ '입찰공고번호' 컬럼이 존재하지 않습니다.")
        return

    bid_ids = df["입찰공고번호"].dropna().unique()
    results = []

    for bid_no in bid_ids:
        print(f"▶️ 조회 중: {bid_no}")
        amount = get_scsbid_amount(bid_no)
        corp_info = get_openg_corp_info(bid_no)

        # 낙찰금액이 없을 경우 → 유찰사유 조회 시도
        if not amount:
            bid_clsfc_no = get_bid_clsfc_no(bid_no)
            nobid_reason = get_nobid_reason(bid_no, bid_clsfc_no) if bid_clsfc_no else "bidClsfcNo 없음"
        else:
            nobid_reason = ""

        results.append({
            "입찰공고번호": bid_no,
            "낙찰금액": amount,
            "개찰업체정보": corp_info,
            "유찰사유": nobid_reason
        })

    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ 개찰 정보 {len(results)}건 저장 완료 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
