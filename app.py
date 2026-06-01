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
    total = h_imp + d_imp + a_imp
    if total == 0:
        return {"h": 0.33, "d": 0.34, "a": 0.33}
    return {"h": h_imp / total, "d": d_imp / total, "a": a_imp / total}


def half_kelly(prob: float, odds_decimal: float) -> float:
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
# 헤더
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.0")
st.caption("월드컵 / A매치 + KBO 통합 배당 분석 엔진 · Half-Kelly 자산배분 · 실데이터 전용")
st.divider()

# ============================================================
# 사이드바 — 공통 설정
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ 공통 설정")
    api_key = st.text_input(
        "the-odds-api.com API Key",
        type="password",
        placeholder="your-api-key-here"
    )
    capital = st.number_input(
        "시드머니 (원)",
        min_value=10_000,
        max_value=100_000_000,
        value=1_000_000,
        step=100_000,
        format="%d"
    )

if not api_key:
    st.info("👈 사이드바에서 API 키와 시드머니를 입력하세요.")
    st.stop()

# ============================================================
# 탭
# ============================================================
tab_wc, tab_kbo = st.tabs(["🏆 월드컵 / A매치", "⚾ KBO 프로야구"])

# ============================================================
# 탭 1 — 월드컵 / A매치
# ============================================================
with tab_wc:
    st.markdown("#### 🏆 국제 A매치 / 친선경기 실시간 배당 분석")
    st.warning(
        "⚠️ 2026 FIFA 월드컵 본선 경기 배당은 대회 개막 전후로 자동 수신됩니다. "
        "현재는 발매 중인 국제 A매치 / 친선경기 배당을 타겟팅합니다."
    )

    # 💡 [보완 교정] 피드가 비어있을 때 사용자를 가두지 않고 강제로 입력창을 열 수 있게 기본 설계 보완
    manual_mode = st.toggle("📝 수동 배당 입력 모드 활성화 (피드가 비어있거나 프로토 배당 직접 계산 시)", value=False)

    if manual_mode:
        st.markdown("##### 배당 직접 입력")
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            m_home_odds = st.number_input("홈팀 배당", min_value=1.01, max_value=50.0, value=2.10, step=0.01, key="m_h")
            m_home_label = st.text_input("홈팀 이름", value="홈팀", key="m_hl")
        with mc2:
            m_draw_odds = st.number_input("무승부 배당 (없으면 0)", min_value=0.0, max_value=50.0, value=3.20, step=0.01, key="m_d")
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

    else:
        if st.button("📡 실시간 친선경기 배당 불러오기", key="wc_load"):
            with st.spinner("해외 배당판 동기화 중..."):
                st.session_state["wc_games"] = fetch_odds(api_key, "soccer_international_friendlies")

        games = st.session_state.get("wc_games", [])

        if not games:
            st.info("💡 현재 실시간 API 마켓에 등록된 당일 국제 친선경기 시세가 없습니다. 위의 '📝 수동 배당 입력 모드'를 켜서 프로토 지표를 주입하세요.")
        else:
            game_labels = [f"{g['home_team']} vs {g['away_team']}" for g in games]
            selected_label = st.selectbox("분석할 경기 선택", game_labels, key="wc_sel")
            selected_game = games[game_labels.index(selected_label)]

            parsed = parse_game_odds(selected_game)
            if not parsed:
                st.error("배당 데이터를 파싱할 수 없습니다.")
            else:
                h_i = 1 / parsed["h"]
                a_i = 1 / parsed["a"]
                d_i = (1 / parsed["d"]) if parsed["d"] else 0.0
                norm = normalize_implied(h_i, d_i, a_i)

                st.divider()
                st.markdown(f"##### 📐 Kelly 배분 — {selected_game['home_team']} vs {selected_game['away_team']}")
                cols = st.columns(3 if parsed["d"] else 2)
                kelly_card(cols[0], f"🏠 홈 ({selected_game['home_team']})", norm["h"], parsed["h"], capital, "#00e5ff")
                if parsed["d"]:
                    kelly_card(cols[1], "🤝 무승부", norm["d"], parsed["d"], capital, "#64748b")
                    kelly_card(cols[2], f"🚌 원정 ({selected_game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")
                else:
                    kelly_card(cols[1], f"🚌 원정 ({selected_game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")

# ============================================================
# 탭 2 — KBO
# ============================================================
with tab_kbo:
    st.markdown("#### ⚾ KBO 프로야구 실시간 배당 분석")

    if st.button("📡 KBO 배당 피드 불러오기", key="kbo_load"):
        with st.spinner("KBO 라이브 시세 동기화 중..."):
            st.session_state["kbo_games"] = fetch_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("kbo_games", [])

    if not kbo_games:
        st.info("💡 월요일이거나 경기 개시 전(오전/새벽) 시간대에는 KBO 배당 피드가 비어 있습니다. 배당판이 개장되면 정상 수신됩니다.")
    else:
        kbo_labels = [f"{g['home_team']} vs {g['away_team']}" for g in kbo_games]
        sel_kbo_label = st.selectbox("분석할 경기 선택", kbo_labels, key="kbo_sel")
        sel_kbo = kbo_games[kbo_labels.index(sel_kbo_label)]

        parsed_kbo = parse_game_odds(sel_kbo)
        if not parsed_kbo:
            st.error("배당 데이터를 파싱할 수 없습니다.")
        else:
            st.divider()
            st.markdown("##### ⚾ 선발 ERA 보정 (선택사항)")
            era_c1, era_c2 = st.columns(2)
            with era_c1:
                h_era = st.number_input(f"🏠 {sel_kbo['home_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="h_era")
            with era_c2:
                a_era = st.number_input(f"🚌 {sel_kbo['away_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01, key="a_era")

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
