from dash import Input, Output, State, callback_context, html, dash_table, ALL, no_update, dcc
import plotly.express as px
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go 

def register_callbacks(app, df):
    register_year_callbacks(app, df)
    register_info_callbacks(app, df)
    register_month_navigation_callbacks(app, df)
    register_bid_selection_callbacks(app, df)
    register_utility_callbacks(app, df)
    register_next_bid_navigation_callbacks(app, df)
    register_full_table_callbacks(app, df)
    register_edit_callbacks(app, df)
    
def register_year_callbacks(app, df):
    @app.callback(
        [Output("selected-year", "data"),
         Output("year-display", "children"),
         Output("current-month-view", "data"),
         Output("selected-bid", "data"), 
         Output("selected-month", "data")],  
        [Input("prev-year-btn", "n_clicks"),
         Input("next-year-btn", "n_clicks")],
        [State("selected-year", "data")],
        prevent_initial_call=False 
    )
    def update_selected_year(prev_clicks, next_clicks, current_year):
        ctx = callback_context
        today = datetime.today()
        
        # 월 그룹 정의 (1~4, 5~8, 9~12)
        months = list(range(1, 13))
        month_groups = [months[i:i+4] for i in range(0, len(months), 4)]
        
        # 현재 월이 속한 그룹 찾기
        default_page = next(i for i, g in enumerate(month_groups) if today.month in g)
        
        if not ctx.triggered:
            # 앱 초기 로드 시 - 현재 월이 속한 그룹 표시
            return current_year, f"{current_year}년", default_page, None, None

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "prev-year-btn" and prev_clicks:
            new_year = current_year - 1
        elif button_id == "next-year-btn" and next_clicks:
            new_year = current_year + 1
        else:
            new_year = current_year

        # 현재 연도일 경우 현재월 포함 그룹, 아니면 첫 그룹(1~4월)
        month_view = default_page if new_year == today.year else 0

        # 연도가 변경되면 선택된 bid와 month를 None으로 설정하여 초기화
        return new_year, f"{new_year}년", month_view, None, None


