import pandas as pd

def preprocess_bid_data(input_csv: str) -> pd.DataFrame:
    df = pd.read_csv(input_csv)

    df["년"] = df["년"].astype(str).str.extract(r'(\d{4})').astype(int)
    df["월"] = df["월"].astype(int)
    df["년월"] = df["년"].astype(str) + df["월"].astype(str).str.zfill(2)
    df["용역기간(개월)"] = df["용역기간(개월)"].fillna(0).astype(int)

    df["공고_시작일"] = pd.to_datetime(df["년"].astype(str) + "-" + df["월"].astype(str) + "-01")
    df["예상_입찰일"] = df["공고_시작일"] + pd.to_timedelta(df["용역기간(개월)"] * 30, unit='D')

    df_processed = df[[
        "년", "월", "년월", "실수요기관", "공고명", "물동량 평균",
        "용역기간(개월)", "계약 기간 내", "입찰결과_1순위", "입찰금액_1순위",
        "공고_시작일", "예상_입찰일"
    ]]

    return df_processed
