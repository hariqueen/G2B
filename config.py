"""
설정 파일 - API 정보와 검색 조건을 관리합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 관련 정보 (.env 파일에서 가져옴)
API_KEY = os.getenv("API_KEY")
BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"

# API 키가 없으면 경고 메시지 출력
if not API_KEY:
    print("API 키를 설정해주세요.")

# 조회할 API 엔드포인트 목록
API_ENDPOINTS = [
    {"path": "getBidPblancListInfoCnstwk", "desc": "공사"},
    {"path": "getBidPblancListInfoServc", "desc": "용역"},
    {"path": "getBidPblancListInfoThng", "desc": "물품"},
    {"path": "getBidPblancListInfoFrgcpt", "desc": "외자"}
]

# 검색 조건 - 필요에 따라 변경 가능
class SearchConfig:
    def __init__(self, start_date="20240101", end_date="20240120", keyword="", inqry_div="1"):
        self.start_date = start_date
        self.end_date = end_date
        self.keyword = keyword
        self.inqry_div = inqry_div  # 조회구분 (1:공고게시일시, 2:개찰일시)
    
    def get_filename(self):
        """검색 조건에 따른 파일명 생성"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        inquiry_type = "공고일시" if self.inqry_div == "1" else "개찰일시"
        
        if self.keyword:
            return f"{self.keyword}_입찰정보_{inquiry_type}_{self.start_date}_{self.end_date}_{current_time}.csv"
        else:
            return f"입찰정보_{inquiry_type}_{self.start_date}_{self.end_date}_{current_time}.csv"

# 병렬 처리 설정
MAX_WORKERS = 4  # 동시에 실행할 최대 스레드 수
SAVE_INTERVAL = 50  # 이 개수만큼 항목이 수집될 때마다 저장

# API 요청 설정
DEFAULT_PER_PAGE = 100
DEFAULT_MAX_PAGES = 100
DEFAULT_MAX_ITEMS_PER_API = 1000