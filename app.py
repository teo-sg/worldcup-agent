import streamlit as st
import requests
from datetime import datetime

# ============================================================
# 페이지 설정 및 전역 스타일
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.8 Final",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght=400;700&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; }
    .metric-box {
        background: #1a2235;
        border: 1px solid #1e2d45;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 핵심 무결성 데이터 파이프라인
# ============================================================
def fetch_all_upcoming_odds(api_key: str, sport_key: str) -> list:
    """
    [진짜 전체 경기 데이터 파이프라인]
    개수 제한(Slicing) 전면 철폐. 마켓에 등록된 미래의 모든 예정 경기를 
    날짜/시간 제한 없이 100% 통째로 긁어옵니다. (가짜 0%)
    """
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        f"?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal"
    )
    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            return res.json()
        if res.status_code == 404:
            st.warning(f"📡 {sport_key} 채널은 현재 마켓 비개장 상태입니다.")
    except Exception as e:
        st.error(f"네트워크 동기화 오류: {e}")
    return []

def normalize_implied(h_imp: float, d_imp: float, a_imp: float) -> dict:
    total = h_imp + d_imp + a_imp
    if total == 0: return {"h": 0.33, "d": 0.34, "a": 0.33}
    return {"h": h_imp / total, "d": d_imp / total, "a": a_imp / total}

def half_kelly(prob: float, odds_decimal: float) -> float:
    b = odds_decimal - 1
    if b <= 0: return 0.0
    k = (prob * b - (1 - prob)) / b
    return max(0.0, k / 2)

