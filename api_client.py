"""
API 클라이언트 - 입찰 정보 API와의 통신을 담당합니다.
"""

import requests
import json
import time
from config import API_KEY, BASE_URL

def fetch_data_from_api(endpoint, search_config, page_no=1, per_page=100, timeout=30, max_retries=3, retry_delay=2):
    """
    특정 API 엔드포인트에서 데이터를 가져오는 함수
    
    Args:
        endpoint (str): API 엔드포인트 경로
        search_config (SearchConfig): 검색 설정 객체
        page_no (int): 페이지 번호
        per_page (int): 페이지당 결과 수
        timeout (int): 요청 타임아웃 시간(초)
        max_retries (int): 최대 재시도 횟수
        retry_delay (int): 재시도 사이의 대기 시간(초)
        
    Returns:
        dict or None: API 응답 데이터 또는 오류 시 None
    """
    # 조회 구분 설정 (1: 공고게시일시, 2: 개찰일시)
    inqry_div = search_config.inqry_div
    
    # 날짜 필드명 설정 (조회 구분에 따라 다름)
    if inqry_div == "1":
        # 공고게시일시 기준 조회
        begin_date_param = f"inqryBgnDt={search_config.start_date}0000"
        end_date_param = f"inqryEndDt={search_config.end_date}2359"
    else:
        # 개찰일시 기준 조회
        begin_date_param = f"opengBgnDt={search_config.start_date}0000"
        end_date_param = f"opengEndDt={search_config.end_date}2359"
    
    # API URL 구성
    url = f"{BASE_URL}/{endpoint}?serviceKey={API_KEY}&inqryDiv={inqry_div}&{begin_date_param}&{end_date_param}&pageNo={page_no}&numOfRows={per_page}&type=json"
    
    # 재시도 로직
    retries = 0
    while retries <= max_retries:
        try:
            # API 요청
            response = requests.get(url, timeout=timeout)  # 타임아웃 설정
            
            # 디버깅 정보 출력 (첫 페이지만)
            if page_no == 1:
                print(f"요청 URL: {url[:100]}... (URL 일부 표시)")
                print(f"상태 코드: {response.status_code}")
            
            # 응답이 200이 아니면 오류 메시지 출력
            if response.status_code != 200:
                print(f"API 요청 실패: 상태 코드 {response.status_code}")
                # 일부 오류 상태 코드는 재시도하지 않음
                if response.status_code in [400, 401, 403, 404]:
                    return None
                # 그 외 오류는 재시도
                retries += 1
                if retries <= max_retries:
                    print(f"재시도 중... ({retries}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                return None
            
            try:
                # JSON 응답 파싱
                json_response = response.json()
                
                # 응답 헤더 확인
                header = json_response.get("response", {}).get("header", {})
                result_code = header.get("resultCode")
                result_msg = header.get("resultMsg")
                
                if result_code != "00" or result_msg != "정상":
                    print(f"API 오류: {result_code} - {result_msg}")
                    retries += 1
                    if retries <= max_retries:
                        print(f"재시도 중... ({retries}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    return None
                
                # 바디에서 데이터 추출
                body = json_response.get("response", {}).get("body", {})
                items = body.get("items", [])
                total_count = body.get("totalCount", 0)
                
                return {
                    "items": items,
                    "total_count": total_count
                }
                
            except json.JSONDecodeError as e:
                print(f"JSON 응답 파싱 오류: {e}")
                retries += 1
                if retries <= max_retries:
                    print(f"재시도 중... ({retries}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            retries += 1
            if retries <= max_retries:
                print(f"재시도 중... ({retries}/{max_retries})")
                time.sleep(retry_delay)
                continue
            return None
    
    return None  # 모든 재시도 실패 시