def register_info_callbacks(app, df):
    @app.callback(
    Output("monthly-count-chart", "figure"),
    Input("selected-year", "data")
    )
    def update_monthly_chart(selected_year):
        # 원본 데이터와 예측 데이터 구분
        original_df = df[~df["공고명"].str.contains("예측", na=False)]
        prediction_df = df[df["공고명"].str.contains("예측", na=False)]
        
        # 선택한 연도의 데이터 필터링
        year_original_df = original_df[original_df["예상_연도"] == selected_year]
        year_prediction_df = prediction_df[prediction_df["예상_연도"] == selected_year]
        
        # 해당 연도에 데이터가 없으면 빈 차트 반환
        if year_original_df.empty and year_prediction_df.empty:
            # 모든 월 (1-12) 생성
            all_months = pd.DataFrame({"예상_입찰월": range(1, 13)})
            all_months["월"] = all_months["예상_입찰월"].astype(str) + "월"
            all_months["공고수"] = 0
            all_months["물동량"] = 0
            
            # 빈 차트 생성
            fig = go.Figure()
            
            # 막대 차트 추가 (물동량 평균) - 0으로 표시
            fig.add_trace(go.Bar(
                x=all_months["월"],
                y=all_months["물동량"],
                name="물동량(M/M)",
                marker_color="#17becf",
                hovertemplate="물동량: %{y:,.0f} 명<extra></extra>"
            ))
            
            # 선 차트 추가 (공고 수) - 0으로 표시
            fig.add_trace(go.Scatter(
                x=all_months["월"],
                y=all_months["공고수"],
                name="공고 수",
                mode="lines+markers",
                marker_color="#d62728",
                line=dict(width=3),
                yaxis="y2",
                hovertemplate="공고 수: %{y} 건<extra></extra>"
            ))
            
            # 레이아웃 설정
            fig.update_layout(
                title=f"{selected_year}년 월별 물동량 및 공고 현황",
                title_font_size=20,
                xaxis_title=None,
                yaxis=dict(
                    title="물동량(명)",
                    titlefont=dict(color="#17becf"),
                    tickfont=dict(color="#17becf")
                ),
                yaxis2=dict(
                    title="공고 수(건)",
                    titlefont=dict(color="#d62728"),
                    tickfont=dict(color="#d62728"),
                    anchor="x",
                    overlaying="y",
                    side="right"
                ),
                plot_bgcolor="white",
                margin=dict(l=20, r=60, t=50, b=20),
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                showlegend=True
            )
            
            return fig
        
        # 1. 월별 원본 공고 수 계산
        if not year_original_df.empty:
            monthly_counts_original = year_original_df.groupby("예상_입찰월")["공고명"].count().reset_index()
            monthly_counts_original.rename(columns={"공고명": "공고수_원본"}, inplace=True)
            
            # 월별 평균 물동량 계산 (원본)
            monthly_mm_original = year_original_df.groupby("예상_입찰월")["물동량 평균"].sum().reset_index()
            monthly_mm_original.rename(columns={"물동량 평균": "물동량_원본"}, inplace=True)
        else:
            # 원본 데이터가 없는 경우 빈 DataFrame 생성
            monthly_counts_original = pd.DataFrame({"예상_입찰월": [], "공고수_원본": []})
            monthly_mm_original = pd.DataFrame({"예상_입찰월": [], "물동량_원본": []})
        
        # 2. 월별 예측 공고 수 계산
        if not year_prediction_df.empty:
            monthly_counts_prediction = year_prediction_df.groupby("예상_입찰월")["공고명"].count().reset_index()
            monthly_counts_prediction.rename(columns={"공고명": "공고수_예측"}, inplace=True)
            
            # 월별 평균 물동량 계산 (예측)
            monthly_mm_prediction = year_prediction_df.groupby("예상_입찰월")["물동량 평균"].sum().reset_index()
            monthly_mm_prediction.rename(columns={"물동량 평균": "물동량_예측"}, inplace=True)
        else:
            # 예측 데이터가 없는 경우 빈 DataFrame 생성
            monthly_counts_prediction = pd.DataFrame({"예상_입찰월": [], "공고수_예측": []})
            monthly_mm_prediction = pd.DataFrame({"예상_입찰월": [], "물동량_예측": []})
        
        # 3. 데이터 병합
        all_months = pd.DataFrame({"예상_입찰월": range(1, 13)})
        all_months["월"] = all_months["예상_입찰월"].astype(str) + "월"
        
        # 원본 공고 수 데이터 병합
        all_months = pd.merge(all_months, monthly_counts_original, on="예상_입찰월", how="left")
        all_months["공고수_원본"] = all_months["공고수_원본"].fillna(0).astype(int)
        
        # 원본 물동량 데이터 병합
        all_months = pd.merge(all_months, monthly_mm_original, on="예상_입찰월", how="left")
        all_months["물동량_원본"] = all_months["물동량_원본"].fillna(0).astype(int)
        
        # 예측 공고 수 데이터 병합
        all_months = pd.merge(all_months, monthly_counts_prediction, on="예상_입찰월", how="left")
        all_months["공고수_예측"] = all_months["공고수_예측"].fillna(0).astype(int)
        
        # 예측 물동량 데이터 병합
        all_months = pd.merge(all_months, monthly_mm_prediction, on="예상_입찰월", how="left")
        all_months["물동량_예측"] = all_months["물동량_예측"].fillna(0).astype(int)
        
        # 4. 단일 데이터셋 생성 (예측이 있으면 예측, 없으면 원본)
        all_months["물동량"] = all_months.apply(
            lambda row: row["물동량_예측"] if row["물동량_예측"] > 0 else row["물동량_원본"], 
            axis=1
        )
        
        all_months["공고수"] = all_months.apply(
            lambda row: row["공고수_예측"] if row["공고수_예측"] > 0 else row["공고수_원본"], 
            axis=1
        )
        
        # 5. 예측 데이터 있는 월 표시하기 위한 플래그
        all_months["is_prediction"] = all_months["물동량_예측"] > 0
        
        # 차트 생성
        fig = go.Figure()
        
        # 막대 차트 추가 (물동량 - 단일 시리즈)
        fig.add_trace(go.Bar(
            x=all_months["월"],
            y=all_months["물동량"],
            name="물동량(M/M)",
            marker_color="#17becf",
            marker=dict(
                color=all_months.apply(
                    lambda row: "#17becf" if row["is_prediction"] else "#1f77b4", 
                    axis=1
                )
            ),
            hovertemplate="물동량: %{y:,.0f} 명<extra></extra>",
        ))
        
        # 선 차트 추가 (공고 수 - 단일 시리즈)
        fig.add_trace(go.Scatter(
            x=all_months["월"],
            y=all_months["공고수"],
            name="공고 수",
            mode="lines+markers",
            marker_color="#d62728",
            marker=dict(
                color=all_months.apply(
                    lambda row: "#d62728" if row["is_prediction"] else "#ff7f0e", 
                    axis=1
                )
            ),
            line=dict(width=3),
            yaxis="y2",
            hovertemplate="물동량: %{y:,.0f} 명<extra></extra>",
        ))
        
        # 예측 데이터 있는 경우에만 예측 표시 추가
        has_prediction = all_months["is_prediction"].any()
        
        # 레이아웃 설정
        fig.update_layout(
            title=f"{selected_year}년 월별 물동량 및 공고 현황 예측",
            title_font_size=20,
            xaxis_title=None,
            yaxis=dict(
                title="물동량(명)",
                titlefont=dict(color="#17becf"),
                tickfont=dict(color="#17becf")
            ),
            yaxis2=dict(
                title="공고 수(건)",
                titlefont=dict(color="#d62728"),
                tickfont=dict(color="#d62728"),
                anchor="x",
                overlaying="y",
                side="right"
            ),
            plot_bgcolor="white",
            margin=dict(l=20, r=60, t=50, b=20),
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            showlegend=True
        )
        
        # 그리드 라인 추가
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
        
    @app.callback(
    [Output("next-bid-month", "children"),
    Output("org-count", "children"),
    Output("org-list-container", "children")],
    [Input("selected-year", "data"),
    Input("current-page", "data")]
    )
    def update_next_bids(selected_year, current_page):
        today = datetime.today()
        
        # 다음 달의 1일 계산
        current_month = today.month
        current_year = today.year
        
        if current_month == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = current_month + 1
            next_year = current_year
        
        next_month_start = datetime(next_year, next_month, 1)
        next_month_str = f"{next_year}-{next_month:02d}"  # 형식: "YYYY-MM"
        
        print(f"다음 달 시작일: {next_month_start}")
        print(f"다음 달 문자열: {next_month_str}")
        
        # 선택된 연도에 맞게 모든 데이터 표시
        # 원본 데이터와 예측 데이터 모두 표시 (원본과 예측 구분없이 모두 표시)
        if selected_year == current_year:
            # 현재 연도인 경우 다음 달부터 시작하는 모든 공고 표시 (원본+예측)
            upcoming_df = df[df["예상_입찰일"] >= next_month_start].copy()
        else:
            # 다른 연도인 경우 해당 연도의 모든 공고 표시 (원본+예측)
            upcoming_df = df[df["예상_연도"] == selected_year].copy()
        
        print(f"다음 예정 입찰 데이터 수: {len(upcoming_df)}")
        
        # 데이터가 없는 경우
        if upcoming_df.empty:
            return "다음 입찰 예상월: 없음", "🏢 실수요기관 수: 0곳", []
        
        # 데이터 확인
        print(f"첫 번째 입찰 일자: {upcoming_df['예상_입찰일'].min()}")
        print(f"마지막 입찰 일자: {upcoming_df['예상_입찰일'].max()}")
        
        # NaT 값 처리 추가
        upcoming_df["예상_년월"] = upcoming_df["예상_입찰일"].dt.strftime("%Y-%m").fillna("")
        
        월순서 = sorted([m for m in upcoming_df["예상_년월"].unique() if m])
        print(f"월 순서: {월순서}")
        
        # 중요 변경: 다음 달 또는 그 이후에 가장 가까운 월 찾기
        if current_page == 0 and selected_year == current_year:  # 초기 페이지이고 현재 연도일 때만 자동으로 다음 달 선택
            # next_month_str 이후의 가장 가까운 월 찾기
            future_months = [m for m in 월순서 if m >= next_month_str]
            if future_months:
                current_month = future_months[0]  # 다음 달 이후의 첫 번째 달
                # current_page 값도 업데이트
                current_page = 월순서.index(current_month)
            else:
                # 다음 달 이후 데이터가 없으면 가장 최근 월 선택
                current_month = 월순서[-1] if 월순서 else None
                current_page = len(월순서) - 1 if 월순서 else 0
        else:
            # 사용자가 페이지를 변경했거나 다른 연도인 경우 해당 페이지 사용
            if 월순서 and current_page < len(월순서):
                current_month = 월순서[current_page]
            else:
                current_month = 월순서[0] if 월순서 else None
                current_page = 0
        
        target_months = [current_month] if current_month else []
        print(f"선택된 타겟 월: {target_months}, 페이지: {current_page}")
        
        # 타겟 월에 해당하는 데이터가 없는 경우
        if not target_months:
            return "다음 입찰 예상월: 없음", "🏢 실수요기관 수: 0곳", []
        
        target_df = upcoming_df[upcoming_df["예상_년월"].isin(target_months)]
        target_월 = target_months[0] if target_months else "N/A"
        기관_리스트 = sorted(target_df["실수요기관"].unique())
        
        start = 0
        end = len(기관_리스트)
        page_기관 = 기관_리스트[start:end]
        기관_총수 = len(기관_리스트)
        
        # 공고 수 계산
        total_count = len(target_df)
        
        # 예측 데이터 개수 계산
        prediction_count = len(target_df[target_df["공고명"].str.contains("예측")])
        original_count = total_count - prediction_count
        
        # 원본과 예측 데이터 비율 계산
        target_info = f"(원본: {original_count}건, 예측: {prediction_count}건)"
        
        # 예측 데이터에 대한 원본 입찰일 계산
        if "원본_입찰일" not in target_df.columns:
            target_df["원본_입찰일"] = pd.NaT
            for idx, row in target_df.iterrows():
                if "예측" in str(row["공고명"]):
                    if pd.notna(row["용역기간(개월)"]) and row["용역기간(개월)"] > 0:
                        target_df.at[idx, "원본_입찰일"] = row["예상_입찰일"] - pd.DateOffset(months=int(row["용역기간(개월)"]))
        
        org_list = []
        for name in page_기관:
            기관공고_df = target_df[target_df["실수요기관"] == name]
            
            # 원본 공고와 예측 공고 구분
            기관공고_원본 = 기관공고_df[~기관공고_df["공고명"].str.contains("예측")]
            기관공고_예측 = 기관공고_df[기관공고_df["공고명"].str.contains("예측")]
            
            # 두 데이터셋을 합치고 정렬
            공고_리스트 = pd.concat([기관공고_원본, 기관공고_예측]).sort_values("예상_입찰일")
            
            buttons = []
            for i, (_, row) in enumerate(공고_리스트.iterrows()):
                # NaT 값 안전하게 처리
                is_prediction = "예측" in str(row["공고명"])
                data_year = str(row["예상_입찰일"].year) if pd.notna(row["예상_입찰일"]) else ""
                data_month = row["예상_년월"] if pd.notna(row["예상_년월"]) else ""
                original_month = row["원본_입찰일"].strftime('%Y-%m') if pd.notna(row["원본_입찰일"]) else "-"
                
                # 예측 공고와 원본 공고를 시각적으로 구분
                button_style = {"background-color": "#f0f8ff"} if is_prediction else {}
                button_prefix = ""
                
                button = html.Button(
                    f"{button_prefix}{row['공고명']}",
                    id={"type": "bid-btn", "index": f"{name}_{i}"},
                    className="bid-button",
                    style=button_style,
                    **{
                        "data-month": data_month,
                        "data-year": data_year,
                        "data-bid": str(row['공고명']),
                        "data-original-month": original_month,
                        "data-is-prediction": "1" if is_prediction else "0"
                    }
                )
                buttons.append(button)
            
            # 원본과 예측 공고 개수 표시
            전체_개수 = len(기관공고_원본) + len(기관공고_예측)
            공고_개수_표시 = f"({전체_개수}건)"
            
            org_details = html.Details([
                html.Summary(f"{name} {공고_개수_표시}", className="org-name"),
                html.Div([
                    html.H4(f"🏢 {name} - 예정 공고", className="org-title"),
                    html.Div(buttons, className="bid-buttons-container")
                ], className="org-details-content")
            ], className="org-details")
            
            org_list.append(org_details)
        
        # 월 표시 (예측 정보 추가)
        month_display = f"다음 입찰 예상월: {target_월} (총 {total_count}건) {target_info}"
        
        # 현재 페이지도 업데이트
        dcc.Store(id="current-page", data=current_page)
                
        return month_display, f"🏢 실수요기관 수: {기관_총수}곳", org_list


