import pandas as pd
import numpy as np
import re

def preprocess_bid_data(input_csv: str) -> pd.DataFrame:
    # CSV 파일 로딩
    df = pd.read_csv(input_csv)
    
    # 연도, 월 데이터 정리
    df["년"] = df["년"].astype(str).str.extract(r'(\d{4})').astype(int)
    df["월"] = df["월"].astype(int)
    df["년월"] = df["년"].astype(str) + df["월"].astype(str).str.zfill(2)
    
    # 용역기간 정수형으로 변환
    df["용역기간(개월)"] = df["용역기간(개월)"].fillna(0).astype(int)
    
    # 날짜 형식 변환
    df["공고_시작일"] = pd.to_datetime(df["년"].astype(str) + "-" + df["월"].astype(str) + "-01")
    df["예상_입찰일"] = df["공고_시작일"] + pd.to_timedelta(df["용역기간(개월)"] * 30, unit='D')
    
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
    
    return df_processed