def kelly_card(col, label: str, prob: float, odds: float, capital: int, color: str):
    k = half_kelly(prob, odds)
    amount = int(capital * k)
    with col:
        st.markdown(f"""
        <div class="metric-box" style="border-color:{color}44">
            <div style="font-size:11px;color:#64748b;letter-spacing:.08em">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{color};margin:6px 0">{prob*100:.1f}%</div>
            <div style="font-size:12px;color:#64748b">정형 보정 확률</div>
            <div style="margin:10px 0;font-size:13px">배당 <strong style="color:{color}">{odds}배</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if k > 0: st.success(f"추천 배분 {k*100:.1f}% → **{amount:,}원**")
        else: st.error("진입 마진 부족 (Pass)")

# ============================================================
# 메인 상단 통제 센터
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.8")
st.caption("글로벌 자본 마켓 등록 전경기(All Matches) 무삭제 전수 로딩 시스템 · 가짜 데이터 0%")
st.divider()

top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input("🔓 the-odds-api.com API Key 입력", type="password", placeholder="your-api-key-here")
with top_c2:
    capital = st.number_input("💵 실전 초기 운용 자산 (원)", min_value=10_000, value=1_000_000, step=100_000, format="%d")

st.divider()

if not api_key:
    st.info("👆 화면 상단에 내 API Key를 주입하시면 발매 중인 '전체 경기' 목록 동기화가 활성화됩니다.")
    st.stop()

tab_soccer, tab_kbo = st.tabs(["⚽ 1. 국제 월드컵 / A매치 전경기 마스터보드", "⚾ 2. KBO 프로야구 전경기 마스터보드"])

# ------------------------------------------------------------
# [탭 1] ⚽ 축구 전경기 마스터보드 (무삭제 버전)
# ------------------------------------------------------------
with tab_soccer:
    st.markdown("#### 🏆 마켓에 발매된 미래 예정 친선경기 / A매치 전체 리스트")
    
    st.markdown("##### 🎛️ 팩트 변수 가중치 조율")
    am_in1, am_in2, am_in3 = st.columns(3)
    with am_in1: am_stat_v = st.number_input("스쿼드 전력 격차 지수 보정치 (-2.0 ~ 2.0)", -2.0, 2.0, 0.0, 0.1, key="am_s_v")
    with am_in2: am_form_v = st.number_input("최신 5경기 흐름 격차 점수 (-1.0 ~ 1.0)", -1.0, 1.0, 0.0, 0.1, key="am_f_v")
    with am_in3: am_inj_v = st.number_input("핵심 라인업 인저리 누수 점수 (-0.5 ~ 0.5)", -0.5, 0.5, 0.0, 0.05, key="am_i_v")

    st.divider()

    if st.button("🔄 발매 중인 축구 전체 경기 피드 땡겨오기", key="btn_load_all_soccer"):
        with st.spinner("해외 자본망에서 누락 없이 전체 축구 일정을 파싱 중..."):
            st.session_state["raw_all_soccer"] = fetch_all_upcoming_odds(api_key, "soccer_international")

    soccer_games = st.session_state.get("raw_all_soccer", [])

    if not soccer_games:
        st.info("💡 위 버튼을 누르면 오늘, 내일 새벽, 이번 주말까지 베팅 마켓에 올라와 있는 모든 A매치 경기가 유실 없이 통째로 정렬됩니다.")
    else:
        # 💡 [핵심 교정] 단 하나의 경기도 자르지 않고 전수 콤보박스에 빌딩
        soccer_labels = []
        for g in soccer_games:
            try:
                g_time = g['commence_time'].replace('T', ' ').replace('Z', '')
            except:
                g_time = "시간미정"
            soccer_labels.append(f"⚽ [{g_time}] {g['home_team']} vs {g['away_team']}")

        selected_soccer = st.selectbox("🎯 분석 및 Kelly 자산 배분을 산출할 경기를 선택하세요 (전수 노출):", soccer_labels, key="sel_soc_all")
        tgt_soccer_game = soccer_games[soccer_labels.index(selected_soccer)]

        # 배당 데이터 파싱 및 퀀트 연산부 직결
        try:
            outcomes = tgt_soccer_game["bookmakers"][0]["markets"][0]["outcomes"]
            odds_map = {o["name"]: o["price"] for o in outcomes}
            h_o = odds_map.get(tgt_soccer_game["home_team"])
            a_o = odds_map.get(tgt_soccer_game["away_team"])
            d_o = odds_map.get("Draw", 0.0)
            
            if h_o and a_o:
                st.success(f"🟢 [실시간 시세 연동 완료] {tgt_soccer_game['home_team']} vs {tgt_soccer_game['away_team']} 배당판 분석 개방")
                norm = normalize_implied(1/h_o, (1/d_o if d_o else 0.0), 1/a_o)
                prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
                adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
                adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
                adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
                
                st.markdown("##### 📐 정밀 가격 기반 Half-Kelly 자산 배분 결과")
                cols = st.columns(3)
                kelly_card(cols[0], f"🏠 홈 ({tgt_soccer_game['home_team']})", adj_h, h_o, capital, "#00e5ff")
                kelly_card(cols[1], "🤝 무승부", adj_d, d_o, capital, "#64748b")
                kelly_card(cols[2], f"🚌 원정 ({tgt_soccer_game['away_team']})", adj_a, a_o, capital, "#ffd700")
            else:
                st.error("이 경기의 홈/원정 배당 데이터를 파싱할 수 없습니다.")
        except Exception as e:
            st.warning("📡 해당 매치의 실시간 배당 시세가 일시적으로 잠겼습니다. 아래에 프로토 배당을 주입해 즉시 수동 연산하세요.")
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1: s_h_odds = st.number_input("프로토 홈 배당 직접 기입", min_value=1.01, value=2.00, step=0.01)
            with m_c2: s_d_odds = st.number_input("프로토 무승부 배당 직접 기입", min_value=1.01, value=3.20, step=0.01)
            with m_c3: s_a_odds = st.number_input("프로토 원정 배당 직접 기입", min_value=1.01, value=3.40, step=0.01)
            
            norm = normalize_implied(1/s_h_odds, 1/s_d_odds, 1/s_a_odds)
            prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
            adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
            adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
            adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
            
            cols = st.columns(3)
            kelly_card(cols[0], f"🏠 홈 수동 연산", adj_h, s_h_odds, capital, "#00e5ff")
            kelly_card(cols[1], "🤝 무승부 수동 연산", adj_d, s_d_odds, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 수동 연산", adj_a, s_a_odds, capital, "#ffd700")

# ------------------------------------------------------------
# [탭 2] ⚾ KBO 프로야구 전경기 마스터보드 (무삭제 버전)
# ------------------------------------------------------------
with tab_kbo:
    st.markdown("#### ⚾ KBO 프로야구 발매 중인 전경기 명세")
    
    if st.button("🔄 KBO 발매 중인 전체 경기 피드 땡겨오기", key="btn_load_all_kbo"):
        with st.spinner("야구 배당판 전수 스캔 중..."):
            st.session_state["raw_all_kbo"] = fetch_all_upcoming_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("raw_all_kbo", [])

    if not kbo_games:
        st.info("💡 화~일 주간 경기 발매 기간에 버튼을 누르시면 당일 및 예정된 KBO 5대 대진표가 무삭제로 전부 출력됩니다.")
    else:
        kbo_labels = []
        for g in kbo_games:
            try:
                g_time = g['commence_time'].replace('T', ' ').replace('Z', '')
            except:
                g_time = "시간미정"
            kbo_labels.append(f"⚾ [{g_time}] {g['home_team']} vs {g['away_team']}")

        selected_kbo = st.selectbox("🎯 분석할 KBO 경기 선택 (전수 노출):", kbo_labels, key="sel_kbo_all")
        tgt_kbo_game = kbo_games[kbo_labels.index(selected_kbo)]

        try:
            outcomes = tgt_kbo_game["bookmakers"][0]["markets"][0]["outcomes"]
            odds_map = {o["name"]: o["price"] for o in outcomes}
            h_o = odds_map.get(tgt_kbo_game["home_team"])
            a_o = odds_map.get(tgt_kbo_game["away_team"])
            
            if h_o and a_o:
                st.divider()
                st.markdown("##### ⚾ 선발 투수 ERA 마진 교정")
                era_c1, era_c2 = st.columns(2)
                with era_c1: h_era = st.number_input(f"🏠 {tgt_kbo_game['home_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01)
                with era_c2: a_era = st.number_input(f"🚌 {tgt_kbo_game['away_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01)

                norm = normalize_implied(1/h_o, 0.0, 1/a_o)
                era_diff = h_era - a_era
                era_adj = max(-0.05, min(0.05, era_diff * -0.01))
                adj_h = max(0.05, min(0.95, norm["h"] + era_adj))
                adj_a = 1.0 - adj_h

                st.divider()
                st.markdown(f"##### 📐 Kelly 배분 결과 — {tgt_kbo_game['home_team']} vs {tgt_kbo_game['away_team']}")
                kbo_cols = st.columns(2)
                kelly_card(kbo_cols[0], f"🏠 홈 ({tgt_kbo_game['home_team']})", adj_h, h_o, capital, "#00e5ff")
                kelly_card(kbo_cols[1], f"🚌 원정 ({tgt_kbo_game['away_team']})", adj_a, a_o, capital, "#ffd700")
        except:
            st.error("이 경기의 실시간 야구 배당판을 파싱할 수 없습니다.")
