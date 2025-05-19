import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import sys
import re
import os

def clean_firebase_key(key):
    """
    Firebase 키에 사용할 수 없는 문자 제거
    Firebase는 키에 ., $, #, [, ], / 문자를 포함할 수 없음
    """
    if not key:
        return "_empty_"  # 빈 키 처리
    
    # 허용되지 않는 문자 변환
    key = str(key)
    key = key.replace('.', '_dot_')
    key = key.replace('$', '_dollar_')
    key = key.replace('#', '_hash_')
    key = key.replace('[', '_lbracket_')
    key = key.replace(']', '_rbracket_')
    key = key.replace('/', '_slash_')
    
    return key

def safe_float_convert(value):
    """문자열에서 쉼표를 제거하고 안전하게 float로 변환하는 함수"""
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # 문자열인 경우
    value = str(value).strip()
    if value == '':
        return 0.0
    
    # 쉼표 제거 후 float로 변환
    try:
        return float(value.replace(',', ''))
    except ValueError:
        print(f"경고: '{value}'를 숫자로 변환할 수 없습니다. 0으로 설정합니다.")
        return 0.0

# 파일 경로
CREDENTIAL_FILE = 'g2b-db-6aae9-firebase-adminsdk-fbsvc-0e3b1ce560.json'
CSV_FILE = 'DB/2324List.csv'
DATABASE_URL = 'https://g2b-db-6aae9-default-rtdb.asia-southeast1.firebasedatabase.app/'

# 파일 존재 확인
if not os.path.exists(CREDENTIAL_FILE):
    print(f"오류: 인증 파일 '{CREDENTIAL_FILE}'을 찾을 수 없습니다.")
    sys.exit(1)

if not os.path.exists(CSV_FILE):
    print(f"오류: CSV 파일 '{CSV_FILE}'을 찾을 수 없습니다.")
    sys.exit(1)

try:
    # Firebase 초기화
    cred = credentials.Certificate(CREDENTIAL_FILE)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    print("Firebase 초기화 성공")
    
    # CSV 파일 로드
    print(f"'{CSV_FILE}' 파일 로드 중...")
    df = pd.read_csv(CSV_FILE)
    print(f"총 {len(df)} 개의 레코드 로드 완료")
    
    # 입찰일시 컬럼에서 연도와 월 추출
    try:
        df['입찰일시'] = pd.to_datetime(df['입찰일시'])
        df['연도'] = df['입찰일시'].dt.year
        df['월'] = df['입찰일시'].dt.month
        print("날짜 데이터 처리 완료")
    except Exception as e:
        print(f"날짜 처리 중 오류 발생: {e}")
        print("오류가 발생했지만 계속 진행합니다...")
    
    # NaN 값 처리
    df = df.fillna('')
    
    # 기본 데이터와 사용자 입력 데이터 분리
    bids_data = {}
    user_inputs = {}
    
    # 진행 상황 표시
    total_rows = len(df)
    print("데이터 처리 중...")
    
    for index, row in df.iterrows():
        if index % 50 == 0:
            print(f"진행 중: {index}/{total_rows} 레코드 처리 완료 ({index/total_rows*100:.1f}%)")
        
        # 데이터 정리
        bid_data = row.to_dict()
        
        # Firebase 키 생성 시 안전한 값 사용
        year = clean_firebase_key(str(row['연도']))
        month = clean_firebase_key(str(row['월']).zfill(2))
        
        # 고유 ID 생성 (UUID 또는 공고명 기반)
        # 공고명에 특수문자가 있을 수 있으므로 안전하게 처리
        safe_name = ''.join(c if c.isalnum() else '_' for c in str(row['공고명']))
        safe_name = clean_firebase_key(safe_name)
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
                    # Firebase는 . 이 포함된 키를 허용하지 않으므로 변환
                    safe_key = clean_firebase_key(k)
                    base_data[safe_key] = v
        
        bids_data[year][month][bid_id] = base_data
        
        # 사용자 입력 데이터는 별도 노드에 저장
        user_inputs[bid_id] = {
            '물동량 평균': safe_float_convert(row['물동량 평균']),
            '용역기간(개월)': safe_float_convert(row['용역기간(개월)']),
            '마지막_수정일': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '수정자': 'initial_import'
        }
    
    print(f"모든 {total_rows} 레코드 처리 완료")
    print("Firebase에 데이터 업로드 중...")
    
    # Firebase에 데이터 업로드
    bids_ref = db.reference('/bids')
    user_inputs_ref = db.reference('/user_inputs')
    
    # 기존 데이터 삭제 확인
    confirm = input("기존 데이터를 모두 삭제하고 새로운 데이터를 업로드하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        print("기존 데이터 삭제 중...")
        bids_ref.delete()
        user_inputs_ref.delete()
        print("기존 데이터 삭제 완료")
    else:
        print("기존 데이터를 유지하고 새 데이터를 추가합니다.")
    
    # 새 데이터 업로드
    print("bids 데이터 업로드 중...")
    bids_ref.set(bids_data)
    print("bids 데이터 업로드 완료")
    
    print("user_inputs 데이터 업로드 중...")
    user_inputs_ref.set(user_inputs)
    print("user_inputs 데이터 업로드 완료")
    
    print("\n데이터 업로드 성공!")
    print(f"총 {total_rows}개의 레코드가 Firebase에 업로드되었습니다.")
    print(f"- 연도 수: {len(bids_data)}")
    print(f"- 사용자 입력 데이터 수: {len(user_inputs)}")
    
except Exception as e:
    print(f"\n오류 발생: {e}")
    print("데이터 업로드에 실패했습니다.")
    import traceback
    traceback.print_exc()
    sys.exit(1)