def register_month_navigation_callbacks(app, df):
    @app.callback(
    [
        Output("current-month-view", "data", allow_duplicate=True),
        Output("selected-year", "data", allow_duplicate=True),
    ],
    [Input("prev-months-btn", "n_clicks"), Input("next-months-btn", "n_clicks")],
    [State("current-month-view", "data"), State("selected-year", "data")],
    prevent_initial_call=True
)
    def update_month_page(prev_clicks, next_clicks, current_view, selected_year):
        ctx = callback_context
        button_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        months = list(range(1, 13))
        month_groups = [months[i:i+4] for i in range(0, len(months), 4)]
        max_page = len(month_groups) - 1

        if button_id == "prev-months-btn":
            if current_view > 0:
                return current_view - 1, selected_year
            else:
                return max_page, selected_year - 1  # 전년도 마지막 그룹

        elif button_id == "next-months-btn":
            if current_view < max_page:
                return current_view + 1, selected_year
            else:
                return 0, selected_year + 1  # 다음년도 첫 그룹

        return current_view, selected_year

    @app.callback(
    [
        Output("selected-month", "data", allow_duplicate=True),
        Output("current-month-view", "data", allow_duplicate=True),
        Output("selected-year", "data", allow_duplicate=True),
    ],
    Input("month-selector", "value"),
    [State("selected-year", "data")],
    prevent_initial_call=True
)
    def select_month_from_dropdown(selected_month, selected_year):
        if not selected_month:
            return no_update, no_update, no_update

        selected_month_num = int(selected_month.split("-")[1])
        months = list(range(1, 13))
        month_groups = [months[i:i+4] for i in range(0, len(months), 4)]

        # 선택한 월이 속한 그룹 찾기
        for idx, group in enumerate(month_groups):
            if selected_month_num in group:
                return selected_month, idx, no_update
        
        return selected_month, no_update, no_update

    @app.callback(
    [Output("monthly-bids-container", "children"),
     Output("monthly-range-display", "children"),
     Output("prev-months-btn", "disabled"),
     Output("next-months-btn", "disabled")],
    [Input("selected-year", "data"),
     Input("current-month-view", "data"),
     Input("selected-month", "data"),
     Input("selected-bid", "data")]
    )
    def update_monthly_bids(selected_year, current_month_view, selected_month, selected_bid):
        months = list(range(1, 13))
        month_groups = [months[i:i+4] for i in range(0, len(months), 4)]
        view_month_nums = month_groups[current_month_view] if current_month_view < len(month_groups) else []

        # 전체 데이터에서 선택된 연도의 데이터만 필터링
        year_df = df[df["예상_연도"] == selected_year]
        
        view_months = year_df[year_df["예상_입찰월"].isin(view_month_nums)]["예상_년월"].unique()
        view_months = sorted(view_months)

        max_pages = len(month_groups) - 1
        
        # 이전/다음 버튼을 항상 활성화 (다른 연도로 이동 가능)
        prev_button_disabled = False
        next_button_disabled = False

        if not view_months:
            return html.Div("이 연도에 해당하는 공고가 없습니다.", className="no-months-message"), f"{selected_year}년 {view_month_nums[0]}월-{view_month_nums[-1]}월 공고 없음", prev_button_disabled, next_button_disabled

        range_display = f"현재 보기: {view_month_nums[0]}월 ~ {view_month_nums[-1]}월 ({current_month_view + 1}/{max_pages + 1}페이지)"

        month_cells = []
        for m in view_months:
            month_data = year_df[year_df["예상_년월"] == m]
            anchor_id = f"anchor-{m}"
            is_selected = (m == selected_month)
            emphasis = "📍 " if is_selected else ""
            section_style = {
                'backgroundColor': '#fff3cd' if is_selected else 'white',
                'border': '1px solid #ffeeba' if is_selected else '1px solid #dee2e6',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
                'padding': '15px'
            }

            month_bids = []
            if month_data.empty:
                month_bids.append(html.P("_(해당 월 공고 없음)_", className="no-bids"))
            else:
                # 원본 데이터와 예측 데이터 구분
                month_original = month_data[~month_data["공고명"].str.contains("예측", na=False)]
                month_prediction = month_data[month_data["공고명"].str.contains("예측", na=False)]
                month_title = f"{emphasis}{m}"  
                
                # 두 데이터 함께 정렬 (공고명 기준)
                sorted_data = pd.concat([month_original, month_prediction]).sort_values(by=["공고명"])
                
                for _, row in sorted_data.iterrows():
                    highlight = (row["공고명"] == selected_bid)
                    
                    # 예측 공고인지 확인
                    is_prediction = "예측" in str(row["공고명"])
                    emoji = "📌" 
                    
                    # 스타일 설정
                    summary_class = "bid-summary"
                    if highlight:
                        summary_class += " highlighted"
                    if is_prediction:
                        summary_class += " prediction"
                    
                    # 예측 입찰일 계산 - "예측_입찰일" 컬럼이 있으면 그 값을 사용, 없으면 계산
                    if is_prediction and "예측_입찰일" in row and pd.notna(row["예측_입찰일"]):
                        predicted_date = row["예측_입찰일"].strftime('%Y-%m-%d') if not pd.isna(row["예측_입찰일"]) else "-"
                    elif not is_prediction and pd.notna(row["예상_입찰일"]) and pd.notna(row["용역기간(개월)"]) and row["용역기간(개월)"] > 0:
                        # 용역기간 기반 예측 계산 (용역기간-1개월 적용)
                        adjusted_period = max(1, int(row["용역기간(개월)"]) - 1)  # 최소 1개월 보장
                        predicted_date = row["예상_입찰일"] + pd.DateOffset(months=adjusted_period)
                        predicted_date = predicted_date.strftime('%Y-%m-%d') if not pd.isna(predicted_date) else "-"
                    else:
                        predicted_date = "-"
                    
                    # 안전한 숫자 포맷팅 함수
                    def safe_format_number(value, suffix=""):
                        if value == 0 or pd.isna(value) or value == "":
                            return "-"
                        try:
                            # 문자열인 경우 쉼표 제거
                            if isinstance(value, str):
                                value = value.replace(',', '')
                            # 정수로 변환 후 천 단위 쉼표 포맷팅
                            return f"{int(float(value)):,} {suffix}".strip()
                        except (ValueError, TypeError):
                            # 변환 실패 시 원본 반환
                            return f"{value} {suffix}".strip()
                    
                    # 숫자 값 포맷팅 - 안전하게 처리
                    mm_value = safe_format_number(row['물동량 평균'], "명")
                    contract_value = safe_format_number(row['계약 기간 내'], "원")
                    bid_value = safe_format_number(row['입찰금액_1순위'], "원")
                    
                    # 용역기간 표시 처리
                    duration = row['용역기간(개월)']
                    duration_display = '-' if duration == 0 else f'{duration} 개월'
                    
                    # 입찰일 형식을 YYYY-MM-DD로 변경
                    bid_date = row['예상_입찰일'].strftime('%Y-%m-%d') if pd.notna(row['예상_입찰일']) else '-'
                    
                    # 원본 입찰일 표시 (예측 공고인 경우만)
                    original_date_display = ""
                    if is_prediction and "원본_입찰일" in row and pd.notna(row["원본_입찰일"]):
                        original_date = row["원본_입찰일"].strftime('%Y-%m-%d')
                        original_date_display = html.P(f"원본입찰일: {original_date}", className="bid-detail")
                    
                    # 예측 공고와 원본 공고에 따라 약간 다른 정보 표시
                    if is_prediction:
                        # 예측 차수 정보 추출 - 공고명에서 "n차 예측" 형식 추출
                        prediction_label = " (예측)"
                        if "차 예측" in row['공고명']:
                            # "n차 예측" 형식 추출
                            import re
                            match = re.search(r'(\d+차 예측)', row['공고명'])
                            if match:
                                prediction_label = f" ({match.group(1)})"
                        
                        # 공고명에서 예측 표시 제거 (n차 예측 포함)
                        clean_name = re.sub(r' \(\d+차 예측\)| \(예측\)', '', row['공고명'])
                        
                        # 예측 공고용 상세 정보
                        bid_details = html.Details([
                            html.Summary([
                                f"{clean_name}",
                                html.Span(prediction_label, className="prediction-label")
                            ], className=summary_class),
                            html.Div([
                                html.P(f"실수요기관: {row['실수요기관'] if row['실수요기관'] else '-'}", className="bid-detail"),
                                html.P(f"예측입찰게시: {bid_date}", className="bid-detail"),
                                original_date_display,
                                html.P(f"평균M/M: {mm_value}", className="bid-detail"),
                                html.P(f"용역기간: {duration_display}", className="bid-detail"),
                                html.P(f"계약금액: {contract_value}", className="bid-detail"),
                            ])
                        ])
                    else:
                        # 원본 공고용 상세 정보
                        bid_details = html.Details([
                            html.Summary(f"{emoji} {row['공고명']}", className=summary_class),
                            html.Div([
                                html.P(f"실수요기관: {row['실수요기관'] if row['실수요기관'] else '-'}", className="bid-detail"),
                                html.P(f"입찰게시: {bid_date}", className="bid-detail"),
                                html.P(f"(예측)입찰게시: {predicted_date}", className="bid-detail"),
                                html.P(f"평균M/M: {mm_value}", className="bid-detail"),
                                html.P(f"용역기간: {duration_display}", className="bid-detail"),
                                html.P(f"계약금액: {contract_value}", className="bid-detail"),
                                html.P(f"(1순위)입찰업체: {'-' if row['입찰결과_1순위'] == '예측' or not row['입찰결과_1순위'] else row['입찰결과_1순위']}", className="bid-detail"),
                                html.P(f"(1순위)입찰금액: {bid_value}", className="bid-detail"),
                            ])
                        ])
                    
                    month_bids.append(bid_details)

                section = html.Div([
                    html.Div(id=anchor_id, className="anchor-point"),
                    html.H3(month_title, className="month-title"),
                    html.Div(month_bids, className="month-bids-list")
                ], className="month-section", style=section_style)
                month_cells.append(html.Div(section, className="month-cell"))

        return month_cells, range_display, prev_button_disabled, next_button_disabled
            
