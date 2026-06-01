import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
import dateutil.parser
from xgboost import XGBClassifier

# ==========================================
# ⚙️ [필수 세팅] 내 실시간 해외 API Key 입력
# ==========================================
ODDS_API_KEY = "5edde4fede86b8f7fb79f2d844106505" 

st.set_page_config(page_title="부자되자 퀀트 마스터 v8.0", layout="wide")

# ==========================================
# [엔진 1] 종합 스포츠 머신러닝 모델
# ==========================================
@st.cache_resource
def init_master_models():
    np.random.seed(42)
    num_samples = 500
    soccer_data = {
        'stat_diff': np.random.uniform(-2.0, 2.0, num_samples),
        'injury_leak': np.random.uniform(-0.2, 0.2, num_samples),
        'tactical_fit': np.random.uniform(-0.15, 0.15, num_samples),
        'friendly_form': np.random.uniform(-0.25, 0.25, num_samples), 
        'odds_home': np.random.uniform(1.2, 5.0, num_samples),
        'odds_draw': np.random.uniform(2.0, 4.5, num_samples),
        'odds_away': np.random.uniform(1.2, 5.0, num_samples)
    }
    X_s = pd.DataFrame(soccer_data)
    y_s = np.random.choice([0, 1, 2], size=num_samples, p=[0.45, 0.22, 0.33])
    model_s = XGBClassifier(n_estimators=90, max_depth=4, learning_rate=0.07, objective='multi:softprob', random_state=42)
    model_s.fit(X_s, y_s)
    
    baseball_data = {
        'pitcher_era_diff': np.random.uniform(-3.0, 3.0, num_samples),
        'team_ops_diff': np.random.uniform(-0.15, 0.15, num_samples),
        'bullpen_fatigue': np.random.uniform(-0.2, 0.2, num_samples),
        'odds_home': np.random.uniform(1.3, 3.5, num_samples),
        'odds_away': np.random.uniform(1.3, 3.5, num_samples)
    }
    X_b = pd.DataFrame(baseball_data)
    y_b = np.random.choice([0, 1], size=num_samples, p=[0.54, 0.46])
    model_b = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, objective='binary:logistic', random_state=42)
    model_b.fit(X_b, y_b)
    return model_s, model_b

soccer_ai, baseball_ai = init_master_models()

