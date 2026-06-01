import streamlit as st
import requests

# ============================================================
# 페이지 설정 및 전역 스타일
# ============================================================
st.set_page_config(
    page_title="Quant Master v2.9 DebugPro",
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
# [🛡️ 진실성 100%] 정밀 진단형 파이프라인 엔진
# ============================================================
def fetch_all_upcoming_odds(api_key: str, sport_key: str, selected_regions: str) -> list:
    """
    [지적사항 반영 2번] regions=eu의 제한을 풀고 us,uk,eu,au 멀티 리전 통합 개방 확장
    [지적사항 반영 내부 원인 추적] status_code와 원천 텍스트 응답을 화면에 정직하게 고지
    """
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        f"?apiKey={api_key}&regions={selected_regions}&markets=h2h&oddsFormat=decimal"
    )
    try:
        res = requests.get(url, timeout=8)
        
        # 하단 디버깅 섹션을 위해 세션 상태에 실시간 상태 기록
        st.session_state["last_status"] = res.status_code
        st.session_state["last_response_text"] = res.text[:1000]
        
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"📡 네트워크 동기화 치명적 실패: {e}")
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
st.markdown("## ⚡ QUANT MASTER v2.9 DebugPro")
st.caption("지적해 주신 6대 API 오류 원인 역추적 마운트 · 실시간 규격 검증 · 임의 데이터 0%")
st.divider()

top_c1, top_c2 = st.columns([2, 1])
with top_c1:
    api_key = st.text_input("🔓 the-odds-api.com API Key 입력", type="password", placeholder="your-api-key-here")
with top_c2:
    capital = st.number_input("💵 실전 초기 운용 자산 (원)", min_value=10_000, value=1_000_000, step=100_000, format="%d")

# [지적사항 반영 2번] 리전을 사용자가 유연하게 확장 선택할 수 있도록 전면에 격리 배치
regions_input = st.text_input("🌐 수신 대상 북메이커 리전 설정 (CORS 및 누락 방지)", value="eu,uk,us,au")

st.divider()

if not api_key:
    st.info("👆 화면 상단에 발급받으신 API Key를 입력하시면 정밀 자산 통제판이 개방됩니다.")
    st.stop()

# ============================================================
# [🕵️ 핵심 추가: 지적사항 1번, 6번 반영] 
# 내 API Key로 현재 호출 가능한 진짜 정식 스포츠 Key 목록 실시간 추적기
# ============================================================
st.subheader("🔍 1. 내 API Key 기반 실시간 가용 스포츠 종목 Key 전수 조사")
st.caption("The Odds API 공식 서버가 현재 허용하는 정식 명칭을 1초 만에 긁어와 대조합니다. 가짜 유령 키를 완전히 예방합니다.")

if st.button("📡 가용 공식 Sport Key 목록 전수 조회"):
    with st.spinner("API 서버에서 활성화된 종목 캘린더 추출 중..."):
        all_sports_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
        try:
            sport_res = requests.get(all_sports_url, timeout=6)
            if sport_res.status_code == 200:
                st.success("🟢 공식 종목 피드 수신 성공 - 하단 명단에서 정확한 'key' 명칭을 복사하여 사용하세요.")
                sports_df = pd.DataFrame(sport_res.json())
                if not sports_df.empty:
                    st.dataframe(sports_df[["key", "group", "title", "active"]], use_container_width=True, hide_index=True)
                else:
                    st.write(sport_res.json())
            else:
                st.error(f"종목 조회 실패 (오류 코드: {sport_res.status_code}): {sport_res.text}")
        except Exception as sport_e:
            st.error(f"네트워크 장애: {sport_e}")

st.divider()

# ============================================================
# 메인 계량 분석 탭 구역
# ============================================================
st.subheader("📊 2. 팩트 데이터 실전 퀀트 매칭 및 Kelly 계산기")
tab_soccer, tab_kbo = st.tabs(["⚽ 국제 축구 분석 룸", "⚾ 국내 KBO 야구 분석 룸"])

