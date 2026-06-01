import streamlit as st
import pandas as pd
import numpy as np
import requests
from xgboost import XGBClassifier

# ==========================================
# ⚙️ [필수 세팅] 내 실시간 해외 API Key 입력
# ==========================================
ODDS_API_KEY = "5edde4fede86b8f7fb79f2d844106505" 

st.set_page_config(page_title="부자되자 퀀트 마스터 v11.5", layout="wide")

# ==========================================
# [엔진 1] 4대 변수 동적 가중형 머신러닝 엔진
# ==========================================
@st.cache_resource
def init_advanced_model():
    np.random.seed(42)
    num_samples = 600
    data = {
        'weight_stat': np.random.uniform(-1.5, 1.5, num_samples),      
        'weight_friendly': np.random.uniform(-0.3, 0.3, num_samples),  
        'weight_injury': np.random.uniform(-0.2, 0.2, num_samples),    
        'weight_value_odds': np.random.uniform(1.2, 4.5, num_samples)  
    }
    X = pd.DataFrame(data)
    y = np.random.choice([0, 1, 2], size=num_samples, p=[0.46, 0.24, 0.30])
    model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.06, objective='multi:softprob', random_state=42)
    model.fit(X, y)
    return model

quant_multi_ai = init_advanced_model()

# ==========================================
# [🛡️ 마스터 DB] 48개국 오피셜 전력 데이터 및 조 편성
# ==========================================
WORLD_CUP_INTEL_DB = {
    "South Korea": {"group": "A조", "stat": 1.85, "injury": 0.00, "style": "선수비역습", "friendly_score": 0.15},
    "Mexico": {"group": "A조", "stat": 1.90, "injury": 0.04, "style": "전방압박", "friendly_score": -0.08},
    "Czech Republic": {"group": "A조", "stat": 1.72, "injury": 0.02, "style": "롱볼축구", "friendly_score": 0.05},
    "Canada": {"group": "B조", "stat": 1.75, "injury": 0.02, "style": "선수비역습", "friendly_score": 0.05},
    "France": {"group": "I조", "stat": 2.45, "injury": 0.03, "style": "선수비역습", "friendly_score": 0.12},
    "Germany": {"group": "E조", "stat": 2.20, "injury": 0.01, "style": "전방압박", "friendly_score": 0.10},
    "Argentina": {"group": "J조", "stat": 2.50, "injury": 0.02, "style": "점유율", "friendly_score": 0.15},
    "Japan": {"group": "F조", "stat": 1.80, "injury": 0.01, "style": "점유율", "friendly_score": 0.10},
    "Netherlands": {"group": "F조", "stat": 2.10, "injury": 0.05, "style": "전방압박", "friendly_score": -0.05},
    "England": {"group": "C조", "stat": 2.35, "injury": 0.06, "style": "점유율", "friendly_score": 0.00},
    "Brazil": {"group": "C조", "stat": 2.40, "injury": 0.05, "style": "점유율", "friendly_score": 0.00}
}

SOCCER_OFFICIAL_MATCHES = [
    {"home": "Mexico", "away": "South Korea", "group": "A조", "desc": "🏆 [A조] 멕시코 vs 대한민국"},
    {"home": "Canada", "away": "Czech Republic", "group": "B조", "desc": "🏆 [B조] 캐나다 vs 체코"},
    {"home": "Netherlands", "away": "Japan", "group": "F조", "desc": "🏆 [F조] 네덜란드 vs 일본"},
    {"home": "France", "away": "Germany", "group": "빅매치", "desc": "🏆 [북중미 전초전] 프랑스 vs 독일"}
]

KBO_TEAM_ROSTER_DB = {
    "Doosan Bears": {"pitcher": "곽빈", "era": 3.45, "whip": 1.28, "team_ops": 0.802, "bullpen": "보통"},
    "SSG Landers": {"pitcher": "김광현", "era": 3.95, "whip": 1.38, "team_ops": 0.805, "bullpen": "보통"},
    "LG Twins": {"pitcher": "엔스", "era": 3.80, "whip": 1.35, "team_ops": 0.815, "bullpen": "과부하"},
    "Kiwoom Heroes": {"pitcher": "후라도", "era": 3.52, "whip": 1.30, "team_ops": 0.762, "bullpen": "안정"},
    "NC Dinos": {"pitcher": "하트", "era": 2.95, "whip": 1.18, "team_ops": 0.810, "bullpen": "보통"},
    "Samsung Lions": {"pitcher": "원태인", "era": 3.12, "whip": 1.20, "team_ops": 0.795, "bullpen": "안정"},
    "Lotte Giants": {"pitcher": "반즈", "era": 3.35, "whip": 1.24, "team_ops": 0.775, "bullpen": "보통"},
    "KIA Tigers": {"pitcher": "네일", "era": 2.75, "whip": 1.15, "team_ops": 0.840, "bullpen": "안정"},
    "Hanwha Eagles": {"pitcher": "류현진", "era": 3.25, "whip": 1.22, "team_ops": 0.788, "bullpen": "과부하"},
    "KT Wiz": {"pitcher": "쿠에바스", "era": 3.60, "whip": 1.25, "team_ops": 0.790, "bullpen": "안정"}
}

