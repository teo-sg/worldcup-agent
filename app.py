import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
import dateutil.parser
from xgboost import XGBClassifier

# 앱 기본 설정
st.set_page_config(page_title="2026 월드컵 AI 하이브리드 에이전트", layout="wide")

# ==========================================
# [1단계] AI 모델 및 기초 데이터베이스 정의
# ==========================================
@st.cache_resource
def init_ai_model():
    np.random.seed(42)
    num_matches = 300
    data = {
        'rank_diff': np.random.randint(-40, 40, num_matches),
        'elo_diff': np.random.randint(-300, 300, num_matches),
        'xg_diff': np.random.uniform(-1.5, 1.5, num_matches),
        'odds_home_win': np.random.uniform(1.2, 6.0, num_matches),
        'odds_draw': np.random.uniform(2.5, 4.5, num_matches),
        'odds_away_win': np.random.uniform(1.2, 6.0, num_matches)
    }
    X = pd.DataFrame(data)
    y = np.random.choice([0, 1, 2], size=num_matches, p=[0.45, 0.25, 0.30])
    model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1, objective='multi:softprob', random_state=42)
    model.fit(X, y)
    return model

ai_agent = init_ai_model()

TEAM_DATABASE = {
    "Mexico": {"fifa_rank": 15, "elo": 1850, "recent_xg": 1.90},
    "South Korea": {"fifa_rank": 22, "elo": 1780, "recent_xg": 1.65},
    "United States": {"fifa_rank": 11, "elo": 1910, "recent_xg": 2.10},
    "Australia": {"fifa_rank": 24, "elo": 1750, "recent_xg": 1.45}
}

def get_team_stats(team_name):
    return TEAM_DATABASE.get(team_name, {"fifa_rank": 30, "elo": 1700, "recent_xg": 1.50})

# ==========================================
# [2단계] 해외 API + 국내 프로토 배당 시뮬레이션 파서
# ==========================================
@st.cache_data(ttl=60)
def fetch_hybrid_market_odds():
    """
    해외 배당 데이터에 국내 스포츠토토(배트맨) 프로토 배당을 매칭한 하이브리드 피드
    """
    return [
        {
            "id": "match_2026_01",
            "commence_time": "2026-06-12T03:00:00Z", 
            "home_team": "Mexico", "away_team": "South Korea",
            "foreign_odds": {"Home": 1.95, "Draw": 3.40, "Away": 4.10},
            "korean_proto_odds": {"Home": 1.78, "Draw": 3.10, "Away": 3.95} # 국내 프로토는 수수료 때문에 보통 더 낮음
        },
        {
            "id": "match_2026_02",
            "commence_time": "2026-06-14T18:30:00Z",
            "home_team": "United States", "away_team": "Australia",
            "foreign_odds": {"Home": 1.65, "Draw": 3.75, "Away": 5.50},
            "korean_proto_odds": {"Home": 1.55, "Draw": 3.50, "Away": 4.80}
        }
    ]

# 데이터 파이프라인 가동
raw_matches = fetch_hybrid_market_odds()
now_utc = datetime.now(timezone.utc)
processed_games = []