def register_bid_selection_callbacks(app, df):
    @app.callback(
        [Output("selected-month", "data", allow_duplicate=True),
        Output("selected-bid", "data", allow_duplicate=True),  # 여기에 allow_duplicate=True 추가
        Output("scroll-target-display", "children"),
        Output("current-month-view", "data", allow_duplicate=True),
        Output("selected-year", "data", allow_duplicate=True)],
        [Input({"type": "bid-btn", "index": ALL}, "n_clicks")],
        [State({"type": "bid-btn", "index": ALL}, "data-month"),
        State({"type": "bid-btn", "index": ALL}, "data-bid"),
        State("selected-year", "data")],
        prevent_initial_call=True
    )
    def update_selection(n_clicks, months, bids, selected_year):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks):
            return no_update, no_update, no_update, no_update, no_update

        try:
            for i, n in enumerate(n_clicks):
                if n:
                    selected_month = months[i]
                    selected_bid = bids[i]
                    new_selected_year = int(selected_month.split("-")[0])
                    target_id = f"anchor-{selected_month}"
                    
                    selected_month_num = int(selected_month.split("-")[1])
                    months_range = list(range(1, 13))
                    month_groups = [months_range[i:i+4] for i in range(0, len(months_range), 4)]

                    for idx, group in enumerate(month_groups):
                        if selected_month_num in group:
                            return selected_month, selected_bid, target_id, idx, new_selected_year
        except Exception as e:
            print("선택 오류:", e)

        return no_update, no_update, no_update, no_update, no_update

    # 자동 펼침 기능을 위한 콜백 - 원래 코드 유지
    app.clientside_callback(
        """
        function(selectedBid) {
            if (selectedBid) {
                setTimeout(function() {
                    // 월별 공고 리스트에서 모든 details 요소 닫기
                    const allBidDetails = document.querySelectorAll('.month-bids-list details');
                    for (let detail of allBidDetails) {
                        if (detail.hasAttribute('open')) {
                            detail.removeAttribute('open');
                        }
                    }
                    
                    // 다음 예정 입찰 정보 섹션에서 모든 기관 details도 닫기
                    const allOrgDetails = document.querySelectorAll('.org-details');
                    for (let orgDetail of allOrgDetails) {
                        if (orgDetail.hasAttribute('open')) {
                            orgDetail.removeAttribute('open');
                        }
                    }
                    
                    // 다음 예정 입찰 정보에서 현재 선택된 공고가 있는 기관만 열기
                    const orgBidButtons = document.querySelectorAll('.bid-button');
                    let foundOrg = false;
                    
                    for (let bidButton of orgBidButtons) {
                        if (bidButton.innerText.includes(selectedBid)) {
                            // 이 버튼이 속한 기관 details 찾기
                            const orgDetails = bidButton.closest('.org-details');
                            if (orgDetails) {
                                orgDetails.setAttribute('open', '');
                                foundOrg = true;
                            }
                            break;
                        }
                    }
                    
                    // 월별 공고 리스트에서 선택된 공고 찾아서 열기
                    const summaries = document.querySelectorAll('.bid-summary');
                    
                    for (let summary of summaries) {
                        if (summary.textContent.includes(selectedBid)) {
                            const details = summary.closest('details');
                            if (details) {
                                details.setAttribute('open', '');
                                
                                summary.style.backgroundColor = '#ffeb3b';
                                setTimeout(function() {
                                    summary.style.backgroundColor = '';
                                }, 1500);
                            }
                            break;
                        }
                    }
                }, 500);
            }
            return '';
        }
        """,
        Output("bid-auto-open-result", "children"),
        Input("selected-bid", "data")
    )