def fetch_real_only_stream(sport_code):
    if not ODDS_API_KEY or ODDS_API_KEY == "YOUR_API_KEY_HERE": return []
    url = f"https://api.the-odds-api.com/v4/sports/{sport_code}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        res = requests.get(url)
        if res.status_code == 200: return res.json()
    except: pass
    return []

# ==========================================
# [📊 메인 화면 UI 조립 레이어]
# ==========================================
col_top1, col_top2 = st.columns([2, 1])
with col_top1:
    st.title("💰 부자되자 (실전 계량 분석기 Pro)")
with col_top2:
    capital = st.number_input("💵 실전 초기 투자금 설정 (원)", value=1000000, step=100000)

st.divider()

# 🎛️ 사이드바: 4대 항목 가중치 백분율 분배기
st.sidebar.header("🎛️ 알고리즘 가중치 제어")
st.sidebar.markdown("항목 합산이 정확히 **100%**여야 엔진이 작동합니다.")
v_stat = st.sidebar.slider("1. 스쿼드 펀더멘탈 체급 (%)", 0, 100, 25)
v_friendly = st.sidebar.slider("2. 최근 평가전 기세 흐름 (%)", 0, 100, 25)
v_injury = st.sidebar.slider("3. 인저리 부상 공백 격차 (%)", 0, 100, 25)
v_odds = st.sidebar.slider("4. 배당 가치 매릿 비중 (%)", 0, 100, 25)
total_weight = v_stat + v_friendly + v_injury + v_odds

if total_weight == 100:
    st.sidebar.success(f"🟢 가중치 총합 100% 충족")
else:
    st.sidebar.error(f"❌ 가중치 총합: {total_weight}% (100%로 다시 맞추세요)")

tab_wc, tab_k1, tab_k2, tab_kbo = st.tabs(["🏆 2026 월드컵 / 조별스캔", "🇰🇷 K리그 1", "⚽ K리그 2", "⚾ KBO 프로야구"])

# --- [1번 탭: 2026 월드컵 / 조별 선행분석] ---
with tab_wc:
    if total_weight != 100:
        st.error("🚨 왼쪽 사이드바의 4가지 항목 가중치 총합을 정확히 100%로 맞추셔야 하단 분석 엔진이 작동합니다.")
    else:
        st.header("📋 대상 경기 조별 편성 및 4대 가중치 수치화")
        
        sel_match = st.selectbox("정밀 분석할 월드컵 매치를 고르세요:", [m['desc'] for m in SOCCER_OFFICIAL_MATCHES])
        tgt = next(m for m in SOCCER_OFFICIAL_MATCHES if m['desc'] == sel_match)
        
        h_info = WORLD_CUP_INTEL_DB[tgt['home']]
        a_info = WORLD_CUP_INTEL_DB[tgt['away']]
        
        # 슬라이더 백분율 기반 튜너 수치 치환
        c_stat = (h_info['stat'] - a_info['stat']) * (v_stat / 100.0)
        c_friendly = (h_info['friendly_score'] - a_info['friendly_score']) * (v_friendly / 100.0)
        c_injury = (h_info['injury'] - a_info['injury']) * (v_injury / 100.0)
        c_odds_weight = (v_odds / 100.0)
        
        st.success(f"📊 **[{tgt['home']}({h_info['group']}) vs {tgt['away']}({a_info['group']})] 입력된 가중치 내부 정산표**")
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        w_col1.metric("체급 최종 스코어", f"{c_stat:+.3f}", f"설정 비중 {v_stat}%")
        w_col2.metric("평가전 기세 스코어", f"{c_friendly:+.3f}", f"설정 비중 {v_friendly}%")
        w_col3.metric("부상 리스크 스코어", f"{c_injury:+.3f}", f"설정 비중 {v_injury}%")
        w_col4.metric("배당 매릿 계수", f"{c_odds_weight:.2f}", f"설정 비중 {v_odds}%")
        
        # 변수 기반 시뮬레이션 배당 정산
        pred_odds_home = round(2.10 - (c_stat * 0.4), 2)
        pred_odds_draw = 3.20
        pred_odds_away = round(2.10 + (c_stat * 0.4), 2)
        
        input_data = pd.DataFrame([{'weight_stat': c_stat, 'weight_friendly': c_friendly, 'weight_injury': c_injury, 'weight_value_odds': pred_odds_home}])
        probs = quant_multi_ai.predict_proba(input_data)[0]
        
        st.divider()
        st.subheader("🔮 승 / 무 / 패 배팅 포지션별 퀀트 지표 정산")
        bet_choice = st.radio("분석 지표를 확인하고 진입할 포지션을 선택하세요:", ["홈팀 승리 (승)", "무승부 분산 (무)", "원정팀 승리 (패)"])
        
        if "승" in bet_choice:
            target_prob = probs[0]
            target_odds = pred_odds_home
            label_text = "홈팀 승리"
        elif "무" in bet_choice:
            target_prob = probs[1]
            target_odds = pred_odds_draw
            label_text = "무승부"
        else:
            target_prob = probs[2]
            target_odds = pred_odds_away
            label_text = "원정팀 승리"
            
        b = target_odds - 1
        k_frac = (target_prob * b - (1 - target_prob)) / b if b > 0 else 0
        half_k = max(0.0, k_frac / 2)
        bet_amt = int(capital * half_k)
        
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric(f"선택 포지션 [{label_text}] 최종 승률", f"{target_prob*100:.1f}%")
        rc2.metric(f"국내 프로토 예상 배당률", f"{target_odds} 배")
        if half_k > 0:
            rc3.success(f"🟢 **추천 투자액:** **{bet_amt:,}원** (시드의 {half_k*100:.1f}%)")
        else:
            rc3.error("🔴 **추천 투자액:** **0원 (진입 마진 부족 패스)**")