# ------------------------------------------------------------
# [탭 1] ⚽ 축구 분석 마스터
# ------------------------------------------------------------
with tab_soccer:
    # [지적사항 1번 대책] 사용자가 위 실시간 표를 보고 정확한 공식 키를 타이핑하여 진입할 수 있도록 입력창 개방
    soccer_key_input = st.text_input("⚽ 축구 대상 마켓 Key 입력 (기본 글로벌 축구 규격)", value="soccer_international")
    
    st.markdown("##### 🎛️ 전술 변수 가중치 조율")
    am_c1, am_c2, am_c3 = st.columns(3)
    with am_c1: am_stat_v = st.number_input("스쿼드 전력 격차 지수 보정치 (-2.0 ~ 2.0)", -2.0, 2.0, 0.0, 0.1, key="s_s")
    with am_c2: am_form_v = st.number_input("최신 5경기 흐름 격차 점수 (-1.0 ~ 1.0)", -1.0, 1.0, 0.0, 0.1, key="s_f")
    with am_c3: am_inj_v = st.number_input("핵심 라인업 인저리 누수 점수 (-0.5 ~ 0.5)", -0.5, 0.5, 0.0, 0.05, key="s_i")

    st.divider()

    if st.button("🔄 설정된 축구 마켓 피드 수신 가동", key="btn_soccer"):
        with st.spinner("해외 자본망 탐색 중..."):
            st.session_state["soc_data"] = fetch_all_upcoming_odds(api_key, soccer_key_input, regions_input)

    soccer_games = st.session_state.get("soc_data", [])

    # [지적사항 5번 반영] 데이터 수집 직후 화면에 실시간 JSON 상태 및 경기 수 투명하게 고지
    if "last_status" in st.session_state:
        st.info(f"📡 API 응답 코드: {st.session_state['last_status']} | 탐지된 총 경기 수: {len(soccer_games)}개")
        with st.expander("🔍 [디버깅] API 원천 텍스트 응답(Response) 데이터 확인"):
            st.code(st.session_state["last_response_text"])

    if not soccer_games:
        st.info("💡 위 버튼을 누르면 설정된 Key와 리전 기준 발매 경기를 긁어옵니다. 데이터가 비어있다면 수동 모드 또는 Sport Key 목록을 대조하세요.")
    else:
        soccer_labels = []
        for g in soccer_games:
            g_time = g.get('commence_time', '시간미정').replace('T', ' ').replace('Z', '')
            soccer_labels.append(f"⚽ [{g_time}] {g.get('home_team')} vs {g.get('away_team')}")

        selected_soccer = st.selectbox("분석 경기를 선택하세요:", soccer_labels, key="sb_soc")
        tgt_soccer_game = soccer_games[soccer_labels.index(selected_soccer)]

        # [지적사항 3번 반영] IndexError 완벽 차단막 가동 - bookmakers 리스트 비어있을 시 수동 모드로 자동 패스 안내
        bookmakers = tgt_soccer_game.get("bookmakers", [])
        
        if len(bookmakers) == 0:
            st.warning("⚠️ [배당 데이터 공백] 라이브스코어상 일정은 등록되었으나 베팅사 가격 마켓이 비어 있습니다. 하단 수동 모드로 정산하세요.")
            has_soccer_odds = False
        else:
            try:
                outcomes = bookmakers[0]["markets"][0]["outcomes"]
                odds_map = {o["name"]: o["price"] for o in outcomes}
                h_o = odds_map.get(tgt_soccer_game["home_team"])
                a_o = odds_map.get(tgt_soccer_game["away_team"])
                d_o = odds_map.get("Draw", 0.0)
                has_soccer_odds = True if (h_o and a_o) else False
            except:
                has_soccer_odds = False

        if has_soccer_odds:
            st.success("🟢 [실시간 시세 매칭 성공] 오피셜 자본 가격 기반 Half-Kelly 배분을 시작합니다.")
            norm = normalize_implied(1/h_o, (1/d_o if d_o else 0.0), 1/a_o)
            prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
            adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
            adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
            adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
            
            cols = st.columns(3)
            kelly_card(cols[0], f"🏠 홈 ({tgt_soccer_game['home_team']})", adj_h, h_o, capital, "#00e5ff")
            kelly_card(cols[1], "🤝 무승부", adj_d, d_o, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 ({tgt_soccer_game['away_team']})", adj_a, a_o, capital, "#ffd700")
        else:
            st.warning("🤝 배당 데이터 마진 분석 대기중. 하단에 토토 프로토 배당률을 직접 입력하여 안전 자산액을 정산하세요.")
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1: s_h_odds = st.number_input("프로토 홈 배당 기입", min_value=1.01, value=2.00, step=0.01, key="sh_1")
            with m_c2: s_d_odds = st.number_input("프로토 무승부 배당 기입", min_value=1.01, value=3.20, step=0.01, key="sd_1")
            with m_c3: s_a_odds = st.number_input("프로토 원정 배당 기입", min_value=1.01, value=3.40, step=0.01, key="sa_1")
            
            norm = normalize_implied(1/s_h_odds, 1/s_d_odds, 1/s_a_odds)
            prob_adj = (am_stat_v * 0.08) + (am_form_v * 0.04) - (am_inj_v * 0.04)
            adj_h = max(0.05, min(0.90, norm["h"] + prob_adj))
            adj_a = max(0.05, min(0.90, norm["a"] - prob_adj))
            adj_d = max(0.05, min(0.90, 1.0 - adj_h - adj_a))
            
            cols = st.columns(3)
            kelly_card(cols[0], f"🏠 홈 수동", adj_h, s_h_odds, capital, "#00e5ff")
            kelly_card(cols[1], "🤝 무승부 수동", adj_d, s_d_odds, capital, "#64748b")
            kelly_card(cols[2], f"🚌 원정 수동", adj_a, s_a_odds, capital, "#ffd700")

# ------------------------------------------------------------
# [탭 2] ⚾ KBO 야구 분석 마스터
# ------------------------------------------------------------
with tab_kbo:
    # [지적사항 1번 대책] 야구도 가용 Sport Key 명단을 보고 정확히 매칭할 수 있게 입력창 전면 개방
    baseball_key_input = st.text_input("⚾ 야구 대상 마켓 Key 입력 (KBO 정식 규격 매칭용)", value="baseball_kbo_league")
    
    if st.button("🔄 설정된 야구 마켓 피드 수신 가동", key="btn_kbo"):
        with st.spinner("야구 시세 동기화 중..."):
            st.session_state["kbo_data"] = fetch_all_upcoming_odds(api_key, baseball_key_input, regions_input)

    kbo_games = st.session_state.get("kbo_data", [])

    if not kbo_games:
        st.info("💡 비시즌이거나 오늘 자 야구 배당판 개장 전 시간대입니다. 가용 Sport Key 목록을 조회하여 시즌 키 명칭을 대조해 보세요.")
    else:
        kbo_labels = []
        for g in kbo_games:
            g_time = g.get('commence_time', '시간미정').replace('T', ' ').replace('Z', '')
            kbo_labels.append(f"⚾ [{g_time}] {g.get('home_team')} vs {g.get('away_team')}")

        selected_kbo = st.selectbox("분석할 KBO 경기 선택:", kbo_labels, key="sb_kbo")
        tgt_kbo_game = kbo_games[kbo_labels.index(selected_kbo)]

        # [지적사항 3번 반영] 야구 배당판 bookmakers 리스트 공백 방어선 가동
        kbo_bookmakers = tgt_kbo_game.get("bookmakers", [])
        
        if len(kbo_bookmakers) == 0:
            st.error("❌ 선택 경기의 실시간 북메이커 데이터가 비어 있습니다. 배당판 등재 대기 상태입니다.")
        else:
            try:
                outcomes = kbo_bookmakers[0]["markets"][0]["outcomes"]
                odds_map = {o["name"]: o["price"] for o in outcomes}
                h_o = odds_map.get(tgt_kbo_game["home_team"])
                a_o = odds_map.get(tgt_kbo_game["away_team"])
                
                if h_o and a_o:
                    st.divider()
                    st.markdown("##### ⚾ 선발 투수 ERA 마진 교정")
                    era_c1, era_c2 = st.columns(2)
                    with era_c1: h_era = st.number_input(f"🏠 {tgt_kbo_game['home_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01)
                    with era_c2: a_era = st.number_input(f"🚌 {tgt_kbo_game['away_team']} 선발 ERA", 0.0, 15.0, 3.50, 0.01)

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
            except Exception as e:
                st.error(f"데이터 파싱 오류: {e}")
