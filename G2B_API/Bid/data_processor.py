import requests
import json
import time
import os
import pandas as pd
from Bid.config import BID_API_KEY, BID_BASE_URL

__all__ = ["collect_data_for_api", "get_collected_count"]

collected_count = 0

def fetch_bid_data(endpoint_path, search_config, page=1, per_page=100):
    params = {
        "pageNo": page,
        "numOfRows": per_page,
        "inqryDiv": 1,
        "inqryBgnDt": search_config.start_date + "0000",
        "inqryEndDt": search_config.end_date + "2359",
        "type": "json",
        "bidNtceNm": search_config.keyword or "",
    }

    # ✅ 인증키는 직접 붙이고 나머지 params는 따로 전달
    url = f"{BID_BASE_URL}/{endpoint_path}?serviceKey={BID_API_KEY}"

    try:
        response = requests.get(url, params=params)
        print(f"[DEBUG] 요청 URL: {response.url}")
        response.raise_for_status()

        result = response.json().get("response", {}).get("body", {})
        return {
            "total_count": result.get("totalCount", 0),
            "items": result.get("items", [])
        }

    except Exception as e:
        print(f"[{endpoint_path}] 요청 실패: {e}")
        print(f"[DEBUG] 응답 내용: {response.text[:300]}")
        return None

def process_bid_items(items, api_desc, search_config):
    results = []

    if not items:
        return results

    keyword = search_config.keyword

    for item in items:
        bid_name = item.get("bidNtceNm", "")
        if not bid_name:
            continue

        if keyword and keyword not in bid_name:
            continue

        creditor = item.get("crdtrNm", "")
        bid_date = item.get("bidNtceDt", "")
        bid_notice_no = item.get("bidNtceNo", "")

        # 사업금액 = presmptPrce + VAT
        presmpt_price = item.get("presmptPrce", "0")
        vat = item.get("VAT", "0")

        try:
            project_amount = int(presmpt_price) + int(vat)
        except ValueError:
            project_amount = ""

        results.append({
            "입찰일시": bid_date,
            "공고명": bid_name,
            "채권자명": creditor,
            "사업금액": project_amount,
            "입찰공고번호": bid_notice_no,
            "분류": api_desc
        })

    return results


def save_data_to_csv(data, filename, mode='a'):
    global collected_count
    
    if not data:
        return
        
    df = pd.DataFrame(data)
    
    file_exists = os.path.isfile(filename)
    if file_exists and mode == 'a':
        df.to_csv(filename, mode=mode, header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(filename, mode=mode, header=True, index=False, encoding='utf-8-sig')
    
    collected_count += len(data)
    print(f"+ {len(data)}개 항목 저장 (총 {collected_count}개)")

def collect_data_for_api(api_info, search_config, output_file, max_pages=100, per_page=100, max_items=1000):
    endpoint_path = api_info["path"]
    api_desc = api_info["desc"]
    
    print(f"\n[{api_desc}] API 데이터 수집 시작...")

    first_page = fetch_bid_data(endpoint_path, search_config, 1, per_page)
    if first_page is None:
        print(f"[{api_desc}] 첫 페이지 요청 실패")
        return []
    
    total_count = first_page.get("total_count", 0)
    print(f"[{api_desc}] 총 {total_count}개의 입찰 공고가 검색되었습니다.")
    
    required_pages = min((total_count + per_page - 1) // per_page, max_pages)
    
    first_page_results = process_bid_items(first_page.get("items", []), api_desc, search_config)
    api_item_count = len(first_page_results)
    
    keyword = search_config.keyword
    if keyword:
        print(f"[{api_desc}] 페이지 1: {api_item_count}개의 '{keyword}' 관련 입찰 정보를 찾았습니다.")
    else:
        print(f"[{api_desc}] 페이지 1: {api_item_count}개의 입찰 정보를 가져왔습니다.")
    
    collected_data = first_page_results
    
    if first_page_results:
        mode = 'w' if not os.path.exists(output_file) else 'a'
        save_data_to_csv(first_page_results, output_file, mode)
    
    if required_pages > 1:
        for page in range(2, required_pages + 1):
            page_data = fetch_bid_data(endpoint_path, search_config, page, per_page)
            if page_data:
                results = process_bid_items(page_data.get("items", []), api_desc, search_config)
                
                save_data_to_csv(results, output_file, 'a')
                collected_data.extend(results)
                api_item_count += len(results)
                
                if keyword:
                    print(f"[{api_desc}] 페이지 {page}: {len(results)}개의 '{keyword}' 관련 입찰 정보를 찾았습니다.")
                else:
                    print(f"[{api_desc}] 페이지 {page}: {len(results)}개의 입찰 정보를 가져왔습니다.")
                
                if api_item_count >= max_items:
                    print(f"[{api_desc}] 최대 항목 수({max_items})에 도달했습니다.")
                    break
    
    print(f"[{api_desc}] API에서 총 {api_item_count}개의 입찰 정보를 수집했습니다.")
    
    return collected_data

def get_collected_count():
    global collected_count
    return collected_count