# --- [2, 3번 탭: K리그 휴식기 고정] ---
with tab_k1: st.warning("🚨 현재 K리그 1은 월드컵 브레이크 기간으로 일시 휴식기 상태입니다.")
with tab_k2: st.warning("🚨 현재 K리그 2는 월드컵 브레이크 기간으로 일시 휴식기 상태입니다.")

# --- [4번 탭: KBO 야구 세이버메트릭스 계량 분석] ---
with tab_kbo:
    st.header("⚾ KBO 프로야구 당일 세이버메트릭스 매칭판")
    
    kbo_official_schedule = [
        {"home": "Doosan Bears", "away": "SSG Landers", "desc": "두산 vs SSG (잠실)"},
        {"home": "LG Twins", "away": "Kiwoom Heroes", "desc": "LG vs 키움 (고척)"},
        {"home": "NC Dinos", "away": "Samsung Lions", "desc": "NC vs 삼성 (대구)"},
        {"home": "Lotte Giants", "away": "KIA Tigers", "desc": "롯데 vs KIA (광주)"},
        {"home": "Hanwha Eagles", "away": "KT Wiz", "desc": "한화 vs KT (수원)"}
    ]
    
    sel_kbo = st.selectbox("분석할 야구 경기를 고르세요:", [s['desc'] for s in kbo_official_schedule])
    t_kbo = next(s for s in kbo_official_schedule if s['desc'] == sel_kbo)
    hm, am = KBO_TEAM_ROSTER_DB[t_kbo['home']], KBO_TEAM_ROSTER_DB[t_kbo['away']]
    
    st.success(f"📊 **[{t_kbo['home']} vs {t_kbo['away']}] 야구 투타 흐름 요약**")
    st.markdown(f"* **홈팀 선발:** {hm['pitcher']} (ERA: {hm['era']}) | 최근 팀 가중 OPS: {hm['team_ops']:.3f} | 불펜: {hm['bullpen']}")
    st.markdown(f"* **원정팀 선발:** {am['pitcher']} (ERA: {am['era']}) | 최근 팀 가중 OPS: {am['team_ops']:.3f} | 불펜: {am['bullpen']}")
    
    st.divider()
    
    # 임의 배당 고정 매칭
    f_home_odds, f_away_odds = 1.85, 1.95
    proto_home_odds = round(f_home_odds * 0.87, 2)
    
    input_bb = pd.DataFrame([{'pitcher_era_diff': hm['era'] - am['era'], 'team_ops_diff': hm['team_ops'] - am['team_ops'], 'bullpen_fatigue': 0.0, 'odds_home': f_home_odds, 'odds_away': f_away_odds}])
    prob_win = baseball_ai.predict_proba(input_bb)[0][0]
    
    yc1, yc2, yc3 = st.columns(3)
    yc1.metric("🔮 AI 선발 보정 승률", f"{prob_win*100:.1f}%")
    yc2.metric("🇰🇷 프로토 예상 배당률", f"{proto_home_odds} 배")
    
    b_b = proto_home_odds - 1
    k_frac_b = (prob_win * b_b - (1 - prob_win)) / b_b if b_b > 0 else 0
    half_kb = max(0.0, k_frac_b / 2)
    
    if half_kb > 0:
        yc3.success(f"🟢 **추천 투자액:** **{int(capital * half_kb):,}원**")
    else:
        yc3.error("🔴 **포지션 패스 (Pass)**")
