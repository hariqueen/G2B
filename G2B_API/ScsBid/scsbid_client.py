import requests
from Bid.config import BID_API_KEY

BASE_URL = "http://apis.data.go.kr/1230000/as/ScsbidInfoService"

__all__ = ["fetch_biget_scsbid_amountd_data", "get_openg_corp_info", "get_nobid_reason"]

def get_scsbid_amount(bidNtceNo):
    """낙찰금액 조회 (inqryDiv=4)"""
    url = f"{BASE_URL}/getScsbidListSttusServc?serviceKey={BID_API_KEY}"
    params = {
        "pageNo": 1,
        "numOfRows": 1,
        "inqryDiv": 4,
        "type": "json",
        "bidNtceNo": bidNtceNo,
        "inqryBgnDt": "202401010000",
        "inqryEndDt": "202512312359"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        item = data.get("response", {}).get("body", {}).get("items", [{}])[0]
        return item.get("sucsfbidAmt", "")
    except Exception as e:
        print(f"[낙찰금액] {bidNtceNo} 오류: {e}")
        return None

def get_openg_corp_info(bidNtceNo):
    """
    개찰업체 정보 조회 (inqryDiv=3)
    API: getOpengResultListInfoServcPPSSrch
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
        data = response.json()
        item = data.get("response", {}).get("body", {}).get("items", [{}])[0]
        return item.get("opengCorpInfo", "")
    except Exception as e:
        print(f"[개찰업체] {bidNtceNo} 오류: {e}")
        return None

def get_nobid_reason(bidNtceNo, bidClsfcNo):
    """
    유찰 사유 조회 (nobidRsn)
    """
    url = f"http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoFailing?serviceKey={BID_API_KEY}"
    params = {
        "pageNo": 1,
        "numOfRows": 1,
        "type": "json",
        "bidNtceNo": bidNtceNo,
        "bidClsfcNo": bidClsfcNo,
        "inqryBgnDt": "202401010000",
        "inqryEndDt": "202512312359"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        item = response.json().get("response", {}).get("body", {}).get("items", [{}])[0]
        return item.get("nobidRsn", "")
    except Exception as e:
        print(f"[유찰사유 조회 오류] {bidNtceNo}: {e}")
        return None