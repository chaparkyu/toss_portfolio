import streamlit as st
import yfinance as yf
import math

# 1. 웹페이지 기본 설정 (모바일 친화적 세팅)
st.set_page_config(page_title="ETF 20% 리밸런싱 계산기", layout="centered", page_icon="📈")

# 💡 [유지] 제목과 구분선 상하 여백을 줄이는 미니 CSS
st.markdown("""
    <style>
        h1 { padding-bottom: 0rem !important; }
        hr { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
        h3 { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# 2. 포트폴리오 기본 설정 및 디폴트 값
PORTFOLIO_TICKERS = {
    'KODEX 미국S&P500': '379800.KS',
    'KODEX 미국나스닥100': '379810.KS',
    'KODEX 200TR': '278530.KS',
    'KODEX 미국머니마켓액티브': '0048J0.KS', 
    'ACE KRX금현물': '411060.KS'
}
TARGET_WEIGHT = 0.20
DEFAULT_HOLDINGS = [22, 19, 14, 36, 21]

# 3. 화면 UI 및 타이틀
st.title("📈 ETF 20% 리밸런싱 계산기")

# 💡 [수정] 설명글 옆에 이쁜 뱃지 모양으로 제작자 이름(차박유) 추가
st.markdown(
    "스마트폰, 태블릿, PC 어디서든 사용할 수 있는 웹 계산기입니다. "
    "<span style='background-color: #f0f2f6; color: #555; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.85em; font-weight: 600; border: 1px solid #e0e0e0; margin-left: 5px;'>✨ Made by 차박유</span>", 
    unsafe_allow_html=True
)
st.divider()

# 4. 입력 폼 구성
st.subheader("1. 현재 계좌 예수금 입력")
available_cash = st.number_input("사용 가능 예수금 (원)", min_value=0, value=165000, step=1000, format="%d")

st.subheader("2. 현재 보유 수량 입력")
cols = st.columns(2) 
holdings = {}
for i, (name, ticker) in enumerate(PORTFOLIO_TICKERS.items()):
    with cols[i % 2]:
        holdings[name] = st.number_input(f"{name} (주)", min_value=0, value=DEFAULT_HOLDINGS[i], step=1, format="%d")

# 5. 계산 버튼 및 로직
st.write("") 
if st.button("🚀 실시간 주가 연동하여 계산하기", type="primary", use_container_width=True):
    with st.spinner('야후 파이낸스에서 실시간 주가를 가져오는 중입니다... 잠시만 기다려주세요!'):
        current_prices = {}
        current_equities = {}
        total_equity_krw = 0
        error_flag = False
        
        # 주가 데이터 수집
        for name, ticker in PORTFOLIO_TICKERS.items():
            try:
                ticker_obj = yf.Ticker(ticker)
                price = ticker_obj.fast_info['lastPrice']
                if math.isnan(price) or price <= 0:
                    st.error(f"⚠️ {name}의 가격을 불러올 수 없습니다.")
                    error_flag = True
                    break
                current_prices[name] = price
                equity = holdings[name] * price
                current_equities[name] = equity
                total_equity_krw += equity
            except Exception as e:
                st.error(f"⚠️ {name} 주가를 가져오는 중 오류 발생")
                error_flag = True
                break
        
        # 오류 없이 수집 성공 시 결과 출력
        if not error_flag:
            total_asset_krw = total_equity_krw + available_cash
            target_amount = total_asset_krw * TARGET_WEIGHT
            
            st.divider()
            st.subheader("📊 내 계좌 요약")
            col1, col2, col3 = st.columns(3)
            col1.metric("내 보유 주식 평가액", f"{total_equity_krw:,.0f} 원")
            col2.metric("사용 가능 예수금", f"{available_cash:,.0f} 원")
            col3.metric("나의 총자산 합계", f"{total_asset_krw:,.0f} 원")
            
            st.info(f"🎯 **종목당 목표 금액 (20%) : {target_amount:,.0f} 원**")
            
            st.divider()
            st.subheader("💡 매수 가이드 결과")
            
            total_used_cash = 0
            
            for name in PORTFOLIO_TICKERS:
                price = current_prices[name]
                held_shares = holdings[name]
                current_equity = current_equities[name]
                shortfall = target_amount - current_equity
                
                # 각각의 결과를 예쁜 박스(container) 안에 담아서 출력
                with st.container(border=True):
                    # 💡 1번째 줄: 종목명과 현재 상태를 하나로 통합 (검은색 텍스트)
                    st.markdown(f"**[{name}]** &nbsp;|&nbsp; 현재가: {price:,.0f}원 | 보유: {held_shares:,.0f}주 | 평가금: {current_equity:,.0f}원")
                    
                    # 💡 2번째 줄: 매수 가이드 결과 (예쁜 색상 알림창)
                    if shortfall <= 0:
                        st.success("👉 **비중 충족 완료 (추가 매수 없음)**")
                    else:
                        shares_to_buy = math.floor(shortfall / price)
                        actual_cost = shares_to_buy * price
                        total_used_cash += actual_cost
                        st.warning(f"👉 **{shares_to_buy:,.0f}주 추가 매수** (비용: {actual_cost:,.0f}원)")
            
            remaining_cash = available_cash - total_used_cash
            
            st.divider()
            st.subheader("💰 최종 정산")
            col4, col5 = st.columns(2)
            col4.metric("이번 매수 총 소요 금액", f"{total_used_cash:,.0f} 원")
            col5.metric("매수 후 남는 예수금(잔돈)", f"{remaining_cash:,.0f} 원")
