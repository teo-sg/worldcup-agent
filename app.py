import streamlit as st
import requests
import json
import datetime

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(page_title="Quant Master v3.0", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; }
    .metric-box {
        background: #1a2235; border: 1px solid #1e2d45;
        border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 8px;
    }
    .info-box {
        background: #0d1f35; border: 1px solid #1e2d45;
        border-radius: 8px; padding: 14px; margin-bottom: 8px; font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 유틸 함수
# ============================================================
def fetch_odds(api_key, sport_key):
    url = (f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
           f"?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal")
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return res.json()
        st.error(f"API 오류 {res.status_code}: {res.text[:200]}")
    except Exception as e:
        st.error(f"네트워크 오류: {e}")
    return []

def normalize_implied(h, d, a):
    total = h + d + a
    if total == 0:
        return {"h": 0.33, "d": 0.34, "a": 0.33}
    return {"h": h/total, "d": d/total, "a": a/total}

def half_kelly(prob, odds):
    b = odds - 1
    if b <= 0:
        return 0.0
    k = (prob * b - (1 - prob)) / b
    return max(0.0, k / 2)

def kelly_card(col, label, prob, odds, capital, color):
    k = half_kelly(prob, odds)
    amount = int(capital * k)
    with col:
        st.markdown(f"""
        <div class="metric-box" style="border-color:{color}44">
            <div style="font-size:11px;color:#64748b">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{color};margin:6px 0">{prob*100:.1f}%</div>
            <div style="font-size:11px;color:#64748b">내재확률 (마진제거)</div>
            <div style="margin:8px 0;font-size:13px">배당 <strong style="color:{color}">{odds}배</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if k > 0:
            st.success(f"추천 {k*100:.1f}% → **{amount:,}원**")
        else:
            st.error("진입 불가 (EV-)")

def parse_game_odds(game):
    try:
        outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
        om = {o["name"]: o["price"] for o in outcomes}
        h_o = om.get(game["home_team"])
        a_o = om.get(game["away_team"])
        d_o = om.get("Draw")
        if not h_o or not a_o:
            return None
        return {"h": h_o, "a": a_o, "d": d_o}
    except:
        return None

def get_ai_briefing(home, away, sport, anthropic_key):
    """Claude API로 팀 전력 브리핑 생성"""
    prompt = f"""당신은 스포츠 분석 전문가입니다.
다음 경기에 대해 한국어로 간결하게 분석해주세요.

경기: {home} vs {away} ({sport})

아래 항목을 각각 2~3문장으로 작성하세요:
1. 홈팀({home}) 최근 전력 및 강약점
2. 원정팀({away}) 최근 전력 및 강약점  
3. 주요 부상/결장 선수 (알려진 경우)
4. 경기 포인트 및 예상 흐름

없는 정보는 "확인 필요"로 표시하세요."""

    try:
        res = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 800,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=20
        )
        if res.status_code == 200:
            return res.json()["content"][0]["text"]
        return f"브리핑 생성 실패: {res.status_code}"
    except Exception as e:
        return f"브리핑 오류: {e}"

# ============================================================
# 베팅 기록 관리 (session_state 기반)
# ============================================================
if "bet_records" not in st.session_state:
    st.session_state["bet_records"] = []

def add_bet_record(date, match, pick, odds, amount, result):
    """result: '적중' or '낙첨'"""
    profit = int(amount * odds) - amount if result == "적중" else -amount
    st.session_state["bet_records"].append({
        "날짜": date, "경기": match, "선택": pick,
        "배당": odds, "투자금": amount, "결과": result, "손익": profit
    })

# ============================================================
# 헤더
# ============================================================
st.markdown("## ⚡ QUANT MASTER v3.0")
st.caption("월드컵·A매치 + 프로토 승무패 통합 분석 · Half-Kelly · AI 전력브리핑 · 베팅기록 백테스팅")
st.divider()

# ============================================================
# 설정 영역
# ============================================================
with st.container(border=True):
    st.markdown("##### ⚙️ 설정 (API 키 · 시드머니)")
    c1, c2 = st.columns(2)
    with c1:
        api_key = st.text_input("the-odds-api.com API Key", type="password",
                                 placeholder="배당 실시간 수신용")
        anthropic_key = st.text_input("Anthropic API Key (AI 브리핑용, 선택사항)",
                                       type="password", placeholder="sk-ant-...")
    with c2:
        capital = st.number_input("시드머니 (원)", min_value=10_000,
                                   max_value=100_000_000, value=1_000_000,
                                   step=100_000, format="%d")
    st.caption("배당 데이터: the-odds-api.com · AI 브리핑: Anthropic Claude · 참고용 도구")

if not api_key:
    st.info("⬆️ 위 설정창에서 배당 API 키를 입력하세요.")
    st.stop()

# ============================================================
# 탭 구성
# ============================================================
tab_wc, tab_proto, tab_bt = st.tabs([
    "🏆 월드컵 / A매치",
    "🇰🇷 프로토 승무패",
    "📊 베팅기록 & 백테스팅"
])

# ============================================================
# 탭 1 — 월드컵 / A매치
# ============================================================
with tab_wc:
    st.markdown("#### 🏆 국제 A매치 / 친선경기 실시간 배당")
    st.warning("⚠️ 2026 FIFA 월드컵 본선 배당은 대회 개막 후 자동 수신됩니다. 현재는 A매치/친선경기 배당을 분석합니다.")

    WC_SOURCES = [
        ("⚽ 국제 친선경기 (A매치)", "soccer_international_friendlies"),
        ("🏆 FIFA 월드컵", "soccer_fifa_world_cup"),
        ("🇰🇷 K리그1", "soccer_korea_kleague1"),
        ("🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL", "soccer_epl"),
        ("🇪🇸 라리가", "soccer_spain_la_liga"),
        ("🇩🇪 분데스리가", "soccer_germany_bundesliga"),
        ("🇮🇹 세리에A", "soccer_italy_serie_a"),
        ("🇫🇷 리그앙", "soccer_france_ligue_one"),
        ("🇳🇱 에레디비시", "soccer_netherlands_eredivisie"),
        ("🇵🇹 프리메이라리가", "soccer_portugal_primeira_liga"),
        ("🇺🇸 MLS", "soccer_usa_mls"),
    ]
    wc_source_label = st.selectbox("리그 / 대회 선택", [s[0] for s in WC_SOURCES], key="wc_source")
    wc_sport_key = dict(WC_SOURCES)[wc_source_label]

    if st.button("📡 배당 불러오기", key="wc_load"):
        with st.spinner("배당 수신 중..."):
            st.session_state["wc_games"] = fetch_odds(api_key, wc_sport_key)

    games = st.session_state.get("wc_games", [])
    if not games:
        st.info("리그를 선택하고 버튼을 눌러 배당을 불러오세요.")
    else:
        labels = [f"{g['home_team']} vs {g['away_team']}" for g in games]
        sel = st.selectbox("경기 선택", labels, key="wc_sel")
        game = games[labels.index(sel)]
        parsed = parse_game_odds(game)

        if not parsed:
            st.error("배당 데이터 파싱 불가")
        else:
            h_i = 1/parsed["h"]; a_i = 1/parsed["a"]
            d_i = (1/parsed["d"]) if parsed["d"] else 0.0
            norm = normalize_implied(h_i, d_i, a_i)

            st.divider()
            st.markdown(f"##### 📐 Kelly 배분 — {game['home_team']} vs {game['away_team']}")
            num_cols = 3 if parsed["d"] else 2
            cols = st.columns(num_cols)
            kelly_card(cols[0], f"🏠 홈 ({game['home_team']})", norm["h"], parsed["h"], capital, "#00e5ff")
            if parsed["d"]:
                kelly_card(cols[1], "🤝 무승부", norm["d"], parsed["d"], capital, "#64748b")
                kelly_card(cols[2], f"🚌 원정 ({game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")
            else:
                kelly_card(cols[1], f"🚌 원정 ({game['away_team']})", norm["a"], parsed["a"], capital, "#ffd700")
            st.caption("※ 마진제거 내재확률 / Half-Kelly")

            # AI 브리핑
            st.divider()
            st.markdown("##### 🤖 AI 팀 전력 브리핑")
            if not anthropic_key:
                st.info("설정창에 Anthropic API Key를 입력하면 AI 브리핑이 활성화됩니다.")
            else:
                if st.button("AI 브리핑 생성", key="wc_brief"):
                    with st.spinner("AI 분석 중..."):
                        brief = get_ai_briefing(game["home_team"], game["away_team"], "축구 A매치", anthropic_key)
                        st.session_state["wc_brief_text"] = brief
                if "wc_brief_text" in st.session_state:
                    st.markdown(f"""<div class="info-box">{st.session_state['wc_brief_text'].replace(chr(10), '<br>')}</div>""",
                                unsafe_allow_html=True)

# ============================================================
# 탭 2 — 프로토 승무패
# ============================================================
with tab_proto:
    st.markdown("#### 🇰🇷 프로토 승무패 분석")
    st.info("프로토 배당은 베트맨(betman.co.kr)에서 확인 후 직접 입력하세요. 경기 목록은 the-odds-api에서 자동 수신합니다.")

    proto_sport = st.selectbox("종목 선택", [
        "⚽ K리그 (soccer_korea_kleague1)",
        "⚽ 해외축구 - EPL (soccer_epl)",
        "⚽ 해외축구 - 라리가 (soccer_spain_la_liga)",
        "⚽ 해외축구 - 분데스리가 (soccer_germany_bundesliga)",
        "⚽ 해외축구 - 세리에A (soccer_italy_serie_a)",
        "⚽ 해외축구 - 리그앙 (soccer_france_ligue_one)",
        "⚽ FIFA 월드컵 (soccer_fifa_world_cup)",
        "⚾ KBO 야구 (baseball_kbo)",
        "직접입력 (경기명 수동)"
    ], key="proto_sport")

    sport_key_map = {
        "⚽ K리그 (soccer_korea_kleague1)": "soccer_korea_kleague1",
        "⚽ 해외축구 - EPL (soccer_epl)": "soccer_epl",
        "⚽ 해외축구 - 라리가 (soccer_spain_la_liga)": "soccer_spain_la_liga",
        "⚽ 해외축구 - 분데스리가 (soccer_germany_bundesliga)": "soccer_germany_bundesliga",
        "⚽ 해외축구 - 세리에A (soccer_italy_serie_a)": "soccer_italy_serie_a",
        "⚽ 해외축구 - 리그앙 (soccer_france_ligue_one)": "soccer_france_ligue_one",
        "⚽ FIFA 월드컵 (soccer_fifa_world_cup)": "soccer_fifa_world_cup",
        "⚾ KBO 야구 (baseball_kbo)": "baseball_kbo",
    }

    is_manual = proto_sport == "직접입력 (경기명 수동)"

    if not is_manual:
        skey = sport_key_map[proto_sport]
        if st.button("📡 경기 목록 불러오기", key="proto_load"):
            with st.spinner("경기 목록 수신 중..."):
                st.session_state["proto_games"] = fetch_odds(api_key, skey)

        proto_games = st.session_state.get("proto_games", [])
        if not proto_games:
            st.info("버튼을 눌러 경기 목록을 불러오세요.")
            home_name, away_name = "홈팀", "원정팀"
        else:
            plabels = [f"{g['home_team']} vs {g['away_team']}" for g in proto_games]
            psel = st.selectbox("경기 선택", plabels, key="proto_sel")
            pgame = proto_games[plabels.index(psel)]
            home_name = pgame["home_team"]
            away_name = pgame["away_team"]
            st.success(f"✅ 선택됨: {home_name} vs {away_name}")
    else:
        mc1, mc2 = st.columns(2)
        with mc1: home_name = st.text_input("홈팀 이름", value="홈팀", key="p_hn")
        with mc2: away_name = st.text_input("원정팀 이름", value="원정팀", key="p_an")

    st.divider()

    # 배당 입력 (항상 수동)
    st.markdown("##### 💰 프로토 배당 입력 (베트맨에서 확인 후 입력)")
    is_baseball = "야구" in proto_sport or "baseball" in proto_sport
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        p_home_odds = st.number_input(f"🏠 {home_name} 배당", 1.01, 50.0, 2.10, 0.01, key="p_ho")
    with bc2:
        if not is_baseball:
            p_draw_odds = st.number_input("🤝 무승부 배당", 0.0, 50.0, 3.20, 0.01, key="p_do")
        else:
            p_draw_odds = 0.0
            st.info("야구는 무승부 없음")
    with bc3:
        p_away_odds = st.number_input(f"🚌 {away_name} 배당", 1.01, 50.0, 3.50, 0.01, key="p_ao")

    # Kelly 계산
    p_h_i = 1/p_home_odds; p_a_i = 1/p_away_odds
    p_d_i = (1/p_draw_odds) if p_draw_odds > 1.0 else 0.0
    p_norm = normalize_implied(p_h_i, p_d_i, p_a_i)

    st.divider()
    st.markdown(f"##### 📐 Kelly 배분 — {home_name} vs {away_name}")
    p_num_cols = 3 if p_draw_odds > 1.0 else 2
    p_cols = st.columns(p_num_cols)
    kelly_card(p_cols[0], f"🏠 홈 ({home_name})", p_norm["h"], p_home_odds, capital, "#00e5ff")
    if p_draw_odds > 1.0:
        kelly_card(p_cols[1], "🤝 무승부", p_norm["d"], p_draw_odds, capital, "#64748b")
        kelly_card(p_cols[2], f"🚌 원정 ({away_name})", p_norm["a"], p_away_odds, capital, "#ffd700")
    else:
        kelly_card(p_cols[1], f"🚌 원정 ({away_name})", p_norm["a"], p_away_odds, capital, "#ffd700")

    # Kelly 구성 내역 상세
    st.divider()
    st.markdown("##### 🔍 Kelly 계산 구성 내역")
    kd1, kd2, kd3 = st.columns(3)
    for col, label, prob, odds in [
        (kd1, f"홈({home_name})", p_norm["h"], p_home_odds),
        (kd2, "무승부" if p_draw_odds > 1.0 else None, p_norm["d"] if p_draw_odds > 1.0 else None, p_draw_odds),
        (kd3, f"원정({away_name})", p_norm["a"], p_away_odds),
    ]:
        if label is None:
            continue
        k = half_kelly(prob, odds)
        b = odds - 1
        with col:
            st.markdown(f"""
            <div class="info-box">
            <b>{label}</b><br>
            마진제거 확률: {prob*100:.1f}%<br>
            배당: {odds}배 (b={b:.2f})<br>
            Kelly: {k*100:.2f}% → Half: {k*50:.2f}%<br>
            투자금: {int(capital*k):,}원
            </div>
            """, unsafe_allow_html=True)

    # AI 브리핑
    st.divider()
    st.markdown("##### 🤖 AI 팀 전력 / 부상자 브리핑")
    if not anthropic_key:
        st.info("설정창에 Anthropic API Key를 입력하면 AI 브리핑이 활성화됩니다.")
    else:
        if st.button("AI 브리핑 생성", key="proto_brief"):
            with st.spinner("AI 분석 중..."):
                sport_label = "축구" if not is_baseball else "야구"
                brief = get_ai_briefing(home_name, away_name, sport_label, anthropic_key)
                st.session_state["proto_brief_text"] = brief
        if "proto_brief_text" in st.session_state:
            st.markdown(f"""<div class="info-box">{st.session_state['proto_brief_text'].replace(chr(10), '<br>')}</div>""",
                        unsafe_allow_html=True)

    # 베팅 기록 저장
    st.divider()
    st.markdown("##### 💾 이 경기 베팅 결과 기록")
    st.caption("경기 종료 후 결과를 입력하면 백테스팅 탭에 자동 반영됩니다.")
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: rec_date = st.date_input("날짜", datetime.date.today(), key="rec_date")
    with r2:
        pick_options = [f"홈({home_name})", "무승부", f"원정({away_name})"] if p_draw_odds > 1.0 else [f"홈({home_name})", f"원정({away_name})"]
        rec_pick = st.selectbox("선택", pick_options, key="rec_pick")
    with r3:
        pick_odds = p_home_odds if "홈" in rec_pick else (p_draw_odds if "무승부" in rec_pick else p_away_odds)
        rec_amount = st.number_input("투자금(원)", 1000, 10_000_000, 10000, 1000, key="rec_amt")
    with r4: rec_result = st.selectbox("결과", ["적중", "낙첨"], key="rec_res")
    with r5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("기록 저장", key="rec_save"):
            add_bet_record(str(rec_date), f"{home_name} vs {away_name}",
                           rec_pick, pick_odds, rec_amount, rec_result)
            st.success("✅ 기록 저장 완료!")

# ============================================================
# 탭 3 — 베팅기록 & 백테스팅
# ============================================================
with tab_bt:
    st.markdown("#### 📊 베팅 기록 & 수익률 백테스팅")

    records = st.session_state["bet_records"]

    if not records:
        st.info("프로토 탭에서 베팅 결과를 기록하면 여기서 수익률 분석이 자동으로 표시됩니다.")
    else:
        # 요약 지표
        total_bets = len(records)
        wins = sum(1 for r in records if r["결과"] == "적중")
        total_invest = sum(r["투자금"] for r in records)
        total_profit = sum(r["손익"] for r in records)
        win_rate = wins / total_bets * 100
        roi = total_profit / total_invest * 100

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("총 베팅 수", f"{total_bets}건")
        s2.metric("적중률", f"{win_rate:.1f}%")
        s3.metric("총 손익", f"{total_profit:+,}원")
        s4.metric("ROI", f"{roi:+.1f}%")

        st.divider()

        # 누적 손익 차트
        st.markdown("##### 📈 누적 손익 곡선")
        cumulative = []
        running = 0
        for r in records:
            running += r["손익"]
            cumulative.append(running)

        import pandas as pd
        chart_df = pd.DataFrame({
            "베팅 회차": list(range(1, len(cumulative)+1)),
            "누적 손익 (원)": cumulative
        })
        st.line_chart(chart_df.set_index("베팅 회차"))

        st.divider()

        # 상세 기록 테이블
        st.markdown("##### 📋 베팅 상세 기록")
        df = pd.DataFrame(records)
        df["손익"] = df["손익"].apply(lambda x: f"{x:+,}원")
        df["투자금"] = df["투자금"].apply(lambda x: f"{x:,}원")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 기록 초기화
        st.divider()
        if st.button("🗑️ 전체 기록 초기화", type="secondary"):
            st.session_state["bet_records"] = []
            st.rerun()

        # CSV 다운로드
        csv = pd.DataFrame(records).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 CSV 다운로드", csv, "betting_records.csv", "text/csv")

st.divider()
st.caption("⚡ QUANT MASTER v3.0 · 참고용 도구 · 투자 손실 책임은 사용자 본인에게 있습니다")
