import os
from dotenv import load_dotenv

load_dotenv()

# API 키 설정
BID_API_KEY = os.getenv("BID_API_KEY")

# 사용할 입찰 API 목록 (현재 용역 카테고리 기준)
BID_ENDPOINTS = [
    {
        "path": "getBidPblancListInfoServcPPSSrch",
        "desc": "용역"
    }
]

# 기본 검색 조건 클래스
class SearchConfig:
    def __init__(self):
        self.start_date = "20250101"  # YYYYMMDD
        self.end_date = "20250201"
        self.keyword = "콜센터"

    def get_filename(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.keyword}_입찰정보_{self.start_date}_{self.end_date}_{timestamp}.csv"
