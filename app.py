import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import dateutil.parser

# 앱 설정
st.set_page_config(page_title="실시간 월드컵 분석기", layout="wide")
st.title("⏱️ 실시간 매치 업데이트 및 마감 시간 에이전트")

# ==========================================
# [데이터 피드] API를 통한 실시간 매치 정보 및 배당 수집
# ==========================================
# API_KEY 발급처: https://the-odds-api.com/ (무료 신청 시 바로 발급)
API_KEY = "YOUR_REAL_API_KEY" 

@st.cache_data(ttl=60) # 60초 동안 데이터를 캐싱하여 API 호출 낭비 방지 (트레이딩 수수료 절감 원리)
def fetch_live_worldcup_odds():
    """
    The Odds API에서 곧 열릴 월드컵 경기 일정과 배당률을 실시간 수집하는 함수
    """
    # 실제 API 호출부 (API Key가 없을 경우를 대비해 하단에 데모 데이터용 백업 로직 포함)
    url = f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # [Demo Backup] API 미연동 시 작동할 2026 북중미 월드컵 시뮬레이션 데이터
    # 실제 API도 정확히 아래와 같은 JSON 구조로 리턴됩니다.
    return [
        {
            "id": "match_01",
            "commence_time": "2026-06-12T03:00:00Z", # UTC 기준 경기 시작 시간
            "home_team": "Mexico", "away_team": "South Korea",
            "bookmakers": [{"markets": [{"outcomes": [{"name": "Mexico", "price": 1.95}, {"name": "Draw", "price": 3.40}, {"name": "South Korea", "price": 4.10}]}]}]
        },
        {
            "id": "match_02",
            "commence_time": "2026-06-12T18:30:00Z",
            "home_team": "United States", "away_team": "Australia",
            "bookmakers": [{"markets": [{"outcomes": [{"name": "United States", "price": 1.65}, {"name": "Draw", "price": 3.75}, {"name": "Australia", "price": 5.50}]}]}]
        }
    ]

# 데이터 긁어오기
raw_matches = fetch_live_worldcup_odds()

# ==========================================
# [엔진] 현재 시간과 경기 시작 시간 비교 분석 로직
# ==========================================
processed_games = []
now_utc = datetime.now(timezone.utc) # 현재 컴퓨터 시간을 UTC로 통일

for game in raw_matches:
    # 경기 시작 시간 파싱 (commence_time: "2026-06-12T03:00:00Z")
    match_time_utc = dateutil.parser.isoparse(game['commence_time'])
    
    # 마감까지 남은 시간 계산 (경기 시작 = 배팅 마감)
    time_delta = match_time_utc - now_utc
    remaining_seconds = time_delta.total_seconds()
    
    # 🛑 리스크 관리: 이미 시작했거나 종료된 경기는 진입 대상에서 자동 제외 (Filter)
    if remaining_seconds <= 0:
        continue
        
    # 남은 시간을 보기 좋게 스트링으로 변환 (ex: 5시간 30분 남음)
    hours, remainder = divmod(int(remaining_seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    time_status = f"⏳ {hours}시간 {minutes}분 남음"
    
    # 배당률 데이터 추출
    try:
        outcomes = game['bookmakers'][0]['markets'][0]['outcomes']
        odds = {o['name']: o['price'] for o in outcomes}
    except:
        odds = {"Home": 2.0, "Draw": 3.0, "Away": 4.0} # 예외처리용 기본값
        
    processed_games.append({
        "ID": game['id'],
        "경기 시간 (국내 기준)": match_time_utc.astimezone().strftime('%Y-%m-%d %H:%M'),
        "마감 현황": time_status,
        "홈 팀": game['home_team'],
        "원정 팀": game['away_team'],
        "홈승 배당": odds.get(game['home_team'], 2.0),
        "무승부 배당": odds.get("Draw", 3.0),
        "원정승 배당": odds.get(game['away_team'], 4.0),
        "remaining_sec": remaining_seconds # 정렬용
    })

# 마감 시간이 가장 임박한 순서(단기 듀레이션)로 테이블 정렬
df_apps = pd.DataFrame(processed_games).sort_values(by="remaining_sec")

# ==========================================
# [UI] 스트림릿 대시보드 화면 렌더링
# ==========================================
st.subheader("📊 실시간 배팅 풀(Pool) - 마감 임박 순 정렬")
st.write("새로고침 버튼을 누르거나 페이지를 열 때마다 실시간 잔여 시간이 동적으로 계산됩니다.")

if not df_apps.empty:
    # 사용자가 보기 편하게 특정 칼럼만 UI 테이블로 노출
    st.dataframe(
        df_apps[["마감 현황", "경기 시간 (국내 기준)", "홈 팀", "원정 팀", "홈승 배당", "무승부 배당", "원정승 배당"]],
        use_container_width=True,
        hide_index=True
    )
    
    # 경기 선택 박스 생성 (배팅 시뮬레이터 연동)
    st.divider()
    st.subheader("💵 선택 매치 켈리 공식 자금 배분 시뮬레이터")
    
    selected_match_str = st.selectbox(
        "분석할 경기를 선택하세요", 
        df_apps.apply(lambda r: f"{r['홈 팀']} vs {r['원정 팀']} ({r['마감 현황']})", axis=1)
    )
    
    # 선택된 경기 데이터 로우 추출
    selected_idx = df_apps.apply(lambda r: f"{r['홈 팀']} vs {r['원정 팀']} ({r['마감 현황']})", axis=1) == selected_match_str
    match_info = df_apps[selected_idx].iloc[0]
    
    # 켈리 공식 UI 연결
    user_prob = st.slider(f"AI 모델이 계산한 [{match_info['홈 팀']}]의 승리 확률 (%)", 0, 100, 50) / 100.0
    capital = st.number_input("나의 총 배팅 자산 (원)", value=1000000)
    
    # 계산
    b = match_info['홈승 배당'] - 1
    p = user_prob
    q = 1 - p
    kelly_f = (p * b - q) / b
    half_kelly_f = kelly_f / 2
    
    if half_kelly_f > 0:
        st.success(f"🎯 **[Trading Signal]** {match_info['홈 팀']} 승리에 총 자산의 **{half_kelly_f*100:.1f}%** 인 **{(int(capital * half_kelly_f)):,}원** 진입 추천!")
    else:
        st.error("🛑 **[Signal]** 해당 배당률 조건에서는 기대수익률이 낮아 패스(Pass)를 권장합니다.")
else:
    st.info("현재 분석 가능한 미래 경기가 없습니다.")
