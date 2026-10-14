import streamlit as st
import pandas as pd

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="제조 품질 현황 대시보드", layout="wide")

st.title("제조 품질 현황 대시보드")
st.subheader("AI 비전검사 PoC 준비를 위한 품질 데이터 모니터링")

# --- 1. 샘플 데이터 생성 함수 ---
# CSV 파일이 없을 때 기본으로 띄워줄 데이터랑께요.
@st.cache_data
def load_sample_data():
    data = {
        'inspection_date': ['2026-10-01', '2026-10-01', '2026-10-02', '2026-10-02', '2026-10-03', '2026-10-03', '2026-10-04'],
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007'],
        'result': ['OK', 'NG', 'OK', 'NG', 'OK', 'OK', 'NG'],
        'defect_type': ['None', 'Scratch', 'None', 'Crack', 'None', 'None', 'Dent'],
        'confidence': [0.98, 0.91, 0.96, 0.88, 0.99, 0.95, 0.85]
    }
    df = pd.DataFrame(data)
    df['inspection_date'] = pd.to_datetime(df['inspection_date'])
    return df

# --- 2. 사이드바 (업로드 및 필터) ---
st.sidebar.header("설정 및 필터")
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=['csv'])

# 파일 업로드 여부에 따라 데이터 불러오기
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['inspection_date'] = pd.to_datetime(df['inspection_date'])
else:
    df = load_sample_data()
    st.sidebar.info("업로드된 파일이 없어서 기본 샘플 데이터를 보여주구마잉.")

st.sidebar.markdown("---")
st.sidebar.subheader("데이터 필터")

# 필터 요소들
min_date = df['inspection_date'].min().date()
max_date = df['inspection_date'].max().date()
# 날짜 선택 (기본값은 전체 기간)
date_range = st.sidebar.date_input("날짜 범위", [min_date, max_date])

# OK/NG 결과 필터
result_options = df['result'].unique()
selected_results = st.sidebar.multiselect("검사 결과", options=result_options, default=result_options)

# 데이터 필터링 적용
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['inspection_date'].dt.date >= start_date) & \
           (df['inspection_date'].dt.date <= end_date) & \
           (df['result'].isin(selected_results))
    filtered_df = df[mask]
else:
    filtered_df = df # 날짜 선택이 덜 끝났을 땐 원본 유지

# --- 3. KPI 지표 (상단) ---
if not filtered_df.empty:
    total_count = len(filtered_df)
    ok_count = len(filtered_df[filtered_df['result'] == 'OK'])
    ng_count = len(filtered_df[filtered_df['result'] == 'NG'])
    ng_rate = (ng_count / total_count * 100) if total_count > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 검사 건수", f"{total_count} 건")
    col2.metric("정상 수량", f"{ok_count} 건")
    col3.metric("불량 수량", f"{ng_count} 건")
    col4.metric("불량률", f"{ng_rate:.1f} %")
else:
    st.warning("선택한 조건에 맞는 데이터가 없당께요. 필터를 다시 확인해보쇼잉.")

st.markdown("---")

# --- 4. 그래프 (중단) ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("날짜별 검사 현황")
    if not filtered_df.empty:
        # 날짜별 데이터 갯수 세기
        daily_counts = filtered_df.groupby(filtered_df['inspection_date'].dt.date).size()
        st.line_chart(daily_counts)

with col_chart2:
    st.subheader("불량 유형별 건수")
    # 불량인 것만 추려내기
    ng_df = filtered_df[filtered_df['result'] == 'NG']
    if not ng_df.empty:
        defect_counts = ng_df['defect_type'].value_counts()
        st.bar_chart(defect_counts)
    else:
        st.info("선택한 기간에는 불량 데이터가 없구마잉! (다행이여)")

st.markdown("---")

# --- 5. 데이터 표 (하단) ---
st.subheader("최근 검사 결과 (최대 10건)")
if not filtered_df.empty:
    # 최신 날짜순으로 정렬해서 10개만 딱 보여주기
    recent_df = filtered_df.sort_values(by='inspection_date', ascending=False).head(10)
    st.dataframe(recent_df, use_container_width=True)