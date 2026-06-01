import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="AI 최적화 백테스터", layout="wide")
st.title("🤖 K리그2 AI 가중치 자동 최적화(Optimization) 엔진")
st.markdown("AI가 전술·흐름·부상 가중치를 스스로 조합하여 **최고의 수익률을 내는 최적의 퀀트 룰셋**을 찾아냅니다.")
st.divider()

# 1. 과거 K리그2 20경기 데이터셋 (정답지 확장)
historical_data = [
    {"home": "수원삼성", "away": "부산아이파크", "odds": 2.10, "result": "Home_Win", "h_xg": 1.95, "a_xg": 1.70, "h_inj": 0.02, "a_inj": 0.05, "h_style": "점유율", "a_style": "전방압박"},
    {"home": "전남드래곤즈", "away": "서울이랜드", "odds": 2.45, "result": "Away_Win", "h_xg": 1.85, "a_xg": 2.10, "h_inj": 0.08, "a_inj": 0.00, "h_style": "선수비역습", "a_style": "선수비역습"},
    {"home": "FC안양", "away": "수원삼성", "odds": 1.95, "result": "Draw", "h_xg": 1.50, "a_xg": 1.95, "h_inj": 0.03, "a_inj": 0.02, "h_style": "전방압박", "a_style": "점유율"},
    {"home": "부산아이파크", "away": "전남드래곤즈", "odds": 2.20, "result": "Home_Win", "h_xg": 1.70, "a_xg": 1.85, "h_inj": 0.05, "a_inj": 0.08, "h_style": "전방압박", "a_style": "선수비역습"},
    {"home": "서울이랜드", "away": "FC안양", "odds": 2.60, "result": "Home_Win", "h_xg": 2.10, "a_xg": 1.50, "h_inj": 0.00, "a_inj": 0.03, "h_style": "선수비역습", "a_style": "전방압박"},
    {"home": "수원삼성", "away": "전남드래곤즈", "odds": 1.80, "result": "Home_Win", "h_xg": 1.95, "a_xg": 1.85, "h_inj": 0.02, "a_inj": 0.08, "h_style": "점유율", "a_style": "선수비역습"},
    {"home": "부산아이파크", "away": "서울이랜드", "odds": 2.30, "result": "Draw", "h_xg": 1.70, "a_xg": 2.10, "h_inj": 0.05, "a_inj": 0.00, "h_style": "전방압박", "a_style": "선수비역습"},
    {"home": "FC안양", "away": "전남드래곤즈", "odds": 2.05, "result": "Home_Win", "h_xg": 1.50, "a_xg": 1.85, "h_inj": 0.03, "a_inj": 0.08, "h_style": "전방압박", "a_style": "선수비역습"},
    {"home": "서울이랜드", "away": "수원삼성", "odds": 2.80, "result": "Away_Win", "h_xg": 2.10, "a_xg": 1.95, "h_inj": 0.00, "a_inj": 0.02, "h_style": "선수비역습", "a_style": "점유율"},
    {"home": "전남드래곤즈", "away": "FC안양", "odds": 2.50, "result": "Home_Win", "h_xg": 1.85, "a_xg": 1.50, "h_inj": 0.08, "a_inj": 0.03, "h_style": "선수비역습", "a_style": "전방압박"}
]

init_capital = st.number_input("💰 테스트에 사용할 가상 투자 원금 설정 (원)", value=1000000, step=100000)

if st.button("🤖 AI에게 최적의 가중치 조합 찾기 명령 (그리드 서치)", type="primary"):
    st.info("시뮬레이터가 배후에서 총 125개의 가중치 시나리오를 초고속으로 백테스팅하는 중입니다...")
    
    best_return = -999.0
    best_cfg = {}
    best_history = []
    best_logs = []
    
    # AI가 0.0부터 1.0까지 가중치 조합을 조합하며 브루트포스(그리드서치) 연산을 수행합니다.
    for w_xg in np.linspace(0.1, 0.9, 5):
        for w_tactical in np.linspace(0.05, 0.25, 5):
            for w_injury in np.linspace(0.1, 0.9, 5):
                
                # 가상 자산 가동
                current_capital = init_capital
                capital_history = [init_capital]
                temp_logs = []
                
                for match in historical_data:
                    # 1. 기본 평점 확률
                    prob = 0.48
                    # 2. xG 흐름 가중치 반영
                    prob += (match['h_xg'] - match['a_xg']) * w_xg
                    # 3. 부상자 페널티 반영
                    prob -= (match['h_inj'] - match['a_inj']) * w_injury
                    # 4. 전술 상성 반영
                    if match['h_style'] == "선수비역습" and match['a_style'] == "전방압박":
                        prob += w_tactical
                    elif match['h_style'] == "전방압박" and match['a_style'] == "선수비역습":
                        prob -= w_tactical
                        
                    prob = max(0.05, min(0.95, prob))
                    
                    # 켈리 공식 계산
                    b = match['odds'] - 1
                    f_star = (prob * b - (1 - prob)) / b
                    half_kelly = f_star / 2
                    
                    if half_kelly > 0:
                        bet_money = int(current_capital * half_kelly)
                        if match['result'] == "Home_Win":
                            current_capital += int(bet_money * b)
                            result_str = "🟢 적중"
                        else:
                            current_capital -= bet_money
                            result_str = "🔴 미적중"
                    else:
                        result_str = "⚪ 패스"
                        
                    capital_history.append(current_capital)
                    temp_logs.append({
                        "경기": f"{match['home']} vs {match['away']}",
                        "AI 연산 승률": f"{prob*100:.1f}%",
                        "배당": match['odds'],
                        "결과": match['result'],
                        "행동": result_str,
                        "잔고": f"{current_capital:,}원"
                    })
                    
                # 최종 수익률 계산
                total_return = ((current_capital - init_capital) / init_capital) * 100
                
                # 가장 돈을 많이 버는 최적 조합 갱신 (트레이딩 최적화 모델링)
                if total_return > best_return:
                    best_return = total_return
                    best_cfg = {"xg": w_xg, "tactical": w_tactical, "injury": w_injury}
                    best_history = capital_history
                    best_logs = temp_logs

    # ==========================================
    # [🏆 최적화 결과 대시보드 출력]
    # ==========================================
    st.success("🏁 AI 최적화 완료! 과거 데이터상 가장 돈을 많이 번 마스터 가중치를 도출했습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🥇 AI가 찾아낸 황금 가중치 필드")
        st.markdown(f"* 📈 **최근 경기 흐름(xG) 가중치:** `{best_cfg['xg']:.2f}`")
        st.markdown(f"* ⚽ **전술 상성 보너스 확률:** `{best_cfg['tactical']:.2f}`")
        st.markdown(f"* 🚑 **부상자 발생 패널티 감점 비중:** `{best_cfg['injury']:.2f}`")
    with col2:
        st.subheader("📊 최적 전략 채택 시 계좌 시뮬레이션")
        st.metric("최종 최고 수익률", f"{best_return:+.1f}%")
        st.line_chart(best_history)
        
    st.subheader("📋 최고 수익을 낸 최적 전략의 과거 매치 타임라인")
    st.dataframe(pd.DataFrame(best_logs), use_container_width=True, hide_index=True)