def register_utility_callbacks(app, df):
    # 기존 스크롤 콜백 유지
    app.clientside_callback(
        """
        function(targetId, selectedYear) {
            if (targetId) {
                // 연도 변경 후 DOM이 업데이트되길 기다리기 위해 타임아웃 증가
                setTimeout(function() {
                    const element = document.getElementById(targetId);
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth', block: 'start'});
                        element.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
                        setTimeout(function() {
                            element.style.backgroundColor = 'transparent';
                        }, 2000);
                        return '스크롤 성공';
                    } else {
                        // 첫 시도에서 요소를 찾을 수 없으면 다시 시도
                        setTimeout(function() {
                            const retryElement = document.getElementById(targetId);
                            if (retryElement) {
                                retryElement.scrollIntoView({behavior: 'smooth', block: 'start'});
                                retryElement.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
                                setTimeout(function() {
                                    retryElement.style.backgroundColor = 'transparent';
                                }, 2000);
                            }
                        }, 800);  // 추가 지연 시간
                        return '요소를 찾을 수 없음 - 재시도';
                    }
                }, 600);  // 지연 시간 증가
            }
            return '';
        }
        """,
        Output("scroll-trigger-result", "children"),
        [Input("scroll-target-display", "children"),
         Input("selected-year", "data")]  # selected-year도 입력으로 추가
    )
    
    # 연도 변경 시 details 닫는 새로운 콜백 추가
    app.clientside_callback(
        """
        function(selectedYear) {
            // 연도 변경 시 모든 details 닫기
            window.lastYear = window.lastYear || selectedYear;
            
            // 연도가 변경된 경우에만 실행
            if (selectedYear !== window.lastYear) {
                setTimeout(function() {
                    // 월별 공고 리스트의 모든 details 닫기
                    const allBidDetails = document.querySelectorAll('.month-bids-list details');
                    for (let i = 0; i < allBidDetails.length; i++) {
                        if (allBidDetails[i].hasAttribute('open')) {
                            allBidDetails[i].removeAttribute('open');
                        }
                    }
                    
                    // 기관 details 닫기
                    const allOrgDetails = document.querySelectorAll('.org-details');
                    for (let i = 0; i < allOrgDetails.length; i++) {
                        if (allOrgDetails[i].hasAttribute('open')) {
                            allOrgDetails[i].removeAttribute('open');
                        }
                    }
                }, 100);
            }
            
            // 현재 연도 저장
            window.lastYear = selectedYear;
            return selectedYear;
        }
        """,
        Output("year-change-close-result", "children"),
        Input("selected-year", "data")
    )

