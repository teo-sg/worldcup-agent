import os
import math
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Quant Master v3.1 (API-SPORTS)", layout="wide")

BASE = "https://v3.football.api-sports.io"

def get_key():
    k = os.getenv("APISPORTS_KEY")
    if not k and hasattr(st, "secrets"):
        k = st.secrets.get("APISPORTS_KEY", None)
    if not k:
        raise RuntimeError("APISPORTS_KEY가 설정되어 있지 않습니다.")
    return k

def headers():
    return {"x-apisports-key": get_key()}

@st.cache_data(ttl=3600)
def api_get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{BASE}{path}", headers=headers(), params=params, timeout=25)
    j = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {j}")
    if j.get("errors"):
        raise RuntimeError(f"API errors: {j['errors']}")
    return j

# ---------- Lookup ----------
@st.cache_data(ttl=86400)
def team_search(query: str) -> pd.DataFrame:
    j = api_get("/teams", {"search": query})
    rows = []
    for it in j.get("response", []):
        t = it.get("team", {})
        rows.append({
            "team_id": t.get("id"),
            "name": t.get("name"),
            "code": t.get("code"),
            "country": t.get("country"),
            "national": t.get("national"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.dropna(subset=["team_id"]).drop_duplicates(subset=["team_id"])
        df["team_id"] = df["team_id"].astype(int)
    return df

@st.cache_data(ttl=86400)
def league_search(query: str) -> pd.DataFrame:
    # 월드컵은 league 검색으로 찾아서 league_id를 알아내는 용도
    j = api_get("/leagues", {"search": query})
    rows = []
    for it in j.get("response", []):
        league = it.get("league", {})
        country = it.get("country", {})
        seasons = it.get("seasons", [])
        # 가장 최신 시즌만 표시(필요하면 확장)
        last_season = seasons[-1]["year"] if seasons else None
        rows.append({
            "league_id": league.get("id"),
            "league": league.get("name"),
            "type": league.get("type"),
            "country": country.get("name"),
            "last_season_year": last_season,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.dropna(subset=["league_id"]).drop_duplicates(subset=["league_id"])
        df["league_id"] = df["league_id"].astype(int)
    return df

# ---------- Matches ----------
@st.cache_data(ttl=3600)
def recent_fixtures(team_id: int, last_n: int = 10) -> pd.DataFrame:
    j = api_get("/fixtures", {"team": team_id, "last": last_n})
    rows = []
    for it in j.get("response", []):
        fixture = it.get("fixture", {})
        league = it.get("league", {})
        teams = it.get("teams", {})
        goals = it.get("goals", {})
        status = (fixture.get("status") or {}).get("short")

        home = (teams.get("home") or {})
        away = (teams.get("away") or {})
        hg, ag = goals.get("home"), goals.get("away")
        if hg is None or ag is None:
            continue

        rows.append({
            "date": fixture.get("date"),
            "status": status,
            "competition": league.get("name"),
            "season": league.get("season"),
            "round": league.get("round"),
            "home": home.get("name"),
            "away": away.get("name"),
            "home_id": home.get("id"),
            "away_id": away.get("id"),
            "home_goals": int(hg),
            "away_goals": int(ag),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)
        df["home_id"] = df["home_id"].astype(int)
        df["away_id"] = df["away_id"].astype(int)
    return df

@st.cache_data(ttl=3600)
def wc_fixtures(league_id: int, season_year: int) -> pd.DataFrame:
    # 월드컵 같은 대회는 league+season으로 전체 fixtures를 가져온 뒤
    # round/stage로 조별리그만 필터링하는 방식이 현실적입니다.
    j = api_get("/fixtures", {"league": league_id, "season": season_year})
    rows = []
    for it in j.get("response", []):
        fixture = it.get("fixture", {})
        league = it.get("league", {})
        teams = it.get("teams", {})
        goals = it.get("goals", {})
        status = (fixture.get("status") or {}).get("short")
        round_ = league.get("round")

        home = (teams.get("home") or {})
        away = (teams.get("away") or {})
        rows.append({
            "fixture_id": fixture.get("id"),
            "date": fixture.get("date"),
            "status": status,
            "round": round_,
            "home": home.get("name"),
            "away": away.get("name"),
            "home_id": home.get("id"),
            "away_id": away.get("id"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=True)
    return df

# ---------- Features / Model ----------
def summarize_form(team_id: int, team_name: str, df: pd.DataFrame) -> dict | None:
    if df.empty:
        return None
    gf = ga = pts = w = d = l = 0
    n = len(df)
    for _, r in df.iterrows():
        is_home = (int(r["home_id"]) == int(team_id))
        tg = int(r["home_goals"] if is_home else r["away_goals"])
        og = int(r["away_goals"] if is_home else r["home_goals"])
        gf += tg; ga += og
        if tg > og: pts += 3; w += 1
        elif tg == og: pts += 1; d += 1
        else: l += 1
    return {
        "team": team_name,
        "matches": n,
        "W": w, "D": d, "L": l,
        "pts_per_game": pts / n,
        "gf_per_game": gf / n,
        "ga_per_game": ga / n,
        "gd_per_game": (gf - ga) / n,
    }

def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def match_probs_poisson(lam_h: float, lam_a: float, max_goals: int = 8):
    pH = pD = pA = 0.0
    for i in range(max_goals + 1):
        pi = poisson_pmf(i, lam_h)
        for j in range(max_goals + 1):
            p = pi * poisson_pmf(j, lam_a)
            if i > j: pH += p
            elif i == j: pD += p
            else: pA += p
    s = pH + pD + pA
    return pH/s, pD/s, pA/s

def estimate_lambdas(h_form: dict, a_form: dict):
    lam_h = max(0.2, (h_form["gf_per_game"] + a_form["ga_per_game"]) / 2)
    lam_a = max(0.2, (a_form["gf_per_game"] + h_form["ga_per_game"]) / 2)
    return lam_h, lam_a

def implied_probs(h_odds, d_odds, a_odds):
    ph, pd, pa = 1/h_odds, 1/d_odds, 1/a_odds
    s = ph + pd + pa
    return ph/s, pd/s, pa/s

def kelly(p: float, odds: float, cap: float = 0.25):
    b = odds - 1.0
    q = 1.0 - p
    f = (p*b - q) / b
    return max(0.0, min(f, cap))

# ================= UI =================
st.title("⚡ QUANT MASTER v3.1 - API-SPORTS direct key")

with st.sidebar:
    st.header("모델/수집 설정")
    last_n = st.slider("최근 경기 수(N)", 5, 30, 10)
    max_goals = st.slider("Poisson 최대 득점 컷", 6, 12, 8)
    half_kelly = st.checkbox("Half-Kelly", value=True)
    st.divider()
    st.header("월드컵 fixtures(선택)")
    wc_search = st.text_input("리그 검색어(예: World Cup)", "World Cup")
    wc_season = st.number_input("season(year)", value=2022, step=1)

tab1, tab2 = st.tabs(["단일 매치업 예측", "월드컵 Fixtures 조회(필터링용)"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        h_query = st.text_input("홈팀 검색어", "South Korea")
    with c2:
        a_query = st.text_input("원정팀 검색어", "Mexico")

    oc1, oc2, oc3 = st.columns(3)
    with oc1: h_o = st.number_input("홈 배당", value=2.10, min_value=1.01, step=0.01)
    with oc2: d_o = st.number_input("무 배당", value=3.20, min_value=1.01, step=0.01)
    with oc3: a_o = st.number_input("원정 배당", value=3.50, min_value=1.01, step=0.01)

    if st.button("📡 데이터 로드 & 🤖 예측", key="run_single"):
        try:
            h_df = team_search(h_query)
            a_df = team_search(a_query)
        except Exception as e:
            st.error(f"팀 검색 실패: {e}")
            st.stop()

        if h_df.empty or a_df.empty:
            st.error("팀 검색 결과가 비었습니다. 검색어를 바꿔보세요.")
            st.stop()

        lcol, rcol = st.columns(2)
        with lcol:
            st.subheader("홈팀 후보")
            st.dataframe(h_df, use_container_width=True)
            h_pick = st.selectbox("홈팀 team_id 선택", h_df["team_id"].tolist(), index=0, key="h_pick")
            h_name = h_df.loc[h_df["team_id"] == h_pick, "name"].iloc[0]
        with rcol:
            st.subheader("원정팀 후보")
            st.dataframe(a_df, use_container_width=True)
            a_pick = st.selectbox("원정팀 team_id 선택", a_df["team_id"].tolist(), index=0, key="a_pick")
            a_name = a_df.loc[a_df["team_id"] == a_pick, "name"].iloc[0]

        try:
            h_matches = recent_fixtures(int(h_pick), last_n=last_n)
            a_matches = recent_fixtures(int(a_pick), last_n=last_n)
        except Exception as e:
            st.error(f"최근 경기 로드 실패: {e}")
            st.stop()

        if h_matches.empty or a_matches.empty:
            st.warning("최근 경기 데이터가 비어있습니다. Free tier 제한/팀 선택 오류 가능성이 있습니다.")
            st.stop()

        h_form = summarize_form(int(h_pick), h_name, h_matches)
        a_form = summarize_form(int(a_pick), a_name, a_matches)

        lam_h, lam_a = estimate_lambdas(h_form, a_form)
        pH, pD, pA = match_probs_poisson(lam_h, lam_a, max_goals=max_goals)
        mH, mD, mA = implied_probs(h_o, d_o, a_o)

        st.markdown(f"## 📊 {h_name} vs {a_name} (최근 {last_n}경기 기반)")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Model P(Home)", f"{pH:.3f}")
            st.metric("Market P(Home)", f"{mH:.3f}")
        with m2:
            st.metric("Model P(Draw)", f"{pD:.3f}")
            st.metric("Market P(Draw)", f"{mD:.3f}")
        with m3:
            st.metric("Model P(Away)", f"{pA:.3f}")
            st.metric("Market P(Away)", f"{mA:.3f}")

        st.caption(f"λ_home={lam_h:.3f}, λ_away={lam_a:.3f} (최근 득점/실점 기반 단순 추정)")

        fH, fD, fA = kelly(pH, h_o), kelly(pD, d_o), kelly(pA, a_o)
        if half_kelly:
            fH, fD, fA = fH/2, fD/2, fA/2

        st.markdown("### 📈 Kelly 배분(상한 25%)")
        st.write({
            "Home": f"{fH*100:.2f}%",
            "Draw": f"{fD*100:.2f}%",
            "Away": f"{fA*100:.2f}%",
        })

        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"{h_name} 최근 {last_n}경기")
            st.dataframe(h_matches, use_container_width=True)
            st.subheader("홈팀 폼 요약")
            st.json(h_form)
        with c2:
            st.subheader(f"{a_name} 최근 {last_n}경기")
            st.dataframe(a_matches, use_container_width=True)
            st.subheader("원정팀 폼 요약")
            st.json(a_form)

with tab2:
    st.markdown("월드컵/대회 league_id를 찾아서 fixtures를 미리 확인하는 탭입니다.")
    if st.button("🔎 리그 검색", key="run_league_search"):
        try:
            ldf = league_search(wc_search)
        except Exception as e:
            st.error(f"리그 검색 실패: {e}")
            st.stop()

        if ldf.empty:
            st.warning("리그 검색 결과가 없습니다. 검색어를 바꿔보세요.")
            st.stop()

        st.dataframe(ldf, use_container_width=True)
        st.info("원하는 league_id를 확인한 뒤, 아래에서 fixtures를 조회하세요.")

    league_id = st.number_input("조회할 league_id", value=1, step=1)

    if st.button("📅 fixtures 조회", key="run_wc_fixtures"):
        try:
            fdf = wc_fixtures(int(league_id), int(wc_season))
        except Exception as e:
            st.error(f"fixtures 조회 실패: {e}")
            st.stop()

        if fdf.empty:
            st.warning("fixtures가 비어있습니다. league_id/season을 확인하세요.")
            st.stop()

        st.subheader("fixtures (전체)")
        st.dataframe(fdf, use_container_width=True)

        st.markdown("#### 조별리그 필터(간단)")
        st.caption("round 문자열에 'Group'이 들어가면 조별리그로 보는 아주 단순한 필터입니다.")
        group_df = fdf[fdf["round"].fillna("").str.contains("Group", case=False)]
        st.dataframe(group_df, use_container_width=True)
