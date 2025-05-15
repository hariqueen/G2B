from dash import Input, Output, State, callback_context, html, dash_table, ALL, no_update, dcc
import plotly.express as px
import pandas as pd
from datetime import datetime

def register_callbacks(app, df):
    register_year_callbacks(app, df)
    register_info_callbacks(app, df)
    register_month_navigation_callbacks(app, df)
    register_bid_selection_callbacks(app, df)
    register_utility_callbacks(app, df)
    register_next_bid_navigation_callbacks(app, df)
    register_full_table_callbacks(app, df)

def register_year_callbacks(app, df):
    @app.callback(
        [Output("selected-year", "data"),
         Output("year-display", "children"),
         Output("current-month-view", "data")],
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
            return current_year, f"{current_year}년", default_page

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "prev-year-btn" and prev_clicks:
            new_year = current_year - 1
        elif button_id == "next-year-btn" and next_clicks:
            new_year = current_year + 1
        else:
            new_year = current_year

        # 현재 연도일 경우 현재월 포함 그룹, 아니면 첫 그룹(1~4월)
        month_view = default_page if new_year == today.year else 0

        return new_year, f"{new_year}년", month_view


def register_info_callbacks(app, df):
    @app.callback(
    Output("monthly-count-chart", "figure"),
    Input("selected-year", "data")
    )
    def update_monthly_chart(selected_year):
        # 원본 데이터의 최대 연도 확인
        max_original_year = df[~df["공고명"].str.contains("예측")]["예상_연도"].max() if not df[~df["공고명"].str.contains("예측")].empty else datetime.today().year
        
        # 선택한 연도가 원본 데이터 최대 연도보다 크면 예측 데이터만 표시
        if selected_year > max_original_year:
            year_df = df[(df["예상_연도"] == selected_year) & (df["공고명"].str.contains("예측"))]
        else:
            year_df = df[df["예상_연도"] == selected_year]
        
        # 해당 연도에 데이터가 없으면 빈 차트 반환
        if year_df.empty:
            # 모든 월 (1-12) 생성
            all_months = pd.DataFrame({"예상_입찰월": range(1, 13)})
            all_months["월"] = all_months["예상_입찰월"].astype(str) + "월"
            all_months["공고명"] = 0
            
            # 빈 차트 생성
            fig = px.bar(
                all_months,
                x="월",
                y="공고명",
                title=f"{selected_year}년 월별 공고 수",
                labels={"공고명": "공고 수", "월": ""},
                color_discrete_sequence=["#1f77b4"]
            )
            
            fig.update_layout(
                title_font_size=20,
                xaxis_title=None,
                yaxis_title="공고 수",
                plot_bgcolor="white",
                margin=dict(l=20, r=20, t=50, b=20),
                height=400,
                showlegend=False
            )
            
            return fig
        
        # 원본 데이터와 예측 데이터 구분하지 않고 통합
        monthly = year_df.groupby("예상_입찰월")["공고명"].count().reset_index()
        
        # 월 이름 추가
        monthly["월"] = monthly["예상_입찰월"].astype(str) + "월"
        
        # 모든 월 (1-12) 생성
        all_months = pd.DataFrame({"예상_입찰월": range(1, 13)})
        all_months["월"] = all_months["예상_입찰월"].astype(str) + "월"
        
        # 데이터 병합
        monthly = pd.merge(all_months, monthly, on=["예상_입찰월", "월"], how="left")
        monthly["공고명"] = monthly["공고명"].fillna(0)
        
        # 그래프 생성 - 단일 색상으로 통합
        fig = px.bar(
            monthly,
            x="월",
            y="공고명",
            title=f"{selected_year}년 월별 공고 수" + (" (예측)" if selected_year > max_original_year else ""),
            labels={"공고명": "공고 수", "월": ""},
            color_discrete_sequence=["#1f77b4"]
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title_font_size=20,
            xaxis_title=None,
            yaxis_title="공고 수",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            height=400,
            showlegend=False
        )
        
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
        
        # 원본 데이터의 최대 연도 확인
        max_original_year = df[~df["공고명"].str.contains("예측")]["예상_연도"].max() if not df[~df["공고명"].str.contains("예측")].empty else datetime.today().year
        
        # 선택한 연도가 원본 데이터 최대 연도보다 큰 경우 (예측 데이터)
        is_future_data = selected_year > max_original_year
        
        if is_future_data:
            # 미래 연도인 경우 해당 연도의 예측 데이터만 표시 (연도별)
            upcoming_df = df[(df["예상_연도"] == selected_year) & (df["공고명"].str.contains("예측"))].copy()
        else:
            # 현재/이전 연도인 경우 다음 달부터 데이터만 표시
            upcoming_df = df[df["예상_입찰일"] >= next_month_start].copy()
        
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
        if current_page == 0:  # 초기 페이지일 때만 자동으로 다음 달 선택
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
            # 사용자가 페이지를 변경한 경우 해당 페이지 사용
            current_month = 월순서[current_page] if 월순서 and current_page < len(월순서) else None
        
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
            공고_리스트 = 기관공고_df[["공고명", "예상_입찰일", "예상_년월", "용역기간(개월)", "원본_입찰일"]].sort_values("예상_입찰일")
            
            buttons = []
            for i, (_, row) in enumerate(공고_리스트.iterrows()):
                # NaT 값 안전하게 처리
                data_year = str(row["예상_입찰일"].year) if pd.notna(row["예상_입찰일"]) else ""
                data_month = row["예상_년월"] if pd.notna(row["예상_년월"]) else ""
                original_month = row["원본_입찰일"].strftime('%Y-%m') if pd.notna(row["원본_입찰일"]) else "-"
                
                button = html.Button(
                    f"{row['공고명']}",
                    id={"type": "bid-btn", "index": f"{name}_{i}"},
                    className="bid-button",
                    **{
                        "data-month": data_month,
                        "data-year": data_year,
                        "data-bid": str(row['공고명']),
                        "data-original-month": original_month
                    }
                )
                buttons.append(button)
            
            org_details = html.Details([
                html.Summary(name, className="org-name"),
                html.Div([
                    html.H4(f"🏢 {name} - 예정 공고", className="org-title"),
                    html.Div(buttons, className="bid-buttons-container")
                ], className="org-details-content")
            ], className="org-details")
            
            org_list.append(org_details)
        
        # 월 표시 (예측 정보 추가)
        month_display = f"다음 입찰 예상월: {target_월} (총 {total_count}건)" + (" (예측)" if is_future_data else "")
        
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

        year_df = df[df["예상_연도"] == selected_year]
        view_months = year_df[year_df["예상_입찰월"].isin(view_month_nums)]["예상_년월"].unique()
        view_months = sorted(view_months)

        max_pages = len(month_groups) - 1
        
        # 중요: 이전/다음 버튼을 항상 활성화 (다른 연도로 이동 가능)
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
                # 원본 데이터와 예측 데이터 구분하여 정렬
                sorted_data = month_data.sort_values(by=["공고명"])
                
                for _, row in sorted_data.iterrows():
                    highlight = (row["공고명"] == selected_bid)
                    
                    # 예측 공고인지 확인 (스타일 차이는 유지하되, 더 미묘하게 표시)
                    is_prediction = "예측" in str(row["공고명"])
                    emoji = "📌" if not is_prediction else ("📍" if highlight else "📌")
                    
                    # 예측 공고에 대한 스타일 수정 (파란색 강조 제거)
                    summary_class = "bid-summary"
                    if highlight:
                        summary_class += " highlighted"
                    
                    # 예측 입찰일 계산 - "예측_입찰일" 컬럼이 있으면 그 값을 사용, 없으면 계산
                    if "예측_입찰일" in row and pd.notna(row["예측_입찰일"]):
                        predicted_date = row["예측_입찰일"].strftime('%Y-%m') if not pd.isna(row["예측_입찰일"]) else "-"
                    else:
                        # 용역기간 기반 예측 계산
                        if pd.notna(row["예상_입찰일"]) and pd.notna(row["용역기간(개월)"]) and row["용역기간(개월)"] > 0:
                            predicted_date = row["예상_입찰일"] + pd.DateOffset(months=int(row["용역기간(개월)"]))
                            predicted_date = predicted_date.strftime('%Y-%m') if not pd.isna(predicted_date) else "-"
                        else:
                            predicted_date = "-"
                    
                    bid_details = html.Details([
                        html.Summary(f"{emoji} {row['공고명']}", className=summary_class),
                        html.Div([
                            html.P(f"실수요기관: {row['실수요기관'] if pd.notna(row['실수요기관']) else '-'}", className="bid-detail"),
                            html.P(f"입찰게시: {row['예상_입찰일'].strftime('%Y-%m') if pd.notna(row['예상_입찰일']) else '-'}", className="bid-detail"),
                            html.P(f"(예측)입찰게시: {predicted_date}", className="bid-detail"),
                            html.P(f"M/M: {row['물동량 평균'] if pd.notna(row['물동량 평균']) else '-'}", className="bid-detail"),
                            html.P(f"용역기간: {row['용역기간(개월)'] if pd.notna(row['용역기간(개월)']) else '-'}{'개월' if pd.notna(row['용역기간(개월)']) else ''}", className="bid-detail"),
                            html.P(f"계약금액: {row['계약 기간 내'] if pd.notna(row['계약 기간 내']) else '-'}{'원' if pd.notna(row['계약 기간 내']) else ''}", className="bid-detail"),
                            html.P(f"1순위 입찰업체: {'-' if row['입찰결과_1순위'] == '예측' else (row['입찰결과_1순위'] if pd.notna(row['입찰결과_1순위']) else '-')}", className="bid-detail"),
                            html.P(f"입찰금액: {row['입찰금액_1순위'] if pd.notna(row['입찰금액_1순위']) and row['입찰금액_1순위'] != 0 else '-'}{'원' if pd.notna(row['입찰금액_1순위']) and row['입찰금액_1순위'] != 0 else ''}", className="bid-detail"),
                        ])
                    ])
                    month_bids.append(bid_details)

                section = html.Div([
                    html.Div(id=anchor_id, className="anchor-point"),
                    html.H3(f"{emphasis}{m}", className="month-title"),
                    html.Div(month_bids, className="month-bids-list")
                ], className="month-section", style=section_style)
                month_cells.append(html.Div(section, className="month-cell"))

        return month_cells, range_display, prev_button_disabled, next_button_disabled
    
def register_bid_selection_callbacks(app, df):
    @app.callback(
        [Output("selected-month", "data", allow_duplicate=True),
         Output("selected-bid", "data"),
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

    # 자동 펼침 기능을 위한 새로운 콜백 추가 (하나만 열리도록 수정)
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
    Output("full-table-container", "children"),
    Input("selected-year", "data")
)
    def update_full_table(selected_year):
    # 원본 데이터의 최대 연도 확인
        max_original_year = df[~df["공고명"].str.contains("예측")]["예상_연도"].max() if not df[~df["공고명"].str.contains("예측")].empty else datetime.today().year
        print(f"원본 데이터 최대 연도: {max_original_year}, 선택 연도: {selected_year}")
        
        # 선택한 연도가 원본 데이터 최대 연도보다 크면 예측 데이터만 표시
        if selected_year > max_original_year:
            year_df = df[(df["예상_연도"] == selected_year) & (df["공고명"].str.contains("예측"))].copy()
        else:
            year_df = df[df["예상_연도"] == selected_year].copy()
        
        if year_df.empty:
            return html.Div("선택한 연도에 해당하는 공고가 없습니다.", className="no-data-message")
        
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
                year_df.at[idx, "예측_입찰일"] = row["예상_입찰일"]  # 현재 예상_입찰일은 예측된 날짜
                
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
            "입찰금액_1순위": "입찰금액(원)"
        }
        
        # 필요한 컬럼만 선택하고 이름 변경
        available_columns = [col for col in column_mapping.keys() if col in year_df.columns]
        table_df = year_df[available_columns].copy()
        table_df.columns = [column_mapping[col] for col in available_columns if col in column_mapping]
        
        # 입찰업체가 "예측"인 경우 빈 값으로 변경
        if "1순위 입찰업체" in table_df.columns:
            table_df["1순위 입찰업체"] = table_df["1순위 입찰업체"].apply(lambda x: "-" if x == "예측" else x)
        
        # 날짜 형식 변환
        date_columns = [col for col in ["입찰게시", "(예측)입찰게시"] if col in table_df.columns]
        for col in date_columns:
            table_df[col] = pd.to_datetime(table_df[col], errors='coerce').dt.strftime('%Y-%m')
        
        # 테이블 컬럼 설정
        columns = []
        for col_id in table_df.columns:
            if col_id in ["입찰게시", "(예측)입찰게시"]:
                columns.append({"name": col_id, "id": col_id, "type": "text"})
            elif col_id in ["공고명", "실수요기관", "1순위 입찰업체"]:
                columns.append({"name": col_id, "id": col_id, "type": "text", "filter_options": {"case": "insensitive"}})
            elif col_id in ["계약금액(원)", "입찰금액(원)"]:
                columns.append({"name": col_id, "id": col_id, "type": "numeric", "format": {"specifier": ","}})
            else:
                columns.append({"name": col_id, "id": col_id, "type": "numeric"})

        table = dash_table.DataTable(
            id='full-data-table',
            columns=columns,
            data=table_df.to_dict('records'),
            style_table={
                'overflowX': 'auto',
                'maxHeight': '600px',
                'overflowY': 'auto'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'minWidth': '100px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'border': '1px solid #ddd',
                'position': 'sticky',
                'top': 0,
                'zIndex': 10
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
            tooltip_duration=None
        )
        
        # 공고 수 계산
        total_count = len(table_df)
        
        # 제목에 예측 표시 추가 (미래 데이터인 경우)
        title_text = f"{selected_year}년 공고 총 {total_count}건" + (" (예측)" if is_future_data else "")
        
        return html.Div([
            html.Div([
                html.P([
                    title_text,
                ], className="table-summary-text"),
            ], className="table-summary-container"),
            html.Div(table, className="table-container")
        ])