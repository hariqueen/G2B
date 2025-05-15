import pandas as pd
import numpy as np
import re
from datetime import datetime

def preprocess_bid_data(input_csv: str, prediction_years: int = 30) -> pd.DataFrame:
    # CSV 파일 로딩
    df = pd.read_csv(input_csv)
    
    # 연도, 월 데이터 정리
    df["년"] = df["년"].astype(str).str.extract(r'(\d{4})').astype(int)
    df["월"] = df["월"].astype(int)
    df["년월"] = df["년"].astype(str) + df["월"].astype(str).str.zfill(2)
    
    # 용역기간 정수형으로 변환
    df["용역기간(개월)"] = df["용역기간(개월)"].fillna(0).astype(int)
    
    # 날짜 형식 변환 - 정확한 연도와 월 사용
    df["공고_시작일"] = pd.to_datetime(df["년"].astype(str) + "-" + df["월"].astype(str).str.zfill(2) + "-01")
    df["예상_입찰일"] = df["공고_시작일"]  # 입찰일은 공고 시작일과 동일하게 설정
    
    # 숫자 데이터 정리 함수
    def clean_numeric(value):
        if pd.isna(value):
            return 0
        if isinstance(value, (int, float)):
            return value
        # 쉼표, 원, 기타 문자 제거 후 숫자만 추출
        cleaned = re.sub(r'[^\d.]', '', str(value))
        return float(cleaned) if cleaned else 0
    
    # 금액 컬럼 숫자로 변환
    df["계약 기간 내"] = df["계약 기간 내"].apply(clean_numeric).astype(float)
    df["입찰금액_1순위"] = df["입찰금액_1순위"].apply(clean_numeric).astype(float)
    
    # 물동량 평균 숫자로 변환
    df["물동량 평균"] = df["물동량 평균"].apply(clean_numeric).astype(float)
    
    # 텍스트 컬럼 정리
    df["실수요기관"] = df["실수요기관"].fillna("").astype(str).str.strip()
    df["공고명"] = df["공고명"].fillna("").astype(str).str.strip()
    df["입찰결과_1순위"] = df["입찰결과_1순위"].fillna("").astype(str).str.strip()
    
    # 예상 연도와 월 컬럼 추가 (정렬 및 필터링용)
    df["예상_연도"] = df["예상_입찰일"].dt.year
    df["예상_입찰월"] = df["예상_입찰일"].dt.month
    
    # 필요한 컬럼만 선택
    df_processed = df[[
        "년", "월", "년월", "실수요기관", "공고명", "물동량 평균",
        "용역기간(개월)", "계약 기간 내", "입찰결과_1순위", "입찰금액_1순위",
        "공고_시작일", "예상_입찰일", "예상_연도", "예상_입찰월"
    ]]
    
    # NaN 값 처리
    numeric_columns = ["물동량 평균", "용역기간(개월)", "계약 기간 내", "입찰금액_1순위"]
    for col in numeric_columns:
        df_processed[col] = df_processed[col].fillna(0)
    
    text_columns = ["실수요기관", "공고명", "입찰결과_1순위"]
    for col in text_columns:
        df_processed[col] = df_processed[col].fillna("")
    
    # 현재 데이터 확인 - 연도별 데이터 개수 출력
    연도별_데이터수 = df_processed.groupby("예상_연도")["공고명"].count()
    print("원본 데이터 연도별 개수:")
    print(연도별_데이터수)
    
    # 예측 데이터 생성 - 현재 데이터가 있는 연도는 제외
    현재_데이터_연도 = set(df_processed["예상_연도"].unique())
    df_prediction = generate_prediction_data(df_processed, prediction_years, 현재_데이터_연도)
    
    # 예측 데이터 확인
    if not df_prediction.empty:
        예측_연도별_데이터수 = df_prediction.groupby("예상_연도")["공고명"].count()
        print("예측 데이터 연도별 개수:")
        print(예측_연도별_데이터수)
    
    # 원본 데이터와 예측 데이터 병합
    df_combined = pd.concat([df_processed, df_prediction], ignore_index=True)
    
    # 예상_년월 컬럼 추가
    df_combined["예상_년월"] = df_combined["예상_입찰일"].dt.strftime('%Y-%m')
    
    # 최종 결과 확인
    최종_연도별_데이터수 = df_combined.groupby("예상_연도")["공고명"].count()
    print("최종 데이터 연도별 개수:")
    print(최종_연도별_데이터수)
    
    return df_combined


def generate_prediction_data(df, prediction_years=30, 현재_데이터_연도=None):
    """
    용역기간이 끝나는 시점에 같은 공고가 다시 올라온다고 가정하여 예측 데이터 생성
    
    Args:
        df (pd.DataFrame): 원본 데이터프레임
        prediction_years (int): 예측할 최대 년수
        현재_데이터_연도 (set): 현재 데이터가 있는 연도 집합
    
    Returns:
        pd.DataFrame: 예측 데이터
    """
    predictions = []
    today = datetime.today()
    max_year = today.year + prediction_years
    
    # 현재 데이터가 있는 연도 집합이 None이면 비어있는 집합으로 초기화
    if 현재_데이터_연도 is None:
        현재_데이터_연도 = set()
    
    # 용역기간이 있는 공고만 대상으로 함
    valid_df = df[df["용역기간(개월)"] > 0].copy()
    
    print(f"예측 대상 공고 수: {len(valid_df)}")
    
    for _, row in valid_df.iterrows():
        current_date = row["예상_입찰일"]
        용역기간 = row["용역기간(개월)"]
        
        # 용역기간이 없는 경우 기본값 설정 (12개월)
        if 용역기간 <= 0:
            용역기간 = 12
            
        cycle = 1  # 첫 번째 예측 사이클
        
        # 최대 예측 년도까지 반복
        while True:
            # 다음 예측 공고일 계산 (용역기간이 끝나는 시점)
            next_date = current_date + pd.DateOffset(months=용역기간)
            
            # 최대 예측 년도를 넘어가면 중단
            if next_date.year > max_year:
                break
                
            # 이미 해당 연도에 현재 데이터가 있으면 예측 제외
            if next_date.year in 현재_데이터_연도:
                current_date = next_date
                cycle += 1
                continue
                
            # 새로운 예측 데이터 생성
            new_row = row.copy()
            new_row["공고_시작일"] = next_date
            new_row["예상_입찰일"] = next_date
            new_row["예상_연도"] = next_date.year
            new_row["예상_입찰월"] = next_date.month
            
            # 공고명에 예측 표시 추가
            new_row["공고명"] = f"{row['공고명']} (예측 {cycle}차)"
            
            # 입찰 결과 데이터 초기화 (예측이므로 결과는 없음)
            new_row["입찰결과_1순위"] = "예측"
            new_row["입찰금액_1순위"] = 0
            
            # 예측 데이터 추가
            predictions.append(new_row)
            
            # 다음 사이클 준비
            current_date = next_date
            cycle += 1
    
    # 예측 데이터가 없으면 빈 데이터프레임 반환
    if not predictions:
        return pd.DataFrame(columns=df.columns)
    
    # 예측 데이터를 데이터프레임으로 변환
    return pd.DataFrame(predictions)