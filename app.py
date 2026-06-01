import streamlit as st
import requests

# ============================================================
# 페이지 설정 및 전역 스타일
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.3",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
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
# 핵심 무결성 퀀트 연산 로직 엔진
# ============================================================
def fetch_odds(api_key: str, sport_key: str) -> list:
    """The Odds API 채널 실시간 시세 스트리밍"""
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        f"?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal"
    )
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return res.json()
        if res.status_code == 404:
            st.warning(f"📡 {sport_key} 채널은 현재 마켓 비개장 상태입니다. 수동 제어판을 활용하세요.")
        else:
            st.error(f"API 오류 {res.status_code}: {res.text[:200]}")
    except Exception as e:
        st.error(f"네트워크 연결 실패: {e}")
    return []


def normalize_implied(h_imp: float, d_imp: float, a_imp: float) -> dict:
    """글로벌 자본 마진(Overround)을 완벽히 소거한 순수 수학적 내재 확률 도출"""
    total = h_imp + d_imp + a_imp
    if total == 0:
        return {"h": 0.33, "d": 0.34, "a": 0.33}
    return {"h": h_imp / total, "d": d_imp / total, "a": a_imp / total}


def half_kelly(prob: float, odds_decimal: float) -> float:
    """Half-Kelly 공식을 자산 훼손 방어선(최대 자산의 50% 제한)에 맞춘 배분율 연산"""
    b = odds_decimal - 1
    if b <= 0:
        return 0.0
    k = (prob * b - (1 - prob)) / b
    return max(0.0, k / 2)


