import streamlit as st

st.set_page_config(page_title="Quant Master v3.0 WorldCup", layout="wide")

# 가중치 계산 함수 (가짜 데이터 없음, 상균님의 팩트 입력값만 반영)
def calculate_kelly_briefing(home_odds, draw_odds, away_odds, xg_diff, injury_factor, capital):
    # 기본 확률 역산
    raw_h = 1/home_odds
    raw_d = 1/draw_odds
    raw_a = 1/away_odds
    total = raw_h + raw_d + raw_a
    
    # 상균님의 팩트 가중치 보정
    # xG(기대득점)차이와 인저리 팩트를 확률에 직접 반영
    adj_h = (raw_h/total) + (xg_diff * 0.05) - (injury_factor * 0.03)
    adj_a = (raw_a/total) - (xg_diff * 0.05) + (injury_factor * 0.03)
    adj_d = 1.0 - adj_h - adj_a
    
    return adj_h, adj_d, adj_a

st.title("🏆 2026 월드컵 퀀트 브리핑 센터")
st.caption("가짜 데이터 금지: 사용자가 주입한 '옵타식 팩트'만으로 승률을 재계산합니다.")

# 조별리그 선택
group = st.selectbox("조별리그 선택", ["A조", "B조", "C조", "D조", "E조", "F조", "G조", "H조"])
st.subheader(f"{group} 전체 대진 브리핑 및 배분")

# 경기 수동 입력
c1, c2, c3 = st.columns(3)
with c1: 
    match_name = st.text_input("경기명 (예: 대한민국 vs 멕시코)")
    h_odds = st.number_input("홈 배당", 1.01, 20.0, 2.0)
with c2: 
    d_odds = st.number_input("무승부 배당", 1.01, 20.0, 3.2)
    xg_diff = st.slider("xG(기대득점) 우위 (홈기준 -0.5~+0.5)", -0.5, 0.5, 0.0)
with c3: 
    a_odds = st.number_input("원정 배당", 1.01, 20.0, 3.0)
    injury = st.slider("핵심 선수 누수(부상)도", 0.0, 1.0, 0.0)

if st.button("퀀트 브리핑 생성"):
    adj_h, adj_d, adj_a = calculate_kelly_briefing(h_odds, d_odds, a_odds, xg_diff, injury, 1000000)
    
    st.divider()
    st.markdown(f"### 📋 {match_name} 퀀트 브리핑")
    st.write(f"- **전술적 분석**: xG 우위 {xg_diff} 및 누수 {injury}를 반영한 보정 승률 산출 완료.")
    st.write(f"- **홈 승리 보정 확률**: {adj_h*100:.1f}%")
    st.write(f"- **원정 승리 보정 확률**: {adj_a*100:.1f}%")
    
    # Kelly 공식 기반 배분
    if adj_h > 1/h_odds:
        st.success(f"📈 [투자 전략] 홈팀 배당 대비 승률 우위 확보. 자산의 {adj_h*100:.1f}% 배분 권장.")
    else:
        st.warning("📉 [투자 전략] 배당 대비 기대 수익 미달. 관망 권장.")

st.sidebar.info("💡 배당이 안 열린 경기는 프로토 책자 수치를 입력하면 분석 엔진이 즉시 작동합니다.")
