import time
from config import BID_ENDPOINTS, SearchConfig, DEFAULT_INPUT
from data_processor import fetch_bid_data, process_bid_items
from scsbid_client import get_scsbid_amount, get_openg_corp_info, get_bid_clsfc_no, get_nobid_reason
import pandas as pd
import os


def print_execution_time(start_time):
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time:.2f}초")


def main():
    start_time = time.time()

    config = SearchConfig()
    output_file = config.get_filename()
    all_data = []

    print("\n📦 입찰 + 개찰 통합 수집을 시작합니다...")
    print(f"검색 조건: 기간 {config.start_date} ~ {config.end_date}, 키워드: '{config.keyword or '전체'}'")
    print(f"수집 결과는 '{output_file}'에 저장됩니다.")
    print("※ 용역 카테고리만 수집합니다.")

    for api in BID_ENDPOINTS:
        try:
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

        except Exception as e:
            print(f"[{api['desc']}] 데이터 수집 중 오류 발생: {e}")
            print(f"[{api['desc']}] 다음 API로 이동합니다.")

    if all_data:
        df = pd.DataFrame(all_data)
        filepath = os.path.join("g:/내 드라이브/업무용/MetaM/g2b", output_file)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"\n✅ 총 {len(df)}건 수집 완료 → {filepath}")
    else:
        print("⚠️ 수집된 데이터가 없습니다.")

    print_execution_time(start_time)


if __name__ == "__main__":
    main()