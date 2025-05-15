from dash import Dash
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from preprocess import preprocess_bid_data
from layout import create_layout
import callbacks

# 애플리케이션 초기화
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# 데이터 로딩 및 전처리 (예측 데이터 포함, 30년 예측)
df = preprocess_bid_data("DB/2324List.csv", prediction_years=30)

# 항상 고정된 월 그룹 사용: (1-4), (5-8), (9-12)
months = list(range(1, 13))
month_groups = [months[i:i+4] for i in range(0, len(months), 4)]
today = datetime.today()

# 현재 월이 속한 그룹 찾기
default_page = next(i for i, group in enumerate(month_groups) if today.month in group)

initial_state = {
    "year": today.year,
    "month_page": default_page  # 현재 월이 포함된 그룹으로 시작
}

# 앱 레이아웃 설정
app.layout = create_layout(initial_state)

# 콜백 등록
callbacks.register_callbacks(app, df)

# 실행
if __name__ == "__main__":
    app.run(debug=True)