import time
from config import SearchConfig, BID_ENDPOINTS
from data_processor import fetch_bid_data, process_bid_items
from scsbid_client import get_scsbid_amount, get_openg_corp_info, get_bid_clsfc_no, get_nobid_reason
from utils import parse_arguments, print_execution_time
import pandas as pd
import os


def main():
    start_time = time.time()

    # ✅ 명령행 인자 파싱
    args = parse_arguments({
        "start_date": "20250301",
        "end_date": "20250401",
        "keyword": "콜센터"
    })

    config = SearchConfig()
    config.start_date = args.start_date
    config.end_date = args.end_date
    config.keyword = args.keyword

    all_data = []
    print("\n📦 입찰 + 개찰 통합 수집을 시작합니다...\n")

    for api in BID_ENDPOINTS:
        response = fetch_bid_data(api["path"], config)
        if response is None:
            continue

        bid_items = process_bid_items(response.get("items", []), api["desc"], config)

        for item in bid_items:
            bid_no = item["입찰공고번호"]
            print(f"📄 처리 중: {bid_no}")

            amount = get_scsbid_amount(bid_no)
            corp_info = get_openg_corp_info(bid_no)

            if not amount:
                clsfc_no = get_bid_clsfc_no(bid_no)
                nobid_reason = get_nobid_reason(bid_no, clsfc_no) if clsfc_no else "bidClsfcNo 없음"
            else:
                nobid_reason = ""

            all_data.append({
                **item,
                "낙찰금액": amount,
                "개찰업체정보": corp_info,
                "유찰사유": nobid_reason
            })

    if all_data:
        df = pd.DataFrame(all_data)
        filename = f"{config.keyword}_입찰+개찰통합_{config.start_date}_{config.end_date}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join("g:/내 드라이브/업무용/MetaM/g2b", filename)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"\n✅ 총 {len(df)}건 수집 완료 → {filepath}")
    else:
        print("⚠️ 수집된 데이터가 없습니다.")

    print_execution_time(start_time)


if __name__ == "__main__":
    main()