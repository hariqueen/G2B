import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

# Firebase 초기화
cred = credentials.Certificate('g2b-db-6aae9-default-rtdb-export.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://g2b-db-6aae9-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# CSV 파일 로드
df = pd.read_csv('2324List.csv')

# 입찰일시 컬럼에서 연도와 월 추출
df['입찰일시'] = pd.to_datetime(df['입찰일시'])
df['연도'] = df['입찰일시'].dt.year
df['월'] = df['입찰일시'].dt.month

# NaN 값 처리
df = df.fillna('')

# 기본 데이터와 사용자 입력 데이터 분리
bids_data = {}
user_inputs = {}

for index, row in df.iterrows():
    # 데이터 정리
    bid_data = row.to_dict()
    year = str(row['연도'])
    month = str(row['월']).zfill(2)
    
    # 고유 ID 생성 (UUID 또는 공고명 기반)
    # 공고명에 특수문자가 있을 수 있으므로 안전하게 처리
    safe_name = ''.join(c if c.isalnum() else '_' for c in row['공고명'])
    bid_id = f"bid_{index}_{safe_name[:20]}"
    
    # 기본 API 데이터는 bids에 저장
    if year not in bids_data:
        bids_data[year] = {}
    
    if month not in bids_data[year]:
        bids_data[year][month] = {}
    
    # 기본 정보만 포함 (사용자 입력 데이터 제외)
    base_data = {}
    for k, v in bid_data.items():
        if k not in ['물동량 평균', '용역기간(개월)', '연도', '월']:
            # datetime 객체는 JSON으로 직렬화할 수 없으므로 문자열로 변환
            if isinstance(v, pd.Timestamp):
                base_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                base_data[k] = v
    
    bids_data[year][month][bid_id] = base_data
    
    # 사용자 입력 데이터는 별도 노드에 저장
    mm_value = row['물동량 평균'] if pd.notna(row['물동량 평균']) else 0
    if isinstance(mm_value, str) and mm_value.strip() == '':
        mm_value = 0
    
    duration_value = row['용역기간(개월)'] if pd.notna(row['용역기간(개월)']) else 0
    if isinstance(duration_value, str) and duration_value.strip() == '':
        duration_value = 0
    
    user_inputs[bid_id] = {
        '물동량 평균': float(mm_value),
        '용역기간(개월)': float(duration_value),
        '마지막_수정일': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '수정자': 'initial_import'
    }

# Firebase에 데이터 업로드
bids_ref = db.reference('/bids')
user_inputs_ref = db.reference('/user_inputs')

# 기존 데이터 삭제 (옵션)
bids_ref.delete()
user_inputs_ref.delete()

# 새 데이터 업로드
bids_ref.set(bids_data)
user_inputs_ref.set(user_inputs)

print("데이터 업로드 완료!")