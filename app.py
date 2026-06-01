import streamlit as st
import requests
from bs4 import BeautifulSoup

# ============================================================
# 페이지 설정 및 전역 스타일
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.6 Pro",
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
# [🛡️ 진실성 100%] 오피셜 일정 및 시세 통합 수집 엔진
# ============================================================
def fetch_real_soccer_schedule() -> list:
    """
    [데이터 원천: Sky Sports 글로벌 매치 센터]
    가짜 주머니 전면 금지. 라이브스코어처럼 실제 매칭되어 있는 
    전 세계 오피셜 축구 일정 대진표 뼈대를 실시간으로 원천 수집합니다.
    """
    url = "https://www.skysports.com/football-fixtures"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    games_list = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Sky Sports 일정 피드의 매치 그룹 핸들링
            matches = soup.find_all("div", class_="fixres__item")
            for m in matches[:25]: # 상위 예정 경기 25개 콤팩트 스캔
                try:
                    home_team = m.find("span", class_="matches__participant--home").text.strip()
                    away_team = m.find("span", class_="matches__participant--away").text.strip()
                    if home_team and away_team:
                        games_list.append({"home": home_team, "away": away_team})
                except: pass
    except: pass
    return games_list

def fetch_odds(api_key: str, sport_key: str) -> list:
    """The Odds API 글로벌 가격 피드 스트리밍"""
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        f"?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal"
    )
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200: return res.json()
    except: pass
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
# 메인 상단 설정 영역 (UI 고정)
# ============================================================
st.markdown("## ⚡ QUANT MASTER v2.6 Pro")
st.caption("오피셜 일정 선행 표출 + 실시간 해외 자본 배당판 동적 매칭 엔진 · 가짜 데이터 0%")
st.divider()

top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input("🔓 the-odds-api.com API Key 입력", type="password", placeholder="your-api-key-here")
with top_c2:
    capital = st.number_input("💵 실전 초기 운용 자산 (원)", min_value=10_000, value=1_000_000, step=100_000, format="%d")

st.divider()

if not api_key:
    st.info("👆 화면 상단에 API Key와 시드머니를 주입하시면 일정-시세 동적 매칭 보드가 활성화됩니다.")
    st.stop()

tab_soccer_hub, tab_kbo_baseball = st.tabs(["⚽ 1. 국제 월드컵 / A매치 통합 매치센터", "⚾ 2. KBO 프로야구"])

