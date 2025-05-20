import pandas as pd
import numpy as np
import re
from datetime import datetime

def preprocess_bid_data(input_csv: str, prediction_years: int = 30) -> pd.DataFrame:
    # CSV 파일 로딩
    df = pd.read_csv(input_csv)
    
    # 입찰일시 컬럼에서 날짜 정보 추출
    df["입찰일시"] = pd.to_datetime(df["입찰일시"])
    
    # 예상_입찰일 설정 (입찰일시에서 추출)
    df["예상_입찰일"] = df["입찰일시"].dt.date.apply(lambda x: pd.Timestamp(x))
    
    # 예상 연도와 월 컬럼 추가 (정렬 및 필터링용)
    df["예상_연도"] = df["예상_입찰일"].dt.year
    df["예상_입찰월"] = df["예상_입찰일"].dt.month
    df["예상_입찰일자"] = df["예상_입찰일"].dt.day  # 일자 정보 추가
    
    # 예상_년월 컬럼 추가 (YYYY-MM 형식)
    df["예상_년월"] = df["예상_입찰일"].dt.strftime('%Y-%m')
    
    # 예상_년월일 컬럼 추가 (YYYY-MM-DD 형식)
    df["예상_년월일"] = df["예상_입찰일"].dt.strftime('%Y-%m-%d')
    
    # 용역기간 정수형으로 변환
    df["용역기간(개월)"] = df["용역기간(개월)"].fillna(0).astype(int)
    
    # 숫자 데이터 정리 함수
    def clean_numeric(value):
        if pd.isna(value):
            return 0
        if isinstance(value, (int, float)):
            return value
        # 쉼표, 원, 기타 문자 제거 후 숫자만 추출
        cleaned = re.sub(r'[^\d.]', '', str(value))
        return float(cleaned) if cleaned else 0
    
    # 금액 컬럼 숫자로 변환 - 정수형으로 변환
    df["계약 기간 내"] = df["계약 기간 내"].apply(clean_numeric).astype(int)
    df["입찰금액_1순위"] = df["입찰금액_1순위"].apply(clean_numeric).astype(int)
    
    # 물동량 평균 숫자로 변환 - 정수형으로 변환
    df["물동량 평균"] = df["물동량 평균"].apply(clean_numeric).astype(int)
    
    # 텍스트 컬럼 정리
    df["실수요기관"] = df["실수요기관"].fillna("").astype(str).str.strip()
    df["공고명"] = df["공고명"].fillna("").astype(str).str.strip()
    df["입찰결과_1순위"] = df["입찰결과_1순위"].fillna("").astype(str).str.strip()
    
    # 필요한 컬럼만 선택
    df_processed = df[[
        "실수요기관", "공고명", "물동량 평균",
        "용역기간(개월)", "계약 기간 내", "입찰결과_1순위", "입찰금액_1순위",
        "예상_입찰일", "예상_연도", "예상_입찰월", "예상_입찰일자", 
        "예상_년월", "예상_년월일"
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
    
    # 예측 데이터 생성 (수정된 함수 호출)
    df_prediction = generate_prediction_data(df_processed, prediction_years)
    
    # 예측 데이터 확인
    if not df_prediction.empty:
        예측_연도별_데이터수 = df_prediction.groupby("예상_연도")["공고명"].count()
        print("예측 데이터 연도별 개수:")
        print(예측_연도별_데이터수)
    
    # 원본 데이터와 예측 데이터 병합
    df_combined = pd.concat([df_processed, df_prediction], ignore_index=True)
    
    # 최종 결과 확인
    최종_연도별_데이터수 = df_combined.groupby("예상_연도")["공고명"].count()
    print("최종 데이터 연도별 개수:")
    print(최종_연도별_데이터수)
    
    return df_combined


def generate_prediction_data(df, prediction_years=5):
    """
    기존 입찰 데이터를 기반으로 예측 데이터를 생성하는 함수
    
    Args:
        df (pandas.DataFrame): 원본 입찰 데이터
        prediction_years (int): 예측할 연도 수 (기본값: 5년)
        
    Returns:
        pandas.DataFrame: 생성된 예측 데이터
    """
    # 원본 데이터에서 용역기간이 있는 입찰 데이터만 선택 (예측공고 제외)
    valid_bids = df[(df["용역기간(개월)"] > 0) & (~df["공고명"].str.contains("예측", na=False))]
    
    if valid_bids.empty:
        print("용역기간이 설정된 입찰 데이터가 없어 예측을 생성할 수 없습니다.")
        return pd.DataFrame()
    
    # 현재 날짜 기준으로 예측 시작
    current_date = datetime.today()
    current_year = current_date.year
    
    # 예측 데이터를 저장할 리스트
    predictions = []
    
    # 원본 데이터의 최대 연도 확인 (로그용)
    max_original_year = df[~df["공고명"].str.contains("예측", na=False)]["예상_연도"].max() if not df.empty else current_year
    print(f"원본 데이터 최대 연도: {max_original_year}")
    
    # 각 입찰에 대해 예측 수행
    for _, bid in valid_bids.iterrows():
        # 기본 정보 복사
        original_date = bid["예상_입찰일"] if pd.notna(bid["예상_입찰일"]) else pd.NaT
        
        if pd.isna(original_date):
            continue
            
        # 용역기간이 없으면 건너뜀
        if pd.isna(bid["용역기간(개월)"]) or bid["용역기간(개월)"] <= 0:
            continue
            
        # 용역기간 기준으로 다음 예측일 계산 (용역기간-1 적용)
        service_months = max(1, int(bid["용역기간(개월)"]) - 1)  # 최소 1개월 보장
        
        # 첫 예측 시작 시점 계산
        next_date = original_date + pd.DateOffset(months=service_months)
        
        # 최대 예측 연도 설정
        max_prediction_year = current_year + prediction_years
        
        # 예측 루프 - 주어진 연도 범위 내에서 반복 예측
        # 첫 예측부터 시작 (최대 연도 제한 없음) - 모든 연도에 예측 데이터 생성
        while next_date.year <= max_prediction_year:
            prediction = bid.copy()
            
            # 예측 표시 추가
            prediction["공고명"] = f"{bid['공고명']} (예측)"
            
            # 원본 입찰일을 저장
            prediction["원본_입찰일"] = original_date
            
            # 예측 날짜 설정
            prediction["예상_입찰일"] = next_date
            prediction["예측_입찰일"] = next_date
            
            # 연도 및 월 정보 업데이트
            prediction["예상_연도"] = next_date.year
            prediction["예상_입찰월"] = next_date.month
            prediction["예상_년월"] = f"{next_date.year}-{next_date.month:02d}"
            
            # 입찰 결과 데이터 초기화 (예측이므로 결과는 없음)
            prediction["입찰결과_1순위"] = "예측"
            prediction["입찰금액_1순위"] = 0
            
            # 예측 플래그 추가
            prediction["is_prediction"] = True
            
            # 예측 데이터 추가
            predictions.append(prediction)
            
            # 다음 예측일 계산 (용역기간 주기로 반복)
            next_date += pd.DateOffset(months=service_months)
    
    # 예측 데이터가 없으면 빈 데이터프레임 반환
    if not predictions:
        return pd.DataFrame()
    
    # 예측 데이터를 데이터프레임으로 변환
    prediction_df = pd.DataFrame(predictions)
    
    print(f"총 {len(prediction_df)}개의 예측 데이터 생성 완료")
    if not prediction_df.empty:
        print(f"예측 연도 범위: {prediction_df['예상_연도'].min()} ~ {prediction_df['예상_연도'].max()}")
        print(f"예측 데이터 연도별 개수:")
        print(prediction_df.groupby("예상_연도")["공고명"].count())
    
    return prediction_df