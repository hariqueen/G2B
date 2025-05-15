import time
import argparse
import requests
from Bid.config import BID_ENDPOINTS, SearchConfig, DEFAULT_PER_PAGE, DEFAULT_MAX_PAGES, DEFAULT_MAX_ITEMS_PER_API, USER_INPUT, BID_API_KEY, BID_BASE_URL
from Bid.data_processor import collect_data_for_api, get_collected_count


__all__ = ["fetch_bid_data"]

def fetch_bid_data(endpoint_path, search_config, page=1, per_page=100):
    """
    입찰 API에서 데이터를 가져오는 함수
    """
    params = {
        "serviceKey": BID_API_KEY,
        "numOfRows": per_page,
        "pageNo": page,
        "type": "json",
        "bidSearchType": 1,  # 용역 카테고리
        "bidNm": search_config.keyword,
        "fromBidDt": search_config.start_date,
        "toBidDt": search_config.end_date
    }

    url = f"{BID_BASE_URL}/{endpoint_path}"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json().get("response", {}).get("body", {})
        return {
            "total_count": result.get("totalCount", 0),
            "items": result.get("items", [])
        }
    except Exception as e:
        print(f"[{endpoint_path}] 요청 실패: {e}")
        return None

def parse_arguments():
    parser = argparse.ArgumentParser(description='공공데이터포털 입찰공고 데이터 수집기')
    
    parser.add_argument('--start-date', 
                        type=str, 
                        default=USER_INPUT["start_date"], 
                        help='조회 시작일 (YYYYMMDD 형식)')
    
    parser.add_argument('--end-date', 
                        type=str, 
                        default=USER_INPUT["end_date"], 
                        help='조회 종료일 (YYYYMMDD 형식)')
    
    parser.add_argument('--keyword', 
                        type=str, 
                        default=USER_INPUT["keyword"], 
                        help='검색 키워드 (빈 문자열로 설정하면 모든 공고 조회)')
    
    parser.add_argument('--max-pages', 
                        type=int, 
                        default=DEFAULT_MAX_PAGES, 
                        help='조회할 최대 페이지 수')
    
    parser.add_argument('--per-page', 
                        type=int, 
                        default=DEFAULT_PER_PAGE, 
                        help='페이지당 결과 수')
    
    parser.add_argument('--max-items', 
                        type=int, 
                        default=DEFAULT_MAX_ITEMS_PER_API, 
                        help='API당 수집할 최대 항목 수')
    
    return parser.parse_args()

def print_execution_time(start_time):
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time:.2f}초")

def main():
    args = parse_arguments()
    
    search_config = SearchConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        keyword=args.keyword
    )
    
    output_file = search_config.get_filename()
    
    start_time = time.time()
    
    print("데이터 수집을 시작합니다...")
    print(f"검색 조건: 기간 {search_config.start_date} ~ {search_config.end_date}, 키워드: '{search_config.keyword or '전체'}'")
    print(f"수집 결과는 '{output_file}'에 저장됩니다.")
    print("※ 용역 카테고리만 수집합니다.")
    
    for api_info in BID_ENDPOINTS:
        try:
            collect_data_for_api(
                api_info=api_info,
                search_config=search_config,
                output_file=output_file,
                max_pages=args.max_pages,
                per_page=args.per_page,
                max_items=args.max_items
            )
        except Exception as e:
            print(f"[{api_info['desc']}] 데이터 수집 중 오류 발생: {e}")
            print(f"[{api_info['desc']}] 다음 API로 이동합니다.")
    
    collected_count = get_collected_count()
    print(f"\n총 {collected_count}개의 입찰 정보를 '{output_file}'에 저장했습니다.")
    
    print_execution_time(start_time)

if __name__ == "__main__":
    main()
