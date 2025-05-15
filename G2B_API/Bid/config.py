import os
from dotenv import load_dotenv

load_dotenv()

USER_INPUT = {
    "keyword": "콜센터",
    "start_date": "20250301",
    "end_date": "20250401"
}

BID_API_KEY = os.getenv("BID_API_KEY")
BID_BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"

if not BID_API_KEY:
    print("BID_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

BID_ENDPOINTS = [
    {"path": "getBidPblancListInfoServcPPSSrch", "desc": "용역"}
]

class SearchConfig:
    def __init__(self, start_date=USER_INPUT["start_date"], end_date=USER_INPUT["end_date"], keyword=USER_INPUT["keyword"]):
        self.start_date = start_date
        self.end_date = end_date
        self.keyword = keyword
    
    def get_filename(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.keyword:
            return f"{self.keyword}_입찰정보_{self.start_date}_{self.end_date}_{current_time}.csv"
        else:
            return f"입찰정보_{self.start_date}_{self.end_date}_{current_time}.csv"

DEFAULT_PER_PAGE = 100
DEFAULT_MAX_PAGES = 100
DEFAULT_MAX_ITEMS_PER_API = 1000