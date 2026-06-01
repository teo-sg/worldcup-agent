import streamlit as st
import requests

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.0",
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
# 헤더 및 메인 상단 설정 영역 (이동 완료)
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.0")
st.caption("월드컵 / A매치 + KBO 통합 배당 분석 엔진 · Half-Kelly 자산배분 · 실데이터 전용")
st.divider()

# 💡 사이드바에서 메인 화면 최상단 2분할 레이아웃으로 전면 이동
top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input(
        "🔓 the-odds-api.com API Key",
        type="password",
        placeholder="your-api-key-here",
        help="https://the-odds-api.com 에서 무료 발급 (월 500회)"
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

# ============================================================
# 사이드바 (안내문구만 유지)
# ============================================================
with st.sidebar:
    st.markdown("### ⚡ QUANT MASTER v2.0")
    st.markdown("""
    **데이터 파이프라인**  
    - 배당 시세: the-odds-api.com  
    - 임의 조작 데이터 미사용 선언  
    
    **설명**  
    - 본 도구는 계량 데이터 기반 자산 분배 참고용입니다.  
    - 모든 최종 투자 판단의 책임은 사용자 본인에게 있습니다.
    """)

# API 키 필수 예외 처리
if not api_key:
    st.info("👆 화면 상단에서 API 키와 시드머니를 입력하시면 실전 계량 엔진이 가동됩니다.")
    st.stop()

# ============================================================
# 탭 구역
# ============================================================
tab_wc, tab_kbo = st.tabs(["🏆 월드컵 / A매치", "⚾ KBO 프로야구"])

# ============================================================
# 탭 1 — 월드컵 / A매치
# ============================================================
with tab_wc:
    st.markdown("#### 🏆 국제 A매치 / 친선경기 실시간 배당 분석")
    st.warning(
        "⚠️ 2026 FIFA 월드컵 본선 경기 배당은 대회 개막 전후로 자동 수신됩니다. "
        "현재는 발매 중인 국제 A매치 / 친선경기 배당을 분석합니다."
    )

    # 수동 입력 토글
    manual_mode = st.toggle("📝 수동 배당 입력 모드 (프로토 배당 직접 입력)", value=False)

    if manual_mode:
        st.markdown("##### 배당 직접 입력")
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            m_home_odds = st.number_input("홈팀 배당", min_value=1.01, max_value=50.0, value=2.10, step=0.01, key="m_h")
            m_home_label = st.text_input("홈팀 이름", value="홈팀", key="m_hl")
        with mc2:
            m_draw_odds = st.number_input("무승부 배당 (야구는 0 입력)", min_value=0.0, max_value=50.0, value=3.20, step=0.01, key="m_d")
        with mc3:
            m_away_odds = st.number_input("원정팀 배당", min_value=1.01, max_value=50.0, value=3.50, step=0.01, key="m_a")
            m_away_label = st.text_input("원정팀 이름", value="원정팀", key="m_al")

        h_i = 1 / m_home_odds
        a_i = 1 / m_away_odds
        d_i = (1 / m_draw_odds) if m_draw_odds > 1.0 else 0.0
        norm = normalize_implied(h_i, d_i, a_i)

        st.divider()
        st.markdown(f"##### 📐 Kelly 배분 — {m_home_label} vs {m_away_label}")
        cols = st.columns(3 if m_draw_odds > 1.0 else 2)
        kelly_card(cols[0], f"🏠 홈 ({m_home_label})", norm["h"], m_home_odds, capital, "#00e5ff")
        if m_draw_odds > 1.0:
            kelly_card(cols[1], "🤝 무승부", norm["d"], m_draw_odds, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 ({m_away_label})", norm["a"], m_away_odds, capital, "#ffd700")
        else:
            kelly_card(cols[1], f"🚌 원정 ({m_away_label})", norm["a"], m_away_odds, capital, "#ffd700")
        st.caption("※ 마진제거 내재확률 기준 / Half-Kelly 적용")

    else:
        # 실시간 API 모드
        if st.button("📡 배당 피드 불러오기", key="wc_load"):
            with st.spinner("배당 수신 중..."):
                st.session_state["wc_games"] = fetch_odds(api_key, "soccer_international_friendlies")

        games = st.session_state.get("wc_games", [])

        if not games:
            st.info("💡 현재 실시간 API 마켓에 대기 중인 국제 친선경기 시세가 없습니다. '📝 수동 배당 입력 모드'를 활성화하여 프로토 지표를 주입하세요.")
        else:
            # 경기 목록 표시
            game_labels = [f"{g['home_team']} vs {g['away_team']}" for g in games]
            selected_label = st.selectbox("분석할 경기 선택", game_labels, key="wc_sel")
            selected_game = games[game_labels.index(selected_label)]

            parsed = parse_game_odds(selected_game)
            if not parsed:
                st.error("선택 경기의 배당 데이터를 파싱할 수 없습니다.")
            else:
                h_i = 1 / parsed["h"]
                a_i = 1 / parsed["a"]
                d_i = (1 / parsed["d"]) if parsed["d"] else 0.0
                norm = normalize_implied(h_i, d_i, a_i)

                st.divider()
                st.markdown(f"##### 📐 Kelly 배분 — {selected_game['home_team']} vs {selected_game['away_team']}")

                num_cols = 3 if parsed["d"] else 2
                cols = st.columns(num_cols)
                kelly_card(cols[0], f"🏠 홈 ({selected_game['home_team']})", norm["h"], parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", norm["d"], parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({selected_game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")
                else:
                    kelly_card(cols[1], f"🚌 원정 ({selected_game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")

                st.caption("※ 마진제거 내재확률 기준 / Half-Kelly 적용")

# ============================================================
# 탭 2 — KBO
# ============================================================
with tab_kbo:
    st.markdown("#### ⚾ KBO 프로야구 실시간 배당 분석")

    if st.button("📡 KBO 배당 피드 불러오기", key="kbo_load"):
        with st.spinner("KBO 배당 수신 중..."):
            st.session_state["kbo_games"] = fetch_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("kbo_games", [])

    if not kbo_games:
        st.info("💡 비시즌이거나 오늘 자 KBO 배당판 개장 전입니다. 시세 개장 후 피드가 정상 동기화됩니다.")
    else:
        kbo_labels = [f"{g['home_team']} vs {g['away_team']}" for g in kbo_games]
        sel_kbo_label = st.selectbox("분석할 경기 선택", kbo_labels, key="kbo_sel")
        sel_kbo = kbo_games[kbo_labels.index(sel_kbo_label)]

        parsed_kbo = parse_game_odds(sel_kbo)
        if not parsed_kbo:
            st.error("선택 경기의 배당 데이터를 파싱할 수 없습니다.")
        else:
            # ERA 보정 입력
            st.divider()
            st.markdown("##### ⚾ 선발 ERA 보정 (선택사항)")
            st.caption("입력 시 내재확률에서 최대 ±5% 보정. 기본값 유지 시 배당 내재확률 그대로 사용.")
            era_c1, era_c2 = st.columns(2)
            with era_c1:
                h_era = st.number_input(f"🏠 {sel_kbo['home_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="h_era")
            with era_c2:
                a_era = st.number_input(f"🚌 {sel_kbo['away_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="a_era")

            # 배당 내재확률 + ERA 보정
            h_i = 1 / parsed_kbo["h"]
            a_i = 1 / parsed_kbo["a"]
            norm = normalize_implied(h_i, 0.0, a_i)

            era_diff = h_era - a_era
            era_adj = max(-0.05, min(0.05, era_diff * -0.01))
            adj_h = max(0.05, min(0.95, norm["h"] + era_adj))
            adj_a = 1.0 - adj_h

            st.divider()
            st.markdown(f"##### 📐 Kelly 배분 — {sel_kbo['home_team']} vs {sel_kbo['away_team']}")
            kbo_cols = st.columns(2)
            kelly_card(kbo_cols[0], f"🏠 홈 ({sel_kbo['home_team']})", adj_h, parsed_kbo["h"], capital, "#00e5ff")
            kelly_card(kbo_cols[1], f"🚌 원정 ({sel_kbo['away_team']})", adj_a, parsed_kbo["a"], capital, "#ffd700")
            st.caption("※ 배당 내재확률 + ERA 보정 / Half-Kelly 적용")