def register_next_bid_navigation_callbacks(app, df):
    @app.callback(
        Output("current-page", "data"),
        [Input("prev-page-btn", "n_clicks"),
         Input("next-page-btn", "n_clicks")],
        [State("current-page", "data"),
         State("selected-year", "data")]
    )
    def update_next_bids_page(prev_clicks, next_clicks, current_page, selected_year):
        ctx = callback_context
        if not ctx.triggered:
            return current_page

        today = datetime.today()
        next_month = datetime(today.year + (today.month == 12), (today.month % 12) + 1, 1)
        
        upcoming_df = df[df["예상_입찰일"] >= next_month].copy()
        upcoming_df["예상_년월"] = upcoming_df["예상_입찰일"].dt.strftime("%Y-%m")
        
        월순서 = sorted(upcoming_df["예상_년월"].unique())
        max_page = len(월순서) - 1
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "prev-page-btn" and prev_clicks and current_page > 0:
            return current_page - 1
        elif button_id == "next-page-btn" and next_clicks and current_page < max_page:
            return current_page + 1
        
        return current_page

def register_full_table_callbacks(app, df):
    @app.callback(
    [Output("full-table-container", "children"),
     Output("update-status-table", "children", allow_duplicate=True)],
    Input("selected-year", "data"),
    prevent_initial_call=True
    )
    def update_full_table(selected_year):
        # 원본 데이터의 최대 연도 확인
        max_original_year = df[~df["공고명"].str.contains("예측")]["예상_연도"].max() if not df[~df["공고명"].str.contains("예측")].empty else datetime.today().year
        print(f"원본 데이터 최대 연도: {max_original_year}, 선택 연도: {selected_year}")
        
        # 선택한 연도가 원본 데이터 최대 연도보다 크면 예측 데이터만 표시
        if selected_year > max_original_year:
            year_df = df[(df["예상_연도"] == selected_year) & (df["공고명"].str.contains("예측", case=False))].copy()
        else:
            year_df = df[df["예상_연도"] == selected_year].copy()
        
        if year_df.empty:
            return html.Div("선택한 연도에 해당하는 공고가 없습니다.", className="no-data-message"), no_update
        
        # 테이블에 표시할 데이터 정렬
        year_df = year_df.sort_values(by="예상_입찰일")
        
        # 현재 연도보다 이전 연도인지 확인 (과거 데이터)
        current_year = datetime.today().year
        is_past_data = selected_year < current_year
        
        # 미래 데이터 (예측 데이터)인지 확인
        is_future_data = selected_year > max_original_year
        
        # 예측 데이터 처리
        for idx, row in year_df.iterrows():
            # 예측 공고인 경우
            if "예측" in str(row["공고명"]):
                # 원본_입찰일이 있는지 확인하고 없으면 계산
                if "원본_입찰일" not in year_df.columns or pd.isna(row.get("원본_입찰일")):
                    if pd.notna(row["용역기간(개월)"]) and row["용역기간(개월)"] > 0:
                        # 예측일에서 용역기간을 빼서 원래 입찰일 계산
                        original_date = row["예상_입찰일"] - pd.DateOffset(months=int(row["용역기간(개월)"]))
                        if "원본_입찰일" not in year_df.columns:
                            year_df["원본_입찰일"] = pd.NaT
                        year_df.at[idx, "원본_입찰일"] = original_date
                
                # 입찰게시와 예측입찰게시 분리
                if "예측_입찰일" not in year_df.columns:
                    year_df["예측_입찰일"] = pd.NaT
                    
                # 용역기간 기반 예측 계산 (용역기간-1개월 적용)
                if pd.notna(row["예상_입찰일"]) and pd.notna(row["용역기간(개월)"]) and row["용역기간(개월)"] > 0:
                    # 용역기간에서 1개월 차감
                    adjusted_period = max(1, int(row["용역기간(개월)"]) - 1)  # 최소 1개월 보장
                    year_df.at[idx, "예측_입찰일"] = row["원본_입찰일"] + pd.DateOffset(months=adjusted_period)
                else:
                    year_df.at[idx, "예측_입찰일"] = row["예상_입찰일"]  # 원본 예측일 사용
                
                # 원본 입찰일이 있으면 예상_입찰일을 원본_입찰일로 교체
                if "원본_입찰일" in year_df.columns and pd.notna(year_df.at[idx, "원본_입찰일"]):
                    year_df.at[idx, "예상_입찰일"] = year_df.at[idx, "원본_입찰일"]
        
        # 컬럼 이름 매핑 (원래 컬럼명 -> 보여줄 컬럼명)
        column_mapping = {
            "공고명": "공고명",
            "실수요기관": "실수요기관",
            "예상_입찰일": "입찰게시",
            "예측_입찰일": "(예측)입찰게시",
            "물동량 평균": "평균M/M",
            "용역기간(개월)": "용역기간(개월)",
            "계약 기간 내": "계약금액(원)",
            "입찰결과_1순위": "1순위 입찰업체",
            "입찰금액_1순위": "입찰금액(원)",
            "bid_id": "bid_id"  # bid_id 포함 (숨겨진 컬럼)
        }
        
        # 필요한 컬럼만 선택하고 이름 변경
        available_columns = [col for col in column_mapping.keys() if col in year_df.columns]
        table_df = year_df[available_columns].copy()
        table_df.columns = [column_mapping[col] for col in available_columns if col in column_mapping]
        
        # 입찰업체가 "예측"인 경우 빈 값으로 변경
        if "1순위 입찰업체" in table_df.columns:
            table_df["1순위 입찰업체"] = table_df["1순위 입찰업체"].apply(lambda x: "-" if x == "예측" else x)
        
        # 날짜 형식을 연-월-일로 변환
        date_columns = [col for col in ["입찰게시", "(예측)입찰게시"] if col in table_df.columns]
        for col in date_columns:
            table_df[col] = pd.to_datetime(table_df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 테이블 컬럼 설정
        columns = []
        for col_id in table_df.columns:
            if col_id == "bid_id":
                # bid_id는 컬럼에 포함하되 나중에 hidden_columns로 숨김
                columns.append({
                    "name": col_id, 
                    "id": col_id
                })
            elif col_id in ["입찰게시", "(예측)입찰게시"]:
                # 날짜 - 좌측 정렬 (기본)
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "text"
                })
            elif col_id in ["공고명", "실수요기관", "1순위 입찰업체"]:
                # 텍스트 - 가운데 정렬
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "text", 
                    "filter_options": {"case": "insensitive"}
                })
            elif col_id in ["계약금액(원)", "입찰금액(원)"]:
                # 금액 - 우측 정렬, 천 단위 쉼표
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "numeric", 
                    "format": {"specifier": ","}
                })
            elif col_id == "평균M/M":
                # 물동량 - 우측 정렬, 천 단위 쉼표, 편집 가능
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "numeric", 
                    "format": {"specifier": ","},
                    "editable": True  # 편집 가능 설정
                })
            elif col_id == "용역기간(개월)":
                # 용역기간 - 우측 정렬, 편집 가능
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "numeric", 
                    "format": {"specifier": ","},
                    "editable": True  # 편집 가능 설정
                })
            else:
                columns.append({
                    "name": col_id, 
                    "id": col_id, 
                    "type": "numeric"
                })

        table = dash_table.DataTable(
            id='full-data-table',
            columns=columns,
            data=table_df.to_dict('records'),
            style_table={
                'overflowX': 'auto',
                'maxHeight': '600px',
                'overflowY': 'auto'
            },
            hidden_columns=["bid_id"],
            # 기본 셀 스타일 설정
            style_cell={
                'padding': '8px',
                'minWidth': '100px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            # 데이터 유형별 정렬 설정
            style_cell_conditional=[
                # 텍스트 컬럼 - 가운데 정렬
                {
                    'if': {'column_id': col},
                    'textAlign': 'center'
                } for col in ["공고명", "실수요기관", "1순위 입찰업체"]
            ] + [
                # 숫자 컬럼 - 우측 정렬
                {
                    'if': {'column_id': col},
                    'textAlign': 'right'
                } for col in ["계약금액(원)", "입찰금액(원)", "용역기간(개월)", "평균M/M"]
            ] + [
                # 날짜 컬럼 - 좌측 정렬
                {
                    'if': {'column_id': col},
                    'textAlign': 'left'
                } for col in ["입찰게시", "(예측)입찰게시"]
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'border': '1px solid #ddd',
                'position': 'sticky',
                'top': 0,
                'zIndex': 10,
                'textAlign': 'center'  # 헤더는 모두 가운데 정렬
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px',
                'border': '1px solid #ddd'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                # 편집 가능한 셀 강조
                {
                    'if': {'column_editable': True},
                    'backgroundColor': 'rgba(255, 250, 230, 0.5)',
                    'border': '1px solid #ffeb3b'
                },
                # NULL 값 강조 (평균M/M)
                {
                    'if': {
                        'filter_query': '{평균M/M} = 0 || {평균M/M} is blank',
                        'column_id': '평균M/M'
                    },
                    'backgroundColor': '#ffdddd',
                    'color': 'red'
                },
                # NULL 값 강조 (용역기간(개월))
                {
                    'if': {
                        'filter_query': '{용역기간(개월)} = 0 || {용역기간(개월)} is blank',
                        'column_id': '용역기간(개월)'
                    },
                    'backgroundColor': '#ffdddd',
                    'color': 'red'
                }
            ],
            style_filter={
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #ddd',
                'padding': '4px'
            },
            filter_action="native",
            filter_options={"placeholder_text": "검색..."},
            sort_action="native",
            sort_mode="multi",
            sort_by=[{"column_id": "입찰게시", "direction": "asc"}],
            page_action='none',
            export_format="csv",
            export_headers="display",
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in table_df.to_dict('records')
            ],
            tooltip_duration=None,
            # 테이블 전체는 편집 불가, 특정 셀만 편집 가능
            editable=False,
            # Toggle Columns 버튼 숨기기 설정
            column_selectable=False
        )
        
        # 필터 버튼 추가
        filter_buttons = html.Div([
            html.Button("빈 값만 보기 (평균M/M)", id="filter-mm-btn", n_clicks=0, 
                        style={"marginRight": "10px", "backgroundColor": "#e7f2fc", "border": "1px solid #ccc", "padding": "5px 10px"}),
            html.Button("빈 값만 보기 (용역기간)", id="filter-duration-btn", n_clicks=0,
                        style={"marginRight": "10px", "backgroundColor": "#e7f2fc", "border": "1px solid #ccc", "padding": "5px 10px"}),
            html.Button("모두 보기", id="filter-all-btn", n_clicks=0,
                        style={"backgroundColor": "#e7f2fc", "border": "1px solid #ccc", "padding": "5px 10px"})
        ], style={"marginBottom": "15px"})
        
        # 공고 수 계산
        total_count = len(table_df)
        
        # 제목에 예측 표시 추가 (미래 데이터인 경우)
        title_text = f"{selected_year}년 공고 총 {total_count}건 (예측일은 게시일+용역기간 시점으로 산정)"
        
        # 설명 텍스트 추가 (편집 기능 안내)
        help_text = html.Div([
            html.P("물동량 평균과 용역기간 셀을 직접 클릭하여 값을 수정할 수 있습니다.", 
                   style={"color": "#0275d8", "fontStyle": "italic", "marginTop": "10px"})
        ])
        
        return html.Div([
            html.Div([
                html.P([
                    title_text,
                ], className="table-summary-text"),
                help_text
            ], className="table-summary-container"),
            filter_buttons,  # 필터 버튼 추가
            html.Div(table, className="table-container")
        ]), no_update
    
    @app.callback(
        Output("update-status-table", "children"),
        [Input("full-data-table", "data_timestamp")],
        [State("full-data-table", "data"),
         State("full-data-table", "data_previous")]
    )
    def update_database_from_table(timestamp, current_data, previous_data):
        if timestamp is None or current_data is None or previous_data is None:
            return no_update
        
        # 변경된 데이터 찾기
        changes = []
        for i, (current_row, previous_row) in enumerate(zip(current_data, previous_data)):
            if current_row != previous_row:
                # 변경 감지
                bid_id = current_row.get('bid_id')
                if not bid_id:
                    continue
                
                # 물동량 평균 변경 확인
                if current_row.get('평균M/M') != previous_row.get('평균M/M'):
                    try:
                        new_value = float(current_row.get('평균M/M', 0))
                        app.update_firebase_data(bid_id, "물동량 평균", new_value)
                        changes.append(f"물동량 평균 변경: {previous_row.get('평균M/M')} → {current_row.get('평균M/M')}")
                    except (ValueError, TypeError) as e:
                        changes.append(f"물동량 평균 변경 오류: {e}")
                
                # 용역기간 변경 확인
                if current_row.get('용역기간(개월)') != previous_row.get('용역기간(개월)'):
                    try:
                        new_value = float(current_row.get('용역기간(개월)', 0))
                        app.update_firebase_data(bid_id, "용역기간(개월)", new_value)
                        changes.append(f"용역기간 변경: {previous_row.get('용역기간(개월)')} → {current_row.get('용역기간(개월)')}")
                    except (ValueError, TypeError) as e:
                        changes.append(f"용역기간 변경 오류: {e}")
        
        if changes:
            return html.Div([
                html.P("변경 내용이 저장되었습니다:", style={"fontWeight": "bold", "marginBottom": "8px"}),
                html.Ul([html.Li(change) for change in changes], style={"marginLeft": "20px"})
            ], style={"color": "green", "backgroundColor": "#e8f5e9", "padding": "10px", "borderRadius": "5px", "marginTop": "10px"})
        
        return no_update
    
    @app.callback(
        Output("full-data-table", "filter_query"),
        [Input("filter-mm-btn", "n_clicks"),
         Input("filter-duration-btn", "n_clicks"),
         Input("filter-all-btn", "n_clicks")]
    )
    def filter_table(mm_clicks, duration_clicks, all_clicks):
        # 클릭된 버튼 확인
        ctx = callback_context
        if not ctx.triggered:
            # 초기 로드 시 필터 없음
            return ""
        
        # 어떤 버튼이 클릭되었는지 확인
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "filter-mm-btn":
            # 평균M/M이 0 또는 빈 값인 행만 표시
            return "{평균M/M} = 0 || {평균M/M} is blank"
        elif button_id == "filter-duration-btn":
            # 용역기간(개월)이 0 또는 빈 값인 행만 표시
            return "{용역기간(개월)} = 0 || {용역기간(개월)} is blank"
        elif button_id == "filter-all-btn":
            # 모든 행 표시 (필터 제거)
            return ""
        
        # 기본값: 필터 없음
        return ""
        
