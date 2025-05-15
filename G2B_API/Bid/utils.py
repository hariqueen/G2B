import time
import argparse
from config import USER_INPUT

def parse_arguments():
    """
    명령행 인자를 파싱하는 함수
    
    Returns:
        argparse.Namespace: 파싱된 명령행 인자
    """
    parser = argparse.ArgumentParser(description='공공데이터포털 입찰공고 및 개찰결과 데이터 수집기')
    
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
                        default=100, 
                        help='조회할 최대 페이지 수')
    
    parser.add_argument('--per-page', 
                        type=int, 
                        default=100, 
                        help='페이지당 결과 수')
    
    parser.add_argument('--max-items', 
                        type=int, 
                        default=1000, 
                        help='API당 수집할 최대 항목 수')
    
    return parser.parse_args()

def print_execution_time(start_time):
    """
    실행 시간을 계산하여 출력하는 함수
    
    Args:
        start_time (float): 시작 시간
    """
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time:.2f}초")