def kelly_card(col, label: str, prob: float, odds: float, capital: int, color: str):
    """최종 자산 분배 금액 출력 컴포넌트"""
    k = half_kelly(prob, odds)
    amount = int(capital * k)
    with col:
        st.markdown(f"""
        <div class="metric-box" style="border-color:{color}44">
            <div style="font-size:11px;color:#64748b;letter-spacing:.08em">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{color};margin:6px 0">{prob*100:.1f}%</div>
            <div style="font-size:12px;color:#64748b">정형 보정 확률</div>
            <div style="margin:10px 0;font-size:13px">환산 배당 <strong style="color:{color}">{odds}배</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if k > 0:
            st.success(f"추천 배분 {k*100:.1f}% → **{amount:,}원**")
        else:
            st.error("진입 마진 부족 (Pass)")


def parse_game_odds(game: dict) -> dict | None:
    """실시간 제이슨 패키지에서 배당 데이터 파싱 추출"""
    try:
        outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
        odds_map = {o["name"]: o["price"] for o in outcomes}
        h_o = odds_map.get(game["home_team"])
        a_o = odds_map.get(game["away_team"])
        d_o = odds_map.get("Draw", 0.0)
        if not h_o or not a_o:
            return None
        return {"h": h_o, "a": a_o, "d": d_o}
    except (KeyError, IndexError):
        return None


# ============================================================
# 메인 상단 통제소 (API Key 및 자산 설정)
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.3")
st.caption("실시간 글로벌 배당 분석 · 4대 핵심 변수 가중치 융합 알고리즘 · 가짜 데이터 0%")
st.divider()

top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input(
        "🔓 the-odds-api.com API Key 입력",
        type="password",
        placeholder="your-api-key-here"
    )
with top_c2:
    capital = st.number_input(
        "💵 실전 초기 운용 자산 (원)",
        min_value=10_000,
        max_value=100_000_000,
        value=1_000_000,
        step=100_000,
        format="%d"
    )

st.divider()

if not api_key:
    st.info("👆 화면 상단에 내 발급 API Key와 시드머니를 입력하시면 리얼타임 계량 보드가 활성화됩니다.")
    st.stop()

# ============================================================
# ⚙️ [정밀 분리] 3대 대진 퀀트 탭 레이아웃
# ============================================================
tab_worldcup, tab_amaet_soccer, tab_kbo_baseball = st.tabs([
    "🏆 1. FIFA 월드컵 본선", 
    "⚽ 2. 국제 A매치 / 친선경기", 
    "⚾ 3. KBO 프로야구"
])

# ------------------------------------------------------------
# [탭 1] 🏆 FIFA 월드컵 본선 분석 엔진 (로직 완벽 탑재)
# ------------------------------------------------------------
with tab_worldcup:
    st.markdown("#### 🏆 2026 FIFA 월드컵 본선 실시간 배당 분석")
    
    # 💡 데이터 공백기에도 직관 가중치 조율이 가능하도록 4대 가중치 튜너 마운트
    st.markdown("##### 🎛️ 팩트 변수 가중치 조율")
    wc_in1, wc_in2, wc_in3 = st.columns(3)
    with wc_in1: w_stat_v = st.number_input("스쿼드 전력 격차 지수 보정치 (-2.0 ~ 2.0)", -2.0, 2.0, 0.0, 0.1, key="wc_s_v")
    with wc_in2: w_form_v = st.number_input("최신 5경기 흐름 격차 점수 (-1.0 ~ 1.0)", -1.0, 1.0, 0.0, 0.1, key="wc_f_v")
    with wc_in3: w_inj_v = st.number_input("핵심 라인업 인저리 누수 점수 (-0.5 ~ 0.5)", -0.5, 0.5, 0.0, 0.05, key="wc_i_v")

    wc_manual = st.toggle("📝 월드컵 수동 배당 입력 분석 모드", value=True, key="wc_man")
    
    if wc_manual:
        st.markdown("##### 배당 수동 주입 연산")
        w_c1, w_c2, w_c3 = st.columns(3)
        with w_c1:
            m_h_odds = st.number_input("홈팀 배당율", min_value=1.01, value=2.10, step=0.01, key="w_h")
            m_h_label = st.text_input("홈팀 국명", value="대한민국", key="w_hl")
        with w_c2:
            m_d_odds = st.number_input("무승부 배당율", min_value=1.01, value=3.20, step=0.01, key="w_d")
        with w_c3:
            m_a_odds = st.number_input("원정팀 배당율", min_value=1.01, value=3.50, step=0.01, key="w_a")
            m_a_label = st.text_input("원정팀 국명", value="멕시코", key="w_al")
            
        # 💡 [로직 재장착] 배당 내재확률 계산 + 사용자의 오피셜 기사 기반 팩트 가중치 결합 수학 연산
        norm = normalize_implied(1/m_h_odds, 1/m_d_odds, 1/m_a_odds)
        prob_adj = (w_stat_v * 0.08) + (w_form_v * 0.04) - (w_inj_v * 0.04)
        adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
        adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
        adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
        
        st.divider()
        st.markdown(f"##### 📐 Kelly 배분 결과 — {m_h_label} vs {m_a_label}")
        cols = st.columns(3)
        kelly_card(cols[0], f"🏠 홈 ({m_h_label})", adj_h, m_h_odds, capital, "#00e5ff")
        kelly_card(cols[1], "🤝 무승부", adj_d, m_d_odds, capital, "#64748b")
        kelly_card(cols[2], f"🚌 원정 ({m_a_label})", adj_a, m_a_odds, capital, "#ffd700")
    else:
        if st.button("📡 오피셜 월드컵 라이브 배당 동기화", key="wc_api_load"):
            st.session_state["wc_api_games"] = fetch_odds(api_key, "soccer_fifa_world_cup")
        
        wc_games = st.session_state.get("wc_api_games", [])
        if not wc_games:
            st.info("현재 배당판에 등록된 실시간 월드컵 본선 시세가 없습니다.")
        else:
            labels = [f"{g['home_team']} vs {g['away_team']}" for g in wc_games]
            sel = st.selectbox("경기 선택", labels, key="wc_api_sel")
            game = wc_games[labels.index(sel)]
            parsed = parse_game_odds(game)
            if parsed:
                norm = normalize_implied(1/parsed["h"], (1/parsed["d"] if parsed["d"] else 0.0), 1/parsed["a"])
                prob_adj = (w_stat_v * 0.08) + (w_form_v * 0.04) - (w_inj_v * 0.04)
                adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
                adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
                adj_d = 1.0 - adj_h - adj_a
                
                st.divider()
                cols = st.columns(3 if parsed["d"] else 2)
                kelly_card(cols[0], f"🏠 홈 ({game['home_team']})", adj_h, parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", adj_d, parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({game['away_team']})", adj_a, parsed["a"], capital, "#ffd700")

# ------------------------------------------------------------
# [탭 2] ⚽ 국제 A매치 / 친선경기 엔진 (새벽 매치용 로직 복구)
# ------------------------------------------------------------
with tab_amaet_soccer:
    st.markdown("#### ⚽ 국제 A매치 / 친선경기 실시간 배당 분석")
    
    st.markdown("##### 🎛️ 팩트 변수 가중치 조율")
    am_in1, am_in2, am_in3 = st.columns(3)
    with am_in1: am_stat_v = st.number_input("스쿼드 전력 격차 지수 보정치 (-2.0 ~ 2.0)", -2.0, 2.0, 0.0, 0.1, key="am_s_v")
    with am_in2: am_form_v = st.number_input("최신 5경기 흐름 격차 점수 (-1.0 ~ 1.0)", -1.0, 1.0, 0.0, 0.1, key="am_f_v")
    with am_in3: am_inj_v = st.number_input("핵심 라인업 인저리 누수 점수 (-0.5 ~ 0.5)", -0.5, 0.5, 0.0, 0.05, key="am_i_v")

    am_manual = st.toggle("📝 A매치 배당 직접 수동 입력 모드", value=False, key="am_man")
    
    if am_manual:
        st.markdown("##### 배당 수동 주입 연산")
        a_c1, a_c2, a_c3 = st.columns(3)
        with a_c1:
            m_h_odds = st.number_input("홈팀 배당율", min_value=1.01, value=2.00, step=0.01, key="a_h")
            m_h_label = st.text_input("홈팀 구단/국가명", value="프랑스", key="a_hl")
        with a_c2:
            m_d_odds = st.number_input("무승부 배당율", min_value=1.01, value=3.40, step=0.01, key="a_d")
        with a_c3:
            m_a_odds = st.number_input("원정팀 배당율", min_value=1.01, value=3.10, step=0.01, key="a_a")
            m_a_label = st.text_input("원정팀 구단/국가명", value="독일", key="a_al")
            
        norm = normalize_implied(1/m_h_odds, 1/m_d_odds, 1/m_a_odds)
        prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
        adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
        adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
        adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
        
        st.divider()
        st.markdown(f"##### 📐 Kelly 배분 결과 — {m_h_label} vs {m_a_label}")
        cols = st.columns(3)
        kelly_card(cols[0], f"🏠 홈 ({m_h_label})", adj_h, m_h_odds, capital, "#00e5ff")
        kelly_card(cols[1], "🤝 무승부", adj_d, m_d_odds, capital, "#64748b")
        kelly_card(cols[2], f"🚌 원정 ({m_a_label})", adj_a, m_a_odds, capital, "#ffd700")
    else:
        # 💡 [새벽 매치 조준] 시차에 따른 미래/새벽 경기를 통째로 받아와서 연산하는 실시간 분석 로직 개방
        if st.button("📡 실시간 글로벌 A매치 배당 피드 수신", key="am_api_load"):
            st.session_state["am_api_games"] = fetch_odds(api_key, "soccer_international")
            
        am_games = st.session_state.get("am_api_games", [])
        if not am_games:
            st.info("💡 현재 실시간 API 마켓에 대기 중인 친선경기 가격이 없습니다. 새벽 경기가 임박하여 배당이 열리면 피드가 활성화됩니다.")
        else:
            labels = [f"{g['home_team']} vs {g['away_team']}" for g in am_games]
            sel = st.selectbox("분석 타겟 매치 선택", labels, key="am_api_sel")
            game = am_games[labels.index(sel)]
            parsed = parse_game_odds(game)
            if parsed:
                norm = normalize_implied(1/parsed["h"], (1/parsed["d"] if parsed["d"] else 0.0), 1/parsed["a"])
                prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
                adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
                adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
                adj_d = 1.0 - adj_h - adj_a
                
                st.divider()
                cols = st.columns(3 if parsed["d"] else 2)
                kelly_card(cols[0], f"🏠 홈 ({game['home_team']})", adj_h, parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", adj_d, parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({game['away_team']})", adj_a, parsed["a"], capital, "#ffd700")

# ------------------------------------------------------------
# [탭 3] ⚾ KBO 프로야구 전용 엔진 (기존 무결성 로직 보존)
# ------------------------------------------------------------
with tab_kbo_baseball:
    st.markdown("#### ⚾ KBO 프로야구 실시간 배당 분석")

    if st.button("📡 KBO 실시간 시세 배당판 노킹", key="kbo_load"):
        with st.spinner("KBO 라이브 배당판 동기화 중..."):
            st.session_state["kbo_games"] = fetch_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("kbo_games", [])

    if not kbo_games:
        st.info("💡 월요일 브레이크 타임이거나 당일 경기 배당 개장 전 시간대입니다. 가격 고지 시 정상 동기화됩니다.")
    else:
        kbo_labels = [f"{g['home_team']} vs {g['away_team']}" for g in kbo_games]
        sel_kbo_label = st.selectbox("분석할 KBO 경기 선택", kbo_labels, key="kbo_sel")
        sel_kbo = kbo_games[kbo_labels.index(sel_kbo_label)]

        parsed_kbo = parse_game_odds(sel_kbo)
        if not parsed_kbo:
            st.error("선택 경기의 배당 데이터를 파싱할 수 없습니다.")
        else:
            st.divider()
            st.markdown("##### ⚾ 선발 투수 ERA 마진 교정")
            era_c1, era_c2 = st.columns(2)
            with era_c1:
                h_era = st.number_input(f"🏠 {sel_kbo['home_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01, key="h_era")
            with era_c2:
                a_era = st.number_input(f"🚌 {sel_kbo['away_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01, key="a_era")

            norm = normalize_implied(1/parsed_kbo["h"], 0.0, 1/parsed_kbo["a"])

            era_diff = h_era - a_era
            era_adj = max(-0.05, min(0.05, era_diff * -0.01))
            adj_h = max(0.05, min(0.95, norm["h"] + era_adj))
            adj_a = 1.0 - adj_h

            st.divider()
            st.markdown(f"##### 📐 Kelly 배분 결과 — {sel_kbo['home_team']} vs {sel_kbo['away_team']}")
            kbo_cols = st.columns(2)
            kelly_card(kbo_cols[0], f"🏠 홈 ({sel_kbo['home_team']})", adj_h, parsed_kbo["h"], capital, "#00e5ff")
            kelly_card(kbo_cols[1], f"🚌 원정 ({sel_kbo['away_team']})", adj_a, parsed_kbo["a"], capital, "#ffd700")
