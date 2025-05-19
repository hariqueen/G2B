# check_firebase.py
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Firebase 초기화
cred = credentials.Certificate('g2b-db-6aae9-firebase-adminsdk-fbsvc-0e3b1ce560.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://g2b-db-6aae9-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# 데이터 확인
def check_data():
    # 루트 데이터 확인
    root_ref = db.reference('/')
    root_data = root_ref.get()
    
    print("===== Firebase 데이터 확인 =====")
    print(f"루트 데이터 존재: {'예' if root_data else '아니오'}")
    
    if not root_data:
        print("데이터가 없습니다. 데이터베이스가 비어 있습니다.")
        return
    
    print(f"루트 키: {list(root_data.keys())}")
    
    # 'bids' 노드 확인
    if 'bids' in root_data:
        bids_data = root_data['bids']
        print(f"\n[bids] 데이터 존재: {'예' if bids_data else '아니오'}")
        if bids_data:
            print(f"연도 목록: {list(bids_data.keys())}")
    else:
        print("\n[bids] 데이터가 없습니다.")
    
    # 'user_inputs' 노드 확인
    if 'user_inputs' in root_data:
        user_inputs = root_data['user_inputs']
        print(f"\n[user_inputs] 데이터 존재: {'예' if user_inputs else '아니오'}")
        if user_inputs:
            print(f"항목 수: {len(user_inputs)}")
    else:
        print("\n[user_inputs] 데이터가 없습니다.")

# 실행
check_data()