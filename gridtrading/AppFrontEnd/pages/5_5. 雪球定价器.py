import streamlit as st
from gridtrading.Pricing.quantlib_pricing import snowball_pricing_mcm_mp, calculate_coupon_snowball
import datetime
import time
import pandas as pd

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    st.set_page_config(page_title="雪球定价器", page_icon="💻", layout="wide")
    st.title("雪球定价器")
    st.write("----------------------------------------------------------------------")

    col1, col2, col3 = st.columns([1,1,2])

    with col1:
        st.markdown("##### 标的资产参数")
        current_price = st.number_input("当前价格", value=100)
        strike_price = st.number_input("执行价格（等于雪球合约创建日标的价格）", value=100)
        risk_free_rate = st.number_input("无风险利率（%）", value=3.0) / 100
        sigma = st.number_input("年化波动率（%）", value=15.0) / 100
        is_ki = st.selectbox("是否已经敲入（评估日在合约开始日之后）", (True, False), 1)
        
    with col2:
        st.markdown("##### 雪球合约参数")
        ki = st.number_input("敲入比率", value=0.85)
        ko = st.number_input("敲出比率", value=1.05)
        ko_lock = st.number_input("敲出观察锁定期（月）", value=0)
        start_date = st.date_input("合约创建日").strftime("%Y-%m-%d")
        maturity_date = st.date_input("合约结束日", datetime.datetime.today() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        evaluation_date = st.date_input("定价评估日", datetime.datetime.today()).strftime("%Y-%m-%d")
        
    snowball_kwargs = {
        "current_price": current_price,
        "strike_price": strike_price,
        "risk_free_rate": risk_free_rate,
        "sigma": sigma,
        "ki": ki,
        "ko": ko,
        "ko_lock": ko_lock,
        "start_date": start_date,
        "maturity_date": maturity_date,
        "evaluation_date": evaluation_date,
        "is_ki": is_ki,
        "num_cores": 20,
        "verbose": False
    }    

    with col3:
        st.markdown("##### 定价引擎")
        principal = st.number_input("名义本金", value=1000000)
        snowball_kwargs["principal"] = principal
        price_choice = {
            0: "定票息（目标价格为0）", 
            1: "定价格（给定票息）"
        }
        choice = st.radio("定价选项", (0, 1), format_func=lambda x: price_choice[x])
        
        if choice == 1:
            coupon_rate = st.number_input("票息率（%）", value=10.0) / 100
            snowball_kwargs["coupon_rate"] = coupon_rate
            
        num_paths = st.number_input("蒙特卡洛模拟路径数", value=300000)
        snowball_kwargs["num_paths"] = num_paths
        
        if st.button("蒙特卡洛模拟开始定价"):
            with st.spinner('定价路径模拟中......'):
                start_time = time.time()  # 程序开始时间
                if choice == 0:
                    result = calculate_coupon_snowball(**snowball_kwargs)
                    st.info(f"票息率：{result:.4f}")
                else:
                    snowball_kwargs["only_price"] = False
                    result = snowball_pricing_mcm_mp(**snowball_kwargs)
                    result = pd.DataFrame({"Value": result.values()}, index=result.keys())
                    st.dataframe(result, use_container_width=True)
                end_time = time.time()  # 程序结束时间
                st.info(f"\n模拟运行时间：{end_time - start_time:.5f}秒")
                st.success("定价完成！", icon="✅")