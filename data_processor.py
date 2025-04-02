"""
데이터 처리 모듈 - API에서 가져온 데이터를 처리하고 저장합니다.
"""

import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
from api_client import fetch_data_from_api
from config import MAX_WORKERS, SAVE_INTERVAL

# 수집된 항목 수를 추적하기 위한 카운터
collected_count = 0

def process_items(items, api_desc, search_config):
    """
    API 응답의 items를 처리하는 함수
    
    Args:
        items (list): API 응답 항목 리스트
        api_desc (str): API 설명 (분류)
        search_config (SearchConfig): 검색 설정 객체
        
    Returns:
        list: 처리된 항목 리스트
    """
    results = []
    
    if not items:
        return results
    
    keyword = search_config.keyword
    
    # 항목 처리
    for item in items:
        # 공고명 가져오기
        bid_name = item.get("bidNtceNm", "")
        if not bid_name:
            continue
            
        # 키워드 필터링 (keyword가 빈 문자열이면 모든 항목 포함)
        if keyword and keyword not in bid_name:
            continue
            
        # 채권자명 가져오기
        creditor = item.get("crdtrNm", "")
        
        # 입찰일시 가져오기
        bid_date = item.get("bidNtceDt", "")
        
        # 개찰일시 가져오기
        opening_date = item.get("opengDt", "")
        
        # 추정가격 가져오기
        estimated_price = item.get("presmptPrce", "")
        
        # 결과 추가
        results.append({
            "공고명": bid_name,
            "채권자명": creditor,
            "입찰일시": bid_date,
            "개찰일시": opening_date,
            "추정가격": estimated_price,
            "분류": api_desc
        })
    
    return results

def save_data_to_csv(data, filename, mode='a'):
    """
    데이터를 CSV 파일로 저장하는 함수
    
    Args:
        data (list): 저장할 데이터 리스트
        filename (str): 저장할 파일명
        mode (str): 파일 저장 모드 ('w': 덮어쓰기, 'a': 추가)
    """
    global collected_count
    
    if not data:
        return
        
    df = pd.DataFrame(data)
    
    # 파일이 이미 존재하고 append 모드라면 헤더 없이 추가
    file_exists = os.path.isfile(filename)
    if file_exists and mode == 'a':
        df.to_csv(filename, mode=mode, header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(filename, mode=mode, header=True, index=False, encoding='utf-8-sig')
    
    collected_count += len(data)
    print(f"+ {len(data)}개 항목 저장 (총 {collected_count}개)")

def fetch_page(args):
    """
    스레드 풀에서 사용할 페이지 조회 함수
    
    Args:
        args (tuple): (endpoint_path, api_desc, page_no, per_page, search_config)
        
    Returns:
        list: 처리된 항목 리스트
    """
    endpoint_path, api_desc, page_no, per_page, search_config = args
    
    # API 요청
    api_response = fetch_data_from_api(endpoint_path, search_config, page_no, per_page)
    if api_response is None:
        return []
        
    # 데이터 처리
    items = api_response.get("items", [])
    return process_items(items, api_desc, search_config)

def collect_data_for_api(api_info, search_config, output_file, max_pages=100, per_page=100, max_items=1000):
    """
    특정 API에 대한 데이터 수집 함수
    
    Args:
        api_info (dict): API 정보 객체
        search_config (SearchConfig): 검색 설정 객체
        output_file (str): 출력 파일명
        max_pages (int): 조회할 최대 페이지 수
        per_page (int): 페이지당 결과 수
        max_items (int): 수집할 최대 항목 수
        
    Returns:
        list: 수집된 항목 리스트
    """
    endpoint_path = api_info["path"]
    api_desc = api_info["desc"]
    
    print(f"\n[{api_desc}] API 데이터 수집 시작 ({endpoint_path})...")
    
    # 첫 페이지 요청하여 총 결과 수 확인
    first_page = fetch_data_from_api(endpoint_path, search_config, 1, per_page)
    if first_page is None:
        print(f"[{api_desc}] 첫 페이지 요청 실패, 다음 API로 이동합니다.")
        return []
    
    total_count = first_page.get("total_count", 0)
    print(f"[{api_desc}] 총 {total_count}개의 입찰 공고가 검색되었습니다.")
    
    # 필요한 페이지 수 계산
    required_pages = min((total_count + per_page - 1) // per_page, max_pages)
    
    # 첫 페이지 처리
    first_page_results = process_items(first_page.get("items", []), api_desc, search_config)
    api_item_count = len(first_page_results)
    
    keyword = search_config.keyword
    if keyword:
        print(f"[{api_desc}] 페이지 1: {api_item_count}개의 '{keyword}' 관련 입찰 정보를 찾았습니다.")
    else:
        print(f"[{api_desc}] 페이지 1: {api_item_count}개의 입찰 정보를 가져왔습니다.")
    
    # 첫 페이지 데이터 저장
    if first_page_results:
        # 첫 번째 API의 첫 페이지인 경우 새 파일 생성, 그 외에는 추가
        mode = 'w' if not os.path.exists(output_file) else 'a'
        save_data_to_csv(first_page_results, output_file, mode)
    
    # 남은 페이지 처리할 작업 목록 생성
    tasks = [(endpoint_path, api_desc, page, per_page, search_config) for page in range(2, required_pages + 1)]
    
    if not tasks:
        print(f"[{api_desc}] 추가 페이지가 없습니다.")
        return first_page_results
    
    # 병렬 처리를 위한 스레드 풀 생성
    collected_data = first_page_results
    buffer = []  # 임시 저장용 버퍼
    
    print(f"[{api_desc}] 남은 {len(tasks)}개 페이지 병렬 처리 시작...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i, results in enumerate(executor.map(fetch_page, tasks), 2):
            # 결과 처리
            buffer.extend(results)
            api_item_count += len(results)
            
            # 로그 출력
            if keyword:
                print(f"[{api_desc}] 페이지 {i}: {len(results)}개의 '{keyword}' 관련 입찰 정보를 찾았습니다.")
            else:
                print(f"[{api_desc}] 페이지 {i}: {len(results)}개의 입찰 정보를 가져왔습니다.")
            
            # 일정 개수마다 저장
            if len(buffer) >= SAVE_INTERVAL:
                save_data_to_csv(buffer, output_file, 'a')
                collected_data.extend(buffer)
                buffer = []
            
            # 최대 항목 수 도달 시 중단
            if api_item_count >= max_items:
                print(f"[{api_desc}] 최대 항목 수({max_items})에 도달했습니다.")
                break
    
    # 남은 데이터 저장
    if buffer:
        save_data_to_csv(buffer, output_file, 'a')
        collected_data.extend(buffer)
    
    print(f"[{api_desc}] API에서 총 {api_item_count}개의 입찰 정보를 수집했습니다.")
    return collected_data

def get_collected_count():
    """수집된 총 항목 수 반환"""
    global collected_count
    return collected_count