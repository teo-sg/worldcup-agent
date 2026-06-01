import streamlit as st
import requests

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.2",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# 스타일
# ============================================================
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
# 유틸 함수
# ============================================================
def fetch_odds(api_key: str, sport_key: str) -> list:
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        f"?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal"
    )
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return res.json()
        # 💡 [상의 해결책 반영] 404 에러 발생 시 앱을 멈추지 않고, 화면에 친절하게 경고문구 공시 후 빈 리스트 반환
        if res.status_code == 404:
            st.warning(f"📡 해당 종목({sport_key})은 현재 API 마켓 비활성화(비개장) 기간입니다. 수동 입력 모드를 활용하세요.")
        else:
            st.error(f"API 오류 {res.status_code}: {res.text[:200]}")
    except Exception as e:
        st.error(f"네트워크 오류: {e}")
    return []


def normalize_implied(h_imp: float, d_imp: float, a_imp: float) -> dict:
    """북마커 마진 제거 후 내재확률 정규화"""
    total = h_imp + d_imp + a_imp
    if total == 0:
        return {"h": 0.33, "d": 0.34, "a": 0.33}
    return {"h": h_imp / total, "d": d_imp / total, "a": a_imp / total}


def half_kelly(prob: float, odds_decimal: float) -> float:
    """Half-Kelly 비율 반환 (0~1)"""
    b = odds_decimal - 1
    if b <= 0:
        return 0.0
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
            <div style="font-size:12px;color:#64748b">내재확률 (마진제거)</div>
            <div style="margin:10px 0;font-size:13px">배당 <strong style="color:{color}">{odds}배</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if k > 0:
            st.success(f"추천 배분 {k*100:.1f}% → **{amount:,}원**")
        else:
            st.error("진입 불가 (EV 마이너스)")


def parse_game_odds(game: dict) -> dict | None:
    """경기 dict에서 홈/무/원정 배당 추출"""
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
# 헤더 및 메인 상단 설정 영역
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.2")
st.caption("월드컵 · A매치 · KBO 개별 분리 엔진 · Half-Kelly 자산배분 · 실데이터 전용")
st.divider()

top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input(
        "🔓 the-odds-api.com API Key",
        type="password",
        placeholder="your-api-key-here",
        help="https://the-odds-api.com 에서 무료 발급"
    )
with top_c2:
    capital = st.number_input(
        "💵 시드머니 (원)",
        min_value=10_000,
        max_value=100_000_000,
        value=1_000_000,
        step=100_000,
        format="%d"
    )

st.divider()

# API 키 입력 대기성 인터셉트
if not api_key:
    st.info("👆 화면 상단에서 API 키와 시드머니를 입력하시면 실전 계량 엔진이 가동됩니다.")
    st.stop()

# ============================================================
# ⚙️ [요청 반영] 3대 마켓 완전 격리 탭 리빌딩
# ============================================================
tab_worldcup, tab_amaet_soccer, tab_kbo_baseball = st.tabs([
    "🏆 1. FIFA 월드컵 본선", 
    "⚽ 2. 국제 A매치 / 친선경기", 
    "⚾ 3. KBO 프로야구"
])

