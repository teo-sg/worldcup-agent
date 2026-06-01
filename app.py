import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
import dateutil.parser
from xgboost import XGBClassifier

# 앱 기본 설정
st.set_page_config(page_title="2026 월드컵 AI 에이전트", layout="wide")
st.title("🤖 2026 북중미 월드컵 완전 자동화 AI 트레이딩 에이전트")
st.markdown("XGBoost 머신러닝 모델이 실시간 전력 분석을 기반으로 승리 확률을 도출하고 켈리 공식을 적용합니다.")

# ==========================================
# 1. 가상 가동용 데이터 및 XGBoost 사전 모델 학습
# ==========================================
@st.cache_resource
def init_ai_model():
    """
    축구 전력 데이터와 배당률을 함께 학습하는 하이브리드 XGBoost 모델 초기화
    """
    np.random.seed(42)
    num_matches = 300
    
    # 훈련용 펀더멘탈 + 수급 데이터 생성
    data = {
        'rank_diff': np.random.randint(-40, 40, num_matches),
        'elo_diff': np.random.randint(-300, 300, num_matches),
        'xg_diff': np.random.uniform(-1.5, 1.5, num_matches),
        'odds_home_win': np.random.uniform(1.2, 6.0, num_matches),
        'odds_draw': np.random.uniform(2.5, 4.5, num_matches),
        'odds_away_win': np.random.uniform(1.2, 6.0, num_matches)
    }
    X = pd.DataFrame(data)
    # 정답셋 (0=홈승, 1=무승부, 2=원정승)
    y = np.random.choice([0, 1, 2], size=num_matches, p=[0.45, 0.25, 0.30])
    
    model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1, objective='multi:softprob', random_state=42)
    model.fit(X, y)
    return model

ai_agent = init_ai_model()

# 各 팀별 가상 데이터 피드 (실제 API나 DB에서 연동되는 펀더멘탈 지표)
TEAM_DATABASE = {
    "Mexico": {"fifa_rank": 15, "elo": 1850, "recent_xg": 1.90},
    "South Korea": {"fifa_rank": 22, "elo": 1780, "recent_xg": 1.65},
    "United States": {"fifa_rank": 11, "elo": 1910, "recent_xg": 2.10},
    "Australia": {"fifa_rank": 24, "elo": 1750, "recent_xg": 1.45}
}

def get_team_stats(team_name):
    return TEAM_DATABASE.get(team_name, {"fifa_rank": 30, "elo": 1700, "recent_xg": 1.50})

# ==========================================
# 2. 실시간 배당률 및 매치 수집 파서
# ==========================================
@st.cache_data(ttl=60)
def fetch_live_matches():
    # 데모 가동용 실시간 데이터 구조 (The Odds API 포맷 반영)
    return [
        {
            "id": "match_2026_01",
            "commence_time": "2026-06-12T03:00:00Z", 
            "home_team": "Mexico", "away_team": "South Korea",
            "bookmakers": [{"markets": [{"outcomes": [{"name": "Mexico", "price": 1.95}, {"name": "Draw", "price": 3.40}, {"name": "South Korea", "price": 4.10}]}]}]
        },
        {
            "id": "match_2026_02",
            "commence_time": "2026-06-14T18:30:00Z",
            "home_team": "United States", "away_team": "Australia",
            "bookmakers": [{"markets": [{"outcomes": [{"name": "United States", "price": 1.65}, {"name": "Draw", "price": 3.75}, {"name": "Australia", "price": 5.50}]}]}]
        }
    ]

# ==========================================
# 3. 데이터 파이프라인 프로세싱
# ==========================================
raw_matches = fetch_live_matches()
now_utc = datetime.now(timezone.utc)
processed_games = []

for game in raw_matches:
    match_time_utc = dateutil.parser.isoparse(game['commence_time'])
    remaining_seconds = (match_time_utc - now_utc).total_seconds()
    
    if remaining_seconds <= 0:
        continue # 마감 경기는 패스
        
    hours, remainder = divmod(int(remaining_seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    
    # 배당 데이터 파싱
    outcomes = game['bookmakers'][0]['markets'][0]['outcomes']
    odds = {o['name']: o['price'] for o in outcomes}
    
    h_stats = get_team_stats(game['home_team'])
    a_stats = get_team_stats(game['away_team'])
    
    processed_games.append({
        "ID": game['id'],
        "마감 현황": f"⏳ {hours}시간 {minutes}분 남음",
        "홈 팀": game['home_team'], "원정 팀": game['away_team'],
        "홈승 배당": odds.get(game['home_team']),
        "무승부 배당": odds.get("Draw"),
        "원정승 배당": odds.get(game['away_team']),
        # 모델 예측용 피처 생성
        "rank_diff": h_stats['fifa_rank'] - a_stats['fifa_rank'],
        "elo_diff": h_stats['elo'] - a_stats['elo'],
        "xg_diff": h_stats['recent_xg'] - a_stats['recent_xg']
    })

df_apps = pd.DataFrame(processed_games)

# ==========================================
# 4. 자산 관리 및 UI 구현
# ==========================================
st.sidebar.header("💰 트레이딩 머니 설정")
capital = st.sidebar.number_input("투자 원금 (원)", value=1000000, step=100000)

if not df_apps.empty:
    st.subheader("📊 실시간 분석 및 신호 탐지 현황")
    
    # 각 경기별로 AI 연산 진행
    for idx, row in df_apps.iterrows():
        st.write(f"### ⚔️ {row['홈 팀']} vs {row['원정 팀']} ({row['마감 현황']})")
        
        # XGBoost 입력용 피처 정렬
        input_data = pd.DataFrame([{
            'rank_diff': row['rank_diff'], 'elo_diff': row['elo_diff'], 'xg_diff': row['xg_diff'],
            'odds_home_win': row['홈승 배당'], 'odds_draw': row['무승부 배당'], 'odds_away_win': row['원정승 배당']
        }])
        
        # AI 확률 계산 (자동 분석 실행!)
        pred_probas = ai_agent.predict_proba(input_data)[0]
        home_win_prob = pred_probas[0] # 홈팀 승리 확률 추출
        
        # 켈리 공식 연산 (홈팀 기준)
        b = row['홈승 배당'] - 1
        kelly_f = (home_win_prob * b - (1 - home_win_prob)) / b
        half_kelly_f = kelly_f / 2  # 보수적 퀀트 전략
        
        # 대시보드 시각화
        c1, c2, c3 = st.columns(3)
        c1.metric("🔮 AI 분석 승리 확률", f"{home_win_prob*100:.1f}%")
        c2.metric("📈 시장 배당률", f"{row['홈승 배당']} 배")
        
        # 트레이딩 시그널 확정
        if half_kelly_f > 0:
            bet_amount = int(capital * half_kelly_f)
            c3.markdown(f"🟢 **[Signal] 진입 추천**\n\n자산 비중: **{half_kelly_f*100:.1f}%**\n\n추천 금액: **{bet_amount:,}원**")
        else:
            c3.markdown("🔴 **[Signal] 패스 (Pass)**\n\n기대 수익률 부족으로 리스크 제외")
        st.divider()
else:
    st.info("현재 분석 가능한 미래 경기가 존재하지 않습니다.")