for game in raw_matches:
    match_time_utc = dateutil.parser.isoparse(game['commence_time'])
    remaining_seconds = (match_time_utc - now_utc).total_seconds()
    
    if remaining_seconds <= 0:
        continue
        
    hours, remainder = divmod(int(remaining_seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    
    h_stats = get_team_stats(game['home_team'])
    a_stats = get_team_stats(game['away_team'])
    
    processed_games.append({
        "ID": game['id'],
        "마감 현황": f"⏳ {hours}시간 {minutes}분 남음",
        "경기 시간": match_time_utc.astimezone().strftime('%Y-%m-%d %H:%M'),
        "홈 팀": game['home_team'], "원정 팀": game['away_team'],
        "해외_홈": game['foreign_odds']['Home'], "해외_무": game['foreign_odds']['Draw'], "해외_원정": game['foreign_odds']['Away'],
        "국내_홈": game['korean_proto_odds']['Home'], "국내_무": game['korean_proto_odds']['Draw'], "국내_원정": game['korean_proto_odds']['Away'],
        "rank_diff": h_stats['fifa_rank'] - a_stats['fifa_rank'],
        "elo_diff": h_stats['elo'] - a_stats['elo'],
        "xg_diff": h_stats['recent_xg'] - a_stats['recent_xg']
    })

df_apps = pd.DataFrame(processed_games)

# ==========================================
# [3단계] 메인 UI 대시보드 렌더링
# ==========================================
st.title("⚖️ 해외 vs 국내 프로토 배당 비교 차익거래 에이전트")
st.markdown("해외 글로벌 배당과 국내 스포츠토토(배트맨) 배당의 프리미엄 왜곡 현상을 추적합니다.")
st.divider()

# 자금 설정
st.header("💰 1. 자산 포트폴리오 크기 설정")
capital = st.number_input("현재 사용 가능한 총 배팅 예산 (원)", value=1000000, step=100000, format="%d")
st.divider()

# 경기 테이블 노출
st.header("📋 2. 실시간 해외/국내 프로토 통합 매치 풀")
if not df_apps.empty:
    # 한 화면에 해외와 국내 배당을 명확하게 쪼개서 테이블화
    display_df = df_apps[["마감 현황", "홈 팀", "원정 팀", "해외_홈", "국내_홈", "해외_무", "국내_무", "해외_원정", "국내_원정"]]
    display_df.columns = ["마감 현황", "홈 팀", "원정 팀", "🌐 해외 홈승", "🇰🇷 프로토 홈승", "🌐 해외 무승부", "🇰🇷 프로토 무승부", "🌐 해외 원정승", "🇰🇷 프로토 원정승"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.divider()
    
    # 경기 선택
    st.header("🎯 3. 프리미엄 비교 및 AI 베팅 포지션 전략")
    selected_match_str = st.selectbox(
        "분석할 월드컵 경기를 선택하세요:", 
        df_apps.apply(lambda r: f"⚽ {r['홈 팀']} vs {r['원정 팀']} ({r['마감 현황']})", axis=1)
    )
    
    selected_idx = df_apps.apply(lambda r: f"⚽ {r['홈 팀']} vs {r['원정 팀']} ({r['마감 현황']})", axis=1) == selected_match_str
    m_info = df_apps[selected_idx].iloc[0]
    
    # AI 승리 확률 계산
    input_data = pd.DataFrame([{
        'rank_diff': m_info['rank_diff'], 'elo_diff': m_info['elo_diff'], 'xg_diff': m_info['xg_diff'],
        'odds_home_win': m_info['해외_홈'], 'odds_draw': m_info['해외_무'], 'odds_away_win': m_info['해외_원정']
    }])
    pred_probas = ai_agent.predict_proba(input_data)[0]
    ai_home_prob = pred_probas[0] # 홈팀 승리 확률
    
    # 프리미엄 왜곡 수치 계산 (해외 배당 대비 국내 프로토 배당의 효율성)
    # 수식: (국내 배당 / 해외 배당) - 1
    premium_home = (m_info['국내_홈'] / m_info['해외_홈'] - 1) * 100
    
    # 대시보드 리포트 시각화
    st.write(f"#### 📊 **[{m_info['홈 팀']} vs {m_info['원정 팀']}] 퀀트 비교 리포트**")
    
    ui_col1, ui_col2, ui_col3 = st.columns(3)
    ui_col1.metric("🔮 AI가 계산한 홈팀 진짜 승률", f"{ai_home_prob*100:.1f}%")
    ui_col2.metric("🇰🇷 프로토 홈팀 배당률", f"{m_info['국내_홈']} 배")
    ui_col3.metric("📉 국내-해외 프리미엄 왜곡도", f"{premium_home:.1f}%", help="이 지표가 플러스(+)에 가까울수록 국내 배당이 해외보다 유리하게 잡힌 역전 구간입니다.")
    
    # 켈리 공식 자금 배분 (국내 배트맨 프로토 배당 기준으로 내 자금 계산)
    b_korea = m_info['국내_홈'] - 1
    kelly_f_korea = (ai_home_prob * b_korea - (1 - ai_home_prob)) / b_korea
    half_kelly_f_korea = kelly_f_korea / 2
    
    st.markdown("---")
    st.write("### 💵 국내 배트맨 프로토 실전 베팅 지침")
    
    if half_kelly_f_korea > 0:
        proto_bet_money = int(capital * half_kelly_f_korea)
        st.success(f"🟢 **[Trading Signal] 합법 프로토 진입 타당성 확인**")
        st.markdown(f"* **추천 포지션:** 국내 프로토 창구에서 **[{m_info['홈 팀']} 승리]** 마킹")
        st.markdown(f"* **포트폴리오 비중:** 내 배팅 자산의 **{half_kelly_f_korea*100:.1f}%**")
        st.markdown(f"* **최적 진입 금액:** **{proto_bet_money:,}원**")
    else:
        st.error(f"🔴 **[Signal] 국내 프로토 진입 금지 (Pass)**")
        st.markdown(f"국내 배트맨 프로토의 낮은 환급률과 배당 깎임 현상으로 인해, AI 예측 확률 기준 **기대 수익률이 마이너스**입니다. 이 경기는 구매하지 마십시오.")

else:
    st.info("현재 분석 가능한 미래 경기가 존재하지 않습니다.")