# ------------------------------------------------------------
# [탭 1] 🏆 FIFA 월드컵 본선 전용 엔진
# ------------------------------------------------------------
with tab_worldcup:
    st.markdown("#### 🏆 2026 FIFA 월드컵 본선 실시간 배당 분석")
    st.info("ℹ️ 현재 월드컵 조 편성이 완료되기 전이거나 배당판이 열리지 않은 비시즌기에는 API가 404를 반환하므로, 아래 '수동 배당 입력 모드'를 통해 프로토 대진을 직접 기입해 연산하세요.")
    
    wc_manual = st.toggle("📝 월드컵 배당 직접 수동 입력", value=True, key="wc_man")
    
    if wc_manual:
        st.markdown("##### 월드컵 경기 배당 직접 주입")
        w_c1, w_c2, w_c3 = st.columns(3)
        with w_c1:
            m_h_odds = st.number_input("홈팀 배당", min_value=1.01, value=2.10, step=0.01, key="w_h")
            m_h_label = st.text_input("홈팀 국가명", value="대한민국", key="w_hl")
        with w_c2:
            m_d_odds = st.number_input("무승부 배당", min_value=1.01, value=3.20, step=0.01, key="w_d")
        with w_c3:
            m_a_odds = st.number_input("원정팀 배당", min_value=1.01, value=3.50, step=0.01, key="w_a")
            m_a_label = st.text_input("원정팀 국가명", value="멕시코", key="w_al")
            
        norm = normalize_implied(1/m_h_odds, 1/m_d_odds, 1/m_a_odds)
        st.divider()
        st.markdown(f"##### 📐 Kelly 배분 — [월드컵 프리뷰] {m_h_label} vs {m_a_label}")
        cols = st.columns(3)
        kelly_card(cols[0], f"🏠 홈 ({m_h_label})", norm["h"], m_h_odds, capital, "#00e5ff")
        kelly_card(cols[1], "🤝 무승부", norm["d"], m_d_odds, capital, "#64748b")
        kelly_card(cols[2], f"🚌 원정 ({m_a_label})", norm["a"], m_a_odds, capital, "#ffd700")
    else:
        if st.button("📡 오피셜 월드컵 배당 피드 수신", key="wc_api_load"):
            st.session_state["wc_api_games"] = fetch_odds(api_key, "soccer_fifa_world_cup")
        
        wc_games = st.session_state.get("wc_api_games", [])
        if not wc_games:
            st.info("현재 배당판 API 채널에 정식 고지된 실시간 월드컵 본선 마켓 시세가 없습니다.")
        else:
            labels = [f"{g['home_team']} vs {g['away_team']}" for g in wc_games]
            sel = st.selectbox("경기 선택", labels, key="wc_api_sel")
            game = wc_games[labels.index(sel)]
            parsed = parse_game_odds(game)
            if parsed:
                norm = normalize_implied(1/parsed["h"], (1/parsed["d"] if parsed["d"] else 0.0), 1/parsed["a"])
                st.divider()
                cols = st.columns(3 if parsed["d"] else 2)
                kelly_card(cols[0], f"🏠 홈 ({game['home_team']})", norm["h"], parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", norm["d"], parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")