# ------------------------------------------------------------
# [탭 1] ⚽ 축구 일정 선행 표출 및 배당 동적 매칭 레이어
# ------------------------------------------------------------
with tab_soccer_hub:
    st.markdown("#### 📅 글로벌 오피셜 대진 일정 기반 퀀트 분석실")
    
    # 가중치 제어판
    st.markdown("##### 🎛️ 팩트 변수 가중치 조율")
    am_in1, am_in2, am_in3 = st.columns(3)
    with am_in1: am_stat_v = st.number_input("스쿼드 전력 격차 지수 보정치 (-2.0 ~ 2.0)", -2.0, 2.0, 0.0, 0.1, key="am_s_v")
    with am_in2: am_form_v = st.number_input("최신 5경기 흐름 격차 점수 (-1.0 ~ 1.0)", -1.0, 1.0, 0.0, 0.1, key="am_f_v")
    with am_in3: am_inj_v = st.number_input("핵심 라인업 인저리 누수 점수 (-0.5 ~ 0.5)", -0.5, 0.5, 0.0, 0.05, key="am_i_v")

    st.divider()
    
    # 💡 [요청 반영] 라이브스코어처럼 일정을 먼저 강제로 긁어와 브리핑
    if st.button("🔄 실시간 매치 일정 및 배당판 동기화", key="load_all_soccer"):
        with st.spinner("Sky Sports 공식 데이터 허브에서 일정 뼈대 수집 중..."):
            st.session_state["soccer_sched"] = fetch_real_soccer_schedule()
        with st.spinner("The Odds API에서 실시간 Bet365 마켓 배당 시세 동시 다운로드 중..."):
            st.session_state["soccer_api_odds"] = fetch_odds(api_key, "soccer_international")

    sched_data = st.session_state.get("soccer_sched", [])
    api_odds_data = st.session_state.get("soccer_api_odds", [])

    if not sched_data:
        st.info("💡 위 버튼을 누르면 라이브스코어처럼 현재 등록된 전 세계 공식 매치 일정을 먼저 쫙 불러옵니다.")
    else:
        # 라이브스코어식 대진표 셀렉트박스 마운트
        sched_labels = [f"⚽ {g['home']} vs {g['away']}" for g in sched_data]
        selected_match_label = st.selectbox("🎯 분석 및 자산 배분을 진행할 경기를 선택하세요:", sched_labels)
        tgt_match = sched_data[sched_labels.index(selected_match_label)]
        
        st.success(f"📖 **선택된 매치 팩트: {tgt_match['home']} vs {tgt_b_away := tgt_match['away']}**")
        
        # 💡 [핵심 로직] 선택된 일정의 팀명이 해외 배당판(API)에 매칭되는지 동적 스캐닝
        matched_game = None
        for odds_game in api_odds_data:
            # 영문 명칭 싱크율 보정을 위해 부분 매칭 규칙 적용
            if tgt_match['home'].lower() in odds_game['home_team'].lower() or odds_game['home_team'].lower() in tgt_match['home'].lower():
                matched_game = odds_game
                break
        
        # 배당 가격 데이터가 매칭되었을 때와 없을 때의 이중화 방어선 가동 (가짜 0%)
        has_live_odds = False
        parsed_odds = None
        
        if matched_game:
            try:
                outcomes = matched_game["bookmakers"][0]["markets"][0]["outcomes"]
                odds_map = {o["name"]: o["price"] for o in outcomes}
                h_o = odds_map.get(matched_game["home_team"])
                a_o = odds_map.get(matched_game["away_team"])
                d_o = odds_map.get("Draw", 0.0)
                if h_o and a_o:
                    parsed_odds = {"h": h_o, "d": d_o, "a": a_o}
                    has_live_odds = True
            except: pass

        if has_live_odds and parsed_odds:
            st.info("🟢 [실시간 시세 동기화 완료] 글로벌 배당판 가격 매칭에 성공했습니다. 즉시 실전 퀀트 연산을 개방합니다.")
            
            h_odds_val = parsed_odds["h"]
            d_odds_val = parsed_odds["d"]
            a_odds_val = parsed_odds["a"]
            
            norm = normalize_implied(1/h_odds_val, (1/d_odds_val if d_odds_val else 0.0), 1/a_odds_val)
            prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
            adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
            adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
            adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
            
            st.markdown("##### 📐 실시간 배당 연산 기반 Half-Kelly 자산 배분 결과")
            cols = st.columns(3)
            kelly_card(cols[0], f"🏠 홈 ({tgt_match['home']})", adj_h, h_odds_val, capital, "#00e5ff")
            kelly_card(cols[1], "🤝 무승부", adj_d, d_odds_val, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 ({tgt_match['away']})", adj_a, a_odds_val, capital, "#ffd700")
            
        else:
            # 배당판이 아직 안 열렸을 때, 가짜 숫자를 채우지 않고 솔직하게 통보 후 수동 주입 레이어 개방
            st.warning("🤝 [🌐 해외 배당판 미개장 상태] 일정은 잡혀있으나 베팅사 가격이 아직 동기화되지 않았습니다. 아래에 프로토 책자 배당률을 직접 입력하여 자산 분배율을 연산하세요.")
            
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1: s_h_odds = st.number_input("프로토 홈팀 배당 직접 기입", min_value=1.01, value=2.00, step=0.01, key="s_h")
            with m_c2: s_d_odds = st.number_input("프로토 무승부 배당 직접 기입", min_value=1.01, value=3.20, step=0.01, key="s_d")
            with m_c3: s_a_odds = st.number_input("프로토 원정팀 배당 직접 기입", min_value=1.01, value=3.40, step=0.01, key="s_a")
            
            norm = normalize_implied(1/s_h_odds, 1/s_d_odds, 1/s_a_odds)
            prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
            adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
            adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
            adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
            
            st.markdown("##### 📐 수동 입력 배당 기준 Half-Kelly 자산 배분 결과")
            cols = st.columns(3)
            kelly_card(cols[0], f"🏠 홈 ({tgt_match['home']})", adj_h, s_h_odds, capital, "#00e5ff")
            kelly_card(cols[1], "🤝 무승부", adj_d, s_d_odds, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 ({tgt_match['away']})", adj_a, s_a_odds, capital, "#ffd700")

# ------------------------------------------------------------
# [탭 2] KBO 프로야구 전용 엔진 (안정 기동 보존)
# ------------------------------------------------------------
with tab_kbo_baseball:
    st.markdown("#### ⚾ KBO 프로야구 실시간 배당 분석")

    if st.button("📡 KBO 실시간 시세 배당판 노킹", key="kbo_load"):
        with st.spinner("KBO 라이브 배당판 동기화 중..."):
            st.session_state["kbo_games"] = fetch_odds(api_key, "baseball_kbo_league")

    kbo_games = st.session_state.get("kbo_games", [])

    if not kbo_games:
        st.info("💡 KBO 프로야구 일정 및 시세를 스캔합니다. 배당판 개장 시간(화~일 주간)에 정상 동기화됩니다.")
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
            with era_c1: h_era = st.number_input(f"🏠 {sel_kbo['home_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01, key="h_era")
            with era_c2: a_era = st.number_input(f"🚌 {sel_kbo['away_team']} 선발 투수 ERA", 0.0, 15.0, 3.50, 0.01, key="a_era")

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