def register_edit_callbacks(app, df):
    @app.callback(
        [Output("edit-data-modal", "is_open"),
         Output("modal-bid-name", "children"),
         Output("mm-input", "value"),
         Output("duration-input", "value"),
         Output("bid-id-input", "value")],
        [Input("edit-bid-btn", "n_clicks")],
        [State("selected-bid", "data")]
    )
    def open_edit_modal(n_clicks, selected_bid):
        if not n_clicks or not selected_bid:
            return False, "", None, None, ""
        
        # 선택된 입찰 정보 찾기
        bid_info = df[df["공고명"] == selected_bid].iloc[0] if len(df[df["공고명"] == selected_bid]) > 0 else None
        
        if bid_info is None:
            return False, "", None, None, ""
        
        return True, bid_info["공고명"], bid_info["물동량 평균"], bid_info["용역기간(개월)"], bid_info["bid_id"]
    
    @app.callback(
        Output("edit-data-modal", "is_open", allow_duplicate=True),
        [Input("close-modal-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def close_modal(n_clicks):
        if n_clicks:
            return False
        return no_update
    
    @app.callback(
        [Output("update-status", "children"),
         Output("edit-data-modal", "is_open", allow_duplicate=True)],
        [Input("save-changes-btn", "n_clicks")],
        [State("bid-id-input", "value"),
         State("mm-input", "value"),
         State("duration-input", "value")],
        prevent_initial_call=True
    )
    def save_changes(n_clicks, bid_id, mm_value, duration_value):
        if not n_clicks or not bid_id:
            return no_update, no_update
        
        # 물동량 평균 업데이트
        mm_success, mm_message = app.update_firebase_data(bid_id, "물동량 평균", mm_value)
        
        # 용역기간 업데이트
        duration_success, duration_message = app.update_firebase_data(bid_id, "용역기간(개월)", duration_value)
        
        if mm_success and duration_success:
            # 성공 시 모달 닫기
            return html.Div("저장이 완료되었습니다.", style={"color": "green"}), False
        else:
            # 실패 시 모달 유지하고 에러 표시
            return html.Div(f"오류: {mm_message}, {duration_message}", style={"color": "red"}), True
