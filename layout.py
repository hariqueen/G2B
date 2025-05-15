from dash import html, dcc, dash_table

def create_layout(initial_state):
    """앱 레이아웃 생성 함수
    
    Args:
        initial_state (dict): 초기 상태 정보 (연도, 월 페이지 등)
        
    Returns:
        dash.html.Div: 전체 앱 레이아웃
    """
    return html.Div([
        # 상단 타이틀
        html.H1("입찰 공고 목록 예측 대시보드", className="app-title"),
        
        # 연도 선택기
        html.Div([
            html.Button("<", id="prev-year-btn", className="month-nav-btn"),
            html.H3(id="year-display", className="year-display"),
            html.Button(">", id="next-year-btn", className="month-nav-btn"),
        ], className="year-selector"),
        
        # 예측 범례 추가
        html.Div([
            html.Div([
                html.Span("실제 공고", className="legend-item"),
                html.Span("🔮 예측 공고 (용역기간 종료 시점에 재발행 예상)", className="legend-item prediction-label"),
            ], className="prediction-legend")
        ], className="legend-container"),
        
        # 메인 컨텐츠 영역 (차트 + 다음 예정 입찰)
        html.Div([
            # 왼쪽 컬럼 - 차트
            html.Div([
                dcc.Graph(id="monthly-count-chart", style={"height": "320px"}),
            ], className="left-column"),
            
            # 오른쪽 컬럼 - 다음 예정 입찰 정보
            html.Div([
                html.H3("🗣️ 다음 예정 입찰 정보", className="section-title"),
                html.H4(id="next-bid-month", className="next-bid-title"),
                html.P(id="org-count", className="org-count"),
                
                # 다음/이전 버튼과 리스트를 감싸는 컨테이너 (가로 정렬)
                html.Div([
                    # 이전 버튼
                    html.Button("<", id="prev-page-btn", className="month-nav-btn"),
                    
                    # 기관 리스트 컨테이너
                    html.Div(id="org-list-container", className="org-list"),
                    
                    # 다음 버튼
                    html.Button(">", id="next-page-btn", className="month-nav-btn"),
                ], className="monthly-bids-wrapper"),
                
            ], className="right-column"),
        ], className="main-content"),
        
        # 월별 공고 리스트
        html.Div([
            html.Div([
                html.H3("🗂️ 월별 공고 리스트", id="monthly-list-title", className="section-title"),
            ], className="monthly-header"),
            
            html.Div(id="monthly-range-display", className="monthly-range"),
            
            html.Div([
                html.Button("<", id="prev-months-btn", className="month-nav-btn"),
                html.Div(id="monthly-bids-container", className="monthly-bids"),
                html.Button(">", id="next-months-btn", className="month-nav-btn"),
            ], className="monthly-bids-wrapper"),
        ], className="monthly-section-container"),
        
        # 전체 테이블 (토글 제거하고 항상 표시)
        html.Div([
            html.H3("📋 전체 공고 보기", className="section-title"),
            html.Div(id="full-table-container", className="full-table"),
        ], className="full-table-section"),
        
        # 예측 방법 설명
        html.Div([
            html.H3("🔮 예측 방법 설명", className="section-title"),
            html.P([
                "이 대시보드는 기존 공고의 용역기간을 기반으로 미래 공고를 예측합니다:",
                html.Br(),
                "1. 기존 공고의 용역기간이 종료되는 시점에 같은 공고가 다시 발행될 것으로 가정합니다.",
                html.Br(),
                "2. 예를 들어, 입찰월이 2025-12이고 용역기간이 12개월이면 2026-12월에 예측 공고가 표시됩니다.",
                html.Br(),
                "3. 예측 공고는 🔮 아이콘과 청색 테두리로 구분됩니다.",
            ], className="prediction-explanation"),
        ], className="prediction-section"),
        
        # 상태 저장용 hidden 요소들
        dcc.Store(id="selected-year", data=initial_state["year"]),
        dcc.Store(id="current-page", data=0),
        dcc.Store(id="selected-month", data=None),
        dcc.Store(id="selected-bid", data=None),
        dcc.Store(id="current-month-view", data=initial_state["month_page"]),
        
        html.Div(id="scroll-target-display", style={"display": "none"}),
        html.Div(id="scroll-trigger-result", style={"display": "none"}),
        html.Div(id="bid-auto-open-result", style={"display": "none"}),
    ])