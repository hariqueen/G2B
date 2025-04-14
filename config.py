import os
from dotenv import load_dotenv

load_dotenv()

# API 키 설정
BID_API_KEY = os.getenv("BID_API_KEY")

# 사용할 입찰 API 목록 (현재는 '용역' 카테고리 기준)
BID_ENDPOINTS = [
    {
        "path": "getBidPblancListInfoServcPPSSrch",
        "desc": "용역"
    }
]

# 🧾 기본 검색 설정값
DEFAULT_INPUT = {
    "start_date": "20250301",
    "end_date": "20250401",
    "keyword": "콜센터"
}

# 기본 검색 조건 객체
class SearchConfig:
    def __init__(self, start_date=None, end_date=None, keyword=None):
        self.start_date = start_date or DEFAULT_INPUT["start_date"]
        self.end_date = end_date or DEFAULT_INPUT["end_date"]
        self.keyword = keyword or DEFAULT_INPUT["keyword"]

    def get_filename(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.keyword}_입찰정보_{self.start_date}_{self.end_date}_{timestamp}.csv"