# ------------------------------------------------------------
# [탭 2] ⚽ 국제 A매치 / 친선경기 전용 엔진
# ------------------------------------------------------------
with tab_amaet_soccer:
    st.markdown("#### ⚽ 국제 A매치 / 친선경기 실시간 배당 분석")
    
    am_manual = st.toggle("📝 A매치 배당 직접 수동 입력", value=False, key="am_man")
    
    if am_manual:
        st.markdown("##### A매치 배당 직접 주입")
        a_c1, a_c2, a_c3 = st.columns(3)
        with a_c1:
            m_h_odds = st.number_input("홈팀 배당", min_value=1.01, value=2.00, step=0.01, key="a_h")
            m_h_label = st.text_input("홈팀 이름", value="프랑스", key="a_hl")
        with a_c2:
            m_d_odds = st.number_input("무승부 배당", min_value=1.01, value=3.40, step=0.01, key="a_d")
        with a_c3:
            m_a_odds = st.number_input("원정팀 배당", min_value=1.01, value=3.10, step=0.01, key="a_a")
            m_a_label = st.text_input("원정팀 이름", value="독일", key="a_al")
            
        norm = normalize_implied(1/m_h_odds, 1/m_d_odds, 1/m_a_odds)
        st.divider()
        st.markdown(f"##### 📐 Kelly 배분 — [A매치] {m_h_label} vs {m_a_label}")
        cols = st.columns(3)
        kelly_card(cols[0], f"🏠 홈 ({m_h_label})", norm["h"], m_h_odds, capital, "#00e5ff")
        kelly_card(cols[1], "🤝 무승부", norm["d"], m_d_odds, capital, "#64748b")
        kelly_card(cols[2], f"🚌 원정 ({m_a_label})", norm["a"], m_a_odds, capital, "#ffd700")
    else:
        if st.button("📡 실시간 A매치 배당 피드 호출", key="am_api_load"):
            st.session_state["am_api_games"] = fetch_odds(api_key, "soccer_international")
            
        am_games = st.session_state.get("am_api_games", [])
        if not am_games:
            st.info("💡 현재 실시간 API 마켓에 등록된 당일 친선 매치업 시세가 없습니다. '📝 수동 배당 입력 모드'를 켜고 토토 책자 수치를 대입하세요.")
        else:
            labels = [f"{g['home_team']} vs {g['away_team']}" for g in am_games]
            sel = st.selectbox("경기 선택", labels, key="am_api_sel")
            game = am_games[labels.index(sel)]
            parsed = parse_game_odds(game)
            if parsed:
                norm = normalize_implied(1/parsed["h"], (1/parsed["d"] if parsed["d"] else 0.0), 1/parsed["a"])
                st.divider()
                cols = st.columns(3 if parsed["d"] else 2)
                kelly_card(cols[0], f"🏠 홈 ({game['home_team']})", norm["h"], parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", norm["d"], parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")

# ------------------------------------------------------------
# [탭 3] ⚾ KBO 프로야구 전용 엔진
# ------------------------------------------------------------
with tab_kbo_baseball:
    st.markdown("#### ⚾ KBO 프로야구 실시간 배당 분석")

    if st.button("📡 KBO 배당 피드 불러오기", key="kbo_load"):
        with st.spinner("KBO 배당 수신 중..."):
            st.session_state["kbo_games"] = fetch_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("kbo_games", [])

    if not kbo_games:
        st.info("💡 비시즌이거나 오늘 자 KBO 배당판 개장 전 시간대입니다. 가격 고지 시 정상 동기화됩니다.")
    else:
        kbo_labels = [f"{g['home_team']} vs {g['away_team']}" for g in kbo_games]
        sel_kbo_label = st.selectbox("분석할 KBO 경기 선택", kbo_labels, key="kbo_sel")
        sel_kbo = kbo_games[kbo_labels.index(sel_kbo_label)]

        parsed_kbo = parse_game_odds(sel_kbo)
        if not parsed_kbo:
            st.error("선택 경기의 배당 데이터를 파싱할 수 없습니다.")
        else:
            st.divider()
            st.markdown("##### ⚾ 선발 ERA 보정 (선택사항)")
            era_c1, era_c2 = st.columns(2)
            with era_c1:
                h_era = st.number_input(f"🏠 {sel_kbo['home_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="h_era")
            with era_c2:
                a_era = st.number_input(f"🚌 {sel_kbo['away_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="a_era")

            norm = normalize_implied(1/parsed_kbo["h"], 0.0, 1/parsed_kbo["a"])

            era_diff = h_era - a_era
            era_adj = max(-0.05, min(0.05, era_diff * -0.01))
            adj_h = max(0.05, min(0.95, norm["h"] + era_adj))
            adj_a = 1.0 - adj_h

            st.divider()
            st.markdown(f"##### 📐 Kelly 배분 — {sel_kbo['home_team']} vs {sel_kbo['away_team']}")
            kbo_cols = st.columns(2)
            kelly_card(kbo_cols[0], f"🏠 홈 ({sel_kbo['home_team']})", adj_h, parsed_kbo["h"], capital, "#00e5ff")
            kelly_card(kbo_cols[1], f"🚌 원정 ({sel_kbo['away_team']})", adj_a, parsed_kbo["a"], capital, "#ffd700")