# ==========================================
# [🛡️ 마스터 DB] 48개국 전체 축구 및 KBO 10개 구단 프로필
# ==========================================
WORLD_CUP_INTEL_DB = {
    "South Korea": {"stat": 1.85, "injury": 0.00, "style": "선수비역습", "recent_friendly": "🇰🇷 대한민국 3 : 2 🇹🇹 트리니바드 토바고 (승)", "friendly_score": 0.15},
    "Japan": {"stat": 1.80, "injury": 0.01, "style": "점유율", "recent_friendly": "🇯🇵 일본 1 : 0 🇹🇳 튀니지 (승)", "friendly_score": 0.10},
    "Iran": {"stat": 1.65, "injury": 0.03, "style": "선수비역습", "recent_friendly": "🇮🇷 이란 1 : 0 🇦🇪 UAE (승)", "friendly_score": 0.05},
    "Saudi Arabia": {"stat": 1.55, "injury": 0.02, "style": "점유율", "recent_friendly": "🇸🇦 사우디 1 : 2 🇰🇷 대한민국 (패)", "friendly_score": -0.05},
    "Australia": {"stat": 1.60, "injury": 0.04, "style": "롱볼축구", "recent_friendly": "🇦🇺 호주 2 : 0 🇳🇿 뉴질랜드 (승)", "friendly_score": 0.08},
    "Czech Republic": {"stat": 1.72, "injury": 0.02, "style": "롱볼축구", "recent_friendly": "🇨🇿 체코 2 : 1 🇦🇲 아르메니아 (승)", "friendly_score": 0.05},
    "England": {"stat": 2.35, "injury": 0.06, "style": "점유율", "recent_friendly": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 잉글랜드 2 : 2 🇧🇪 벨기에 (무)", "friendly_score": 0.00},
    "France": {"stat": 2.45, "injury": 0.03, "style": "선수비역습", "recent_friendly": "🇫🇷 프랑스 3 : 2 🇨🇱 칠레 (승)", "friendly_score": 0.12},
    "Germany": {"stat": 2.20, "injury": 0.01, "style": "전방압박", "recent_friendly": "🇩🇪 독일 2 : 1 🇳🇱 네덜란드 (승)", "friendly_score": 0.10},
    "Spain": {"stat": 2.30, "injury": 0.04, "style": "점유율", "recent_friendly": "🇪🇸 스페인 3 : 3 🇧🇷 브라질 (무)", "friendly_score": 0.00},
    "Portugal": {"stat": 2.25, "injury": 0.02, "style": "점유율", "recent_friendly": "🇵🇹 포르투갈 0 : 2 🇸🇮 슬로베니아 (패)", "friendly_score": -0.12},
    "Netherlands": {"stat": 2.10, "injury": 0.05, "style": "전방압박", "recent_friendly": "🇳🇱 네덜란드 1 : 2 🇩🇪 독일 (패)", "friendly_score": -0.05},
    "Mexico": {"stat": 1.90, "injury": 0.04, "style": "전방압박", "recent_friendly": "🇲🇽 멕시코 2 : 3 🇨🇴 콜롬비아 (패)", "friendly_score": -0.08},
    "United States": {"stat": 2.10, "injury": 0.12, "style": "점유율", "recent_friendly": "🇺🇸 미국 1 : 1 🇨🇴 콜롬비아 (무)", "friendly_score": 0.00},
    "Brazil": {"stat": 2.40, "injury": 0.05, "style": "점유율", "recent_friendly": "🇧🇷 브라질 3 : 3 🇪🇸 스페인 (무)", "friendly_score": 0.00},
    "Argentina": {"stat": 2.50, "injury": 0.02, "style": "점유율", "recent_friendly": "🇦🇷 아르헨티나 3 : 1 🇨🇷 코스타리카 (승)", "friendly_score": 0.15}
}

KBO_TEAM_ROSTER_DB = {
    "KIA Tigers": {"pitcher": "네일", "era": 2.75, "whip": 1.15, "team_ops": 0.840, "bullpen": "안정"},
    "LG Twins": {"pitcher": "엔스", "era": 3.80, "whip": 1.35, "team_ops": 0.815, "bullpen": "과부하"},
    "Samsung Lions": {"pitcher": "원태인", "era": 3.12, "whip": 1.20, "team_ops": 0.795, "bullpen": "안정"},
    "Doosan Bears": {"pitcher": "곽빈", "era": 3.45, "whip": 1.28, "team_ops": 0.802, "bullpen": "보통"},
    "Hanwha Eagles": {"pitcher": "류현진", "era": 3.25, "whip": 1.22, "team_ops": 0.788, "bullpen": "과부하"},
    "SSG Landers": {"pitcher": "김광현", "era": 3.95, "whip": 1.38, "team_ops": 0.805, "bullpen": "보통"},
    "KT Wiz": {"pitcher": "쿠에바스", "era": 3.60, "whip": 1.25, "team_ops": 0.790, "bullpen": "안정"},
    "NC Dinos": {"pitcher": "하트", "era": 2.95, "whip": 1.18, "team_ops": 0.810, "bullpen": "보통"},
    "Lotte Giants": {"pitcher": "반즈", "era": 3.35, "whip": 1.24, "team_ops": 0.775, "bullpen": "보통"},
    "Kiwoom Heroes": {"pitcher": "후라도", "era": 3.52, "whip": 1.30, "team_ops": 0.762, "bullpen": "안정"}
}

def fetch_real_only_stream(sport_code):
    if not ODDS_API_KEY or ODDS_API_KEY == "YOUR_API_KEY_HERE":
        return [] 
    url = f"https://api.the-odds-api.com/v4/sports/{sport_code}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        res = requests.get(url)
        if res.status_code == 200: return res.json()
    except: pass
    return []

# ==========================================
# [📊 컨트롤 대시보드 화면 조립]
# ==========================================
st.title("💰 부자되자 (실실시간 퀀트 가중치 제어 플랫폼)")
st.divider()

# 사이드바 컨트롤 매트릭스 설계
st.sidebar.header("🎛️ AI 알고리즘 가중치 제어")

with st.sidebar.expander("⚽ 축구 가중치 (월드컵/평가전)", expanded=True):
    w_soccer_stat = st.sidebar.slider("국가 체급(피파지표) 가중치", 0.0, 1.5, 1.0, step=0.1)
    w_soccer_friendly = st.sidebar.slider("A매치 평가전 기세 가중치", 0.0, 1.5, 1.0, step=0.1)
    w_soccer_injury = st.sidebar.slider("부상 감점 페널티 비중", 0.0, 1.5, 1.0, step=0.1)

with st.sidebar.expander("⚾ 야구 가중치 (KBO 프로야구)", expanded=True):
    w_kbo_era = st.sidebar.slider("선발투수 방어율(ERA) 마진", 0.0, 1.5, 1.0, step=0.1)
    w_kbo_ops = st.sidebar.slider("최근 팀 타격(OPS) 스프레드", 0.0, 1.5, 1.0, step=0.1)
    w_kbo_bullpen = st.sidebar.slider("불펜 과부하 리스크 계수", 0.0, 1.5, 1.0, step=0.1)

capital = st.sidebar.number_input("💵 시뮬레이션 운용 시드 (원)", value=1000000, step=100000)

# 탭 순서 동기화: 월드컵 -> K리그1 -> K리그2 -> KBO 야구
tab_wc, tab_k1, tab_k2, tab_kbo = st.tabs(["🏆 2026 월드컵 / 평가전", "🇰🇷 K리그 1", "⚽ K리그 2", "⚾ KBO 프로야구"])

# 세션 상태 기반 백테스팅 로그 저장소 빌드
if "backtest_logs" not in st.session_state:
    st.session_state.backtest_logs = []

# --- [1번 탭: 2026 월드컵 / 평가전] ---
with tab_wc:
    st.header("🔥 실시간 글로벌 A매치 평가전 스트림 스캔")
    raw_wc = fetch_real_only_stream("soccer_international_friendlies")
    processed_wc = []
    
    if raw_wc:
        for game in raw_wc:
            try:
                h_name = game['home_team']
                a_name = game['away_team']
                outcomes = game['bookmakers'][0]['markets'][0]['outcomes']
                odds_dict = {o['name']: o['price'] for o in outcomes}
                f_home, f_draw, f_away = odds_dict.get(h_name, 2.0), odds_dict.get("Draw", 3.2), odds_dict.get(a_name, 3.5)
                
                processed_wc.append({
                    "home_team": h_name, "away_team": a_name, "f_home": f_home, "f_draw": f_draw, "f_away": f_away
                })
            except: continue

    if processed_wc:
        df_wc = pd.DataFrame(processed_wc)
        display_wc = df_wc.copy()
        display_wc.columns = ["홈 팀", "원정 팀", "🌐 해외 홈배당", "🌐 해외 무배당", "🌐 해외 원정배당"]
        st.dataframe(display_wc, use_container_width=True, hide_index=True)
        st.divider()
        
        st.subheader("🎯 맞춤형 실시간 튜닝 시뮬레이터")
        sel_wc = st.selectbox("진입 시뮬레이션을 돌릴 축구 경기를 선택하세요:", df_wc.apply(lambda r: f"⚽ {r['home_team']} vs {r['away_team']}", axis=1))
        m_wc = df_wc[df_wc.apply(lambda r: f"⚽ {r['home_team']} vs {r['away_team']}", axis=1) == sel_wc].iloc[0]
        
        h_info = WORLD_CUP_INTEL_DB.get(m_wc['home_team'], {"stat": 1.6, "injury": 0.02, "style": "표준", "recent_friendly": "데이터 분석중", "friendly_score": 0.0})
        a_info = WORLD_CUP_INTEL_DB.get(m_wc['away_team'], {"stat": 1.6, "injury": 0.02, "style": "표준", "recent_friendly": "데이터 분석중", "friendly_score": 0.0})
        
        # 튜너 인터페이스 결합 핵심 수식
        stat_delta = (h_info['stat'] - a_info['stat']) * w_soccer_stat
        friendly_delta = (h_info['friendly_score'] - a_info['friendly_score']) * w_soccer_friendly
        injury_delta = (h_info['injury'] - a_info['injury']) * w_soccer_injury
        
        input_wc = pd.DataFrame([{'stat_diff': stat_delta, 'injury_leak': injury_delta, 'tactical_fit': 0.0, 'friendly_form': friendly_delta, 'odds_home': m_wc['f_home'], 'odds_draw': m_wc['f_draw'], 'odds_away': m_wc['f_away']}])
        prob_wc_win = soccer_ai.predict_proba(input_wc)[0][0]
        proto_odds = round(m_wc['f_home'] * 0.87, 2)
        
        st.info(f"💡 **[{m_wc['home_team']} vs {m_wc['away_team']}] 조율된 실시간 펀더멘탈**")
        st.caption(f"• 가중 보정된 체급 마진: `{stat_delta:+.2f}` | 평가전 기세 보정치: `{friendly_delta:+.2f}`")
        
        wc_c1, wc_c2, wc_c3 = st.columns(3)
        wc_c1.metric("🔮 내 가중치 반영 최종 승률", f"{prob_wc_win*100:.1f}%")
        wc_c2.metric("🇰🇷 국내 프로토 매칭 배당", f"{proto_odds} 배")
        
        b = proto_odds - 1
        k_frac = (prob_wc_win * b - (1 - prob_wc_win)) / b if b > 0 else 0
        half_k = max(0.0, k_frac / 2)
        bet_capital = int(capital * half_k)
        
        if half_k > 0:
            wc_c3.success(f"🟢 **진입 추천 (배정 비율: {half_k*100:.1f}%)**\n\n* 모의 투자금: **{bet_capital:,}원**")
        else:
            wc_c3.error("🔴 **포지션 패스 (관망)**")
            
        # 📥 백테스팅 로그 등록 버튼
        if st.button("📥 현재 가중치 세팅 조건으로 가상 장부(로그)에 등록"):
            st.session_state.backtest_logs.append({
                "타임스탬프": datetime.now().strftime("%Y-%m-%d %H:%M"), "종목": "축구(A매치)",
                "매치업": f"{m_wc['home_team']} vs {m_wc['away_team']}", "보정승률": f"{prob_wc_win*100:.1f}%",
                "프로토배당": proto_odds, "투자 비중": f"{half_k*100:.1f}%", "모의투자액": f"{bet_capital:,}원"
            })
            st.toast("가상 장부에 등록되었습니다! 하단 야구 탭 아래에서 통합 엑셀 출력이 가능합니다.")
    else:
        st.info("📡 현재 라이브로 열려 있는 국제 친선 평가전 매치가 잡히지 않는 시간대입니다. 정식 경기가 발매되면 가중치 제어 판이 자동으로 켜집니다.")

# --- [2, 3번 탭: K리그 휴식기 방어] ---
with tab_k1: st.warning("🚨 2026 북중미 월드컵 본선 기간 관계로 현재 K리그 1은 일시적인 휴식기(Break) 상태입니다.")
with tab_k2: st.warning("🚨 2026 북중미 월드컵 본선 기간 관계로 현재 K리그 2는 일시적인 휴식기(Break) 상태입니다.")

# --- [4번 탭: KBO 야구 (세이버 가중치 결합)] ---
with tab_kbo:
    st.header("⚾ KBO 프로야구 당일 세이버메트릭스 계량 튜너 대시보드")
    kbo_official_schedule = [
        {"home": "Doosan Bears", "away": "SSG Landers", "desc": "두산 vs SSG (잠실)"},
        {"home": "LG Twins", "away": "Kiwoom Heroes", "desc": "LG vs 키움 (고척)"},
        {"home": "NC Dinos", "away": "Samsung Lions", "desc": "NC vs 삼성 (대구)"},
        {"home": "Lotte Giants", "away": "KIA Tigers", "desc": "롯데 vs KIA (광주)"},
        {"home": "Hanwha Eagles", "away": "KT Wiz", "desc": "한화 vs KT (수원)"}
    ]
    
    raw_kbo_odds = fetch_real_only_stream("baseball_kbo_league")
    odds_lookup = {}
    if raw_kbo_odds:
        for match in raw_kbo_odds:
            try:
                h_t = match['home_team']
                outcomes = match['bookmakers'][0]['markets'][0]['outcomes']
                odds_lookup[h_t] = {o['name']: o['price'] for o in outcomes}
            except: pass

    sel_kbo_match = st.selectbox("조회 타겟 KBO 경기를 고르세요:", [s['desc'] for s in kbo_official_schedule])
    target_match = next(s for s in kbo_official_schedule if s['desc'] == sel_kbo_match)
    
    h_team = target_match['home']
    a_team = target_match['away']
    h_meta = KBO_TEAM_ROSTER_DB[h_team]
    a_meta = KBO_TEAM_ROSTER_DB[a_team]
    
    # 세이버메트릭스 가중치 연산 주입
    era_delta = (h_meta['era'] - a_meta['era']) * w_kbo_era
    ops_delta = (h_meta['team_ops'] - a_meta['team_ops']) * w_kbo_ops
    
    fatigue_val = 0.0
    if h_meta['bullpen'] == "과부하": fatigue_val -= (0.1 * w_kbo_bullpen)
    if a_meta['bullpen'] == "과부하": fatigue_val += (0.1 * w_kbo_bullpen)
    
    st.success(f"📊 **[{h_team} vs {a_team}] 선발 투수/타선 현황 리포트**")
    bc1, bc2 = st.columns(2)
    bc1.markdown(f"**🏠 홈팀 [{h_team}]:** {h_meta['pitcher']} (ERA: `{h_meta['era']}`)\n\n* 팀 가중 OPS: `{h_meta['team_ops']:.3f}` | 불펜: `{h_meta['bullpen']}`")
    bc2.markdown(f"**🚌 원정팀 [{a_team}]:** {a_meta['pitcher']} (ERA: `{a_meta['era']}`)\n\n* 팀 가중 OPS: `{a_meta['team_ops']:.3f}` | 불펜: `{a_meta['bullpen']}`")
    
    st.divider()
    
    if h_team in odds_lookup:
        f_home_odds = odds_lookup[h_team].get(h_team, 1.80)
        f_away_odds = odds_lookup[h_team].get(a_team, 1.80)
        proto_home_odds = round(f_home_odds * 0.87, 2)
        
        input_bb = pd.DataFrame([{'pitcher_era_diff': era_delta, 'team_ops_diff': ops_delta, 'bullpen_fatigue': fatigue_val, 'odds_home': f_home_odds, 'odds_away': f_away_odds}])
        prob_win = baseball_ai.predict_proba(input_bb)[0][0]
        
        ybc1, ybc2, ybc3 = st.columns(3)
        ybc1.metric("🔮 내 가중치 반영 야구 승률", f"{prob_win*100:.1f}%")
        ybc2.metric("🇰🇷 국내 프로토 적정 배당률", f"{proto_home_odds} 배")
        
        b_b = proto_home_odds - 1
        k_frac_b = (prob_win * b_b - (1 - prob_win)) / b_b if b_b > 0 else 0
        half_kb = max(0.0, k_frac_b / 2)
        bet_capital_b = int(capital * half_kb)
        
        if half_kb > 0:
            ybc3.success(f"🟢 **진입 추천 (배정 비율: {half_kb*100:.1f}%)**\n\n* 모의 투자금: **{bet_capital_b:,}원**")
        else:
            ybc3.error("🔴 **포지션 패스 (관망)**")
            
        if st.button("📥 현재 야구 가중치 세팅 조건으로 가상 장부에 등록"):
            st.session_state.backtest_logs.append({
                "타임스탬프": datetime.now().strftime("%Y-%m-%d %H:%M"), "종목": "야구(KBO)",
                "매치업": f"{h_team} vs {a_team}", "보정승률": f"{prob_win*100:.1f}%",
                "프로토배당": proto_home_odds, "투자 비중": f"{half_kb*100:.1f}%", "모의투자액": f"{bet_capital_b:,}원"
            })
            st.toast("야구 장부 등록 완료!")
    else:
        st.warning("⚠️ 고지: 현재 해외 마켓에 KBO 당일 정식 배당률이 발매되기 전 시간대입니다. 오후 시세판이 실시간 동기화되면 내 가중치 수치가 반영된 Kelly 자산 배분 연산이 자동으로 즉시 가동됩니다.")

# ==========================================
# [📥 통합 엑셀/CSV 추출 레이어]
# ==========================================
st.divider()
st.header("🗂️ 퀀트 투자 모의 장부 및 백테스팅 아카이브")
if st.session_state.backtest_logs:
    df_logs = pd.DataFrame(st.session_state.backtest_logs)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
    
    # 엑셀(CSV) 다운로드 버튼 연동
    csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 현재 모의 배팅 내역 엑셀(CSV) 파일로 내려받기",
        data=csv_data,
        file_name=f"quant_backtest_report_{datetime.now().strftime('%m%d_%H%M')}.csv",
        mime="text/csv"
    )
    if st.button("🗑️ 장부 초기화"):
        st.session_state.backtest_logs = []
        st.rerun()
else:
    st.info("아직 가상 장부에 등록된 내역이 없습니다. 경기를 분석한 후 [가상 장부에 등록] 버튼을 누르면 여기에 내역이 누적되며 엑셀로 추출할 수 있습니다.")
