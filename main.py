"""
메인 모듈 - 입찰정보 수집 프로그램의 진입점입니다.
"""

import time
from config import API_ENDPOINTS, SearchConfig, DEFAULT_PER_PAGE, DEFAULT_MAX_PAGES, DEFAULT_MAX_ITEMS_PER_API
from data_processor import collect_data_for_api, get_collected_count
from utils import parse_arguments, print_execution_time

def main():
    """메인 프로그램"""
    # 명령행 인자 파싱
    args = parse_arguments()
    
    # 검색 설정 생성
    search_config = SearchConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        keyword=args.keyword,
        inqry_div=args.inqry_div
    )
    
    # 출력 파일명 생성
    output_file = search_config.get_filename()
    
    # 실행 시간 측정 시작
    start_time = time.time()
    
    print("데이터 수집을 시작합니다...")
    inquiry_type = "공고일시" if search_config.inqry_div == "1" else "개찰일시"
    print(f"검색 조건: 기준 {inquiry_type}, 기간 {search_config.start_date} ~ {search_config.end_date}, 키워드: '{search_config.keyword or '전체'}'")
    print(f"수집 결과는 '{output_file}'에 실시간으로 저장됩니다.")
    
    # 각 API 엔드포인트에 대해 데이터 수집
    for api_info in API_ENDPOINTS:
        try:
            # API별 데이터 수집 (내부에서 실시간 저장)
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
    
    # 결과 출력
    collected_count = get_collected_count()
    print(f"\n총 {collected_count}개의 입찰 정보를 '{output_file}'에 저장했습니다.")
    
    # 실행 시간 출력
    print_execution_time(start_time)

if __name__ == "__main__":
    main()