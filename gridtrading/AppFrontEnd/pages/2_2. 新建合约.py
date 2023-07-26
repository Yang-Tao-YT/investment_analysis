import streamlit as st
import datetime
import os
import config
import pandas as pd
from utils import cal_coupon, cal_delta, read_etf_price, read_stock_price, format_money, stock_last_price, get_stock_name, get_industry_name

if "authentication_status" in st.session_state and st.session_state.authentication_status:  
    
    st_dict = st.session_state.to_dict()
    for keys, values in st_dict.items():
        st.session_state[keys] = values     
    
    st.set_page_config(page_title="新建合约", page_icon="💰", layout="wide")
    st.title("新建合约")
    st.write("----------------------------------------------------------------------")
    st.write("""
            <style>
                div[class*="stNumberInput"] label p {
                font-size:110%; 
                font-weight:bold; 
            }
                div[class*="stRadio"] label p {
                font-size:110%; 
                font-weight:bold; 
            }
                div[class*="stDateInput"] label p {
                font-size:110%; 
                font-weight:bold; 
            }
            </style> 
            """, 
            unsafe_allow_html=True)

    # 当前日期
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    st.sidebar.markdown(f"#### 当前日期：{today}")

    # ------------------------------------------------------------------------------------------------------
    st.markdown("### 1. 标的选择")

    if "target" in st.session_state and st.session_state.target:
        target_index = 0 if st.session_state.target == "股票" else 1
        target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True, key="target", index=target_index)
    else:
        target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True, key="target")

    if "update_stock" not in st.session_state:
        st.session_state.update_stock = False
    def set_target_callback():
        st.session_state.update_stock = True
        
    if target == "股票":
        if "ticker" in st.session_state and st.session_state.ticker:
            ticker = st.text_input("请输入股票代码：", value=st.session_state.ticker, on_change=set_target_callback, key="ticker")
        else:
            ticker = st.text_input("请输入股票代码：", placeholder="000001", on_change=set_target_callback, key="ticker")
        ticker_list = read_stock_price().columns
    else:
        if "ticker" in st.session_state and st.session_state.ticker:
            ticker = st.text_input("请输入ETF代码：", value=st.session_state.ticker, on_change=set_target_callback, key="ticker")
        else:
            ticker = st.text_input("请输入ETF代码：", placeholder="501500", on_change=set_target_callback, key="ticker")    
        ticker_list = read_etf_price().columns
        
    if not ticker:
        st.info("请输入标的代码！")
        st.stop()    
    elif ticker and ticker not in ticker_list:
        st.error('标的代码输入错误，请重新输入！', icon="🚨")
        st.stop()

    if target == "股票":
        stock_name = get_stock_name(ticker=ticker)
        if not isinstance(stock_name, str):
            st.warning("该股票代码不在股票池中")
            st.stop()
        industry_name = get_industry_name(ticker=ticker)
        st.markdown(f"###### 股票名称：{stock_name}")
        st.markdown(f"###### 一级行业：{industry_name}")

    if st.sidebar.button("刷新最新价格") or st.session_state.update_stock:
        cur_price, pct_change = stock_last_price(ticker)
        st.session_state.cur_price, st.session_state.pct_change = cur_price, pct_change
        if st.session_state.update_stock:
            st.session_state.ki, st.session_state.ko = 0.8, 1.05
            st.session_state.principal = 1000000
            st.session_state.start_date = datetime.datetime.today().strftime("%Y-%m-%d")
            st.session_state.term = 180
            if "pred_vola" in st.session_state:
                del st.session_state["pred_vola"]
        st.session_state.update_stock = False
    if "cur_price" in st.session_state:
        st.sidebar.metric(label=f"{ticker} 最新价格", 
                        value=st.session_state.cur_price, 
                        delta=f"{st.session_state.pct_change:.2%}", 
                        delta_color="inverse")

    if st.session_state.cur_price == 0:
        st.warning("当前股票无行情数据")
        st.stop()

    # -------------------------------------------------------------------------------------------------------
    st.markdown("### 2. 雪球合约设置")

    col_1, col_2 = st.columns([1, 3])
    with col_1:
        principal = st.number_input("本金", value=st.session_state.principal, key="principal")
    with col_2:
        st.write("人民币")
        st.markdown(format_money(principal))
    
    strike_price = st.number_input("期初价格", value=st.session_state.cur_price, key="strike_price")
    st.caption("期初价格默认等于标的最新价格，定价时作为蒙塔卡罗模拟的起点。")

    price_way = st.radio("敲入敲出价格决定方法：", ["绝对价格", "相对比率"], horizontal=True)

    col_3, col_4 = st.columns(2)

    if price_way == "相对比率":
        with col_3:
            ki = st.number_input("敲入比率", value=st.session_state.ki)
            ki_price = ki * strike_price
            st.write(f"敲入价格：{ki_price:.2f}")
        with col_4:
            ko = st.number_input("敲出比率", value=st.session_state.ko)
            ko_price = ko * strike_price
            st.write(f"敲出价格：{ko_price:.2f}")
    else:
        with col_3:
            ki_price = st.number_input("敲入价格", value=st.session_state.strike_price * st.session_state.ki)
            ki = ki_price / strike_price
            st.write(f"敲入比率：{ki:.2f}")
        with col_4:
            ko_price = st.number_input("敲出价格", value=st.session_state.strike_price * st.session_state.ko)
            ko = ko_price / strike_price
            st.write(f"敲出比率：{ko:.2f}")
            
    if ki != st.session_state.ki or ko != st.session_state.ko:
        st.session_state.ki, st.session_state.ki_price = ki, ki_price
        st.session_state.ko, st.session_state.ko_price = ko, ko_price
        st.experimental_rerun()    

    start_date = st.date_input("合约创建日", value=datetime.datetime.strptime(st.session_state.start_date, "%Y-%m-%d"))
    term = st.number_input("合约期限（天）", value=st.session_state.term, key="term")

    end_date = start_date + datetime.timedelta(days=term)
    start_date, end_date = start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    if start_date != st.session_state.start_date:
        st.session_state.start_date, st.session_state.end_date = start_date, end_date
        st.experimental_rerun()

    contract_state = st.button("确认合约信息，获取预测波动率")
    if not contract_state and "pred_vola" not in st.session_state:
        st.stop()
    if contract_state and "coupon_rate" in st.session_state:
        del st.session_state["coupon_rate"]
        del st.session_state["delta"]
    if contract_state and "pred_vola" in st.session_state:
        del st.session_state["pred_vola"]
    # ----------------------------------------------------------------------------------------------------
    st.markdown("#### 3. 波动率预测")

    if "pred_vola" not in st.session_state:
        st.info("标的信息已同步至波动率分析页面，请浏览波动率分析页面获取预测波动率！")
        st.stop()
    else:
        st.info(f"获取预测波动率成功，预测波动率为{st.session_state.pred_vola:.2%}")
        
    # ----------------------------------------------------------------------------------------------------
    st.markdown("#### 4. 期初定票息")

    sigma = st.session_state.pred_vola

    snowball_kwargs = {
        "current_price": strike_price,
        "strike_price": strike_price,
        "principal": principal,
        "risk_free_rate": 0.03,
        "sigma": sigma,
        "ki": ki,
        "ko": ko,
        "start_date": start_date,
        "maturity_date": end_date,
        "evaluation_date": start_date,
        "num_cores": 20,
    } 

    if st.button("计算票息和底仓Delta"):
        if "ready_contract" in st.session_state:
            del st.session_state["ready_contract"]
        with st.spinner('定价路径模拟中......'):
            coupon_rate = cal_coupon(**snowball_kwargs)
            snowball_kwargs["coupon_rate"] = coupon_rate
            snowball_kwargs.pop("current_price")
            delta = cal_delta(current_price=strike_price, **snowball_kwargs)
            st.session_state.coupon_rate, st.session_state.delta = coupon_rate, delta
    if "coupon_rate" in st.session_state:
        st.success(f"票息率：{st.session_state.coupon_rate:.2%} | 底仓Delta：{st.session_state.delta:.2f}")
    else:
        st.stop()
        
    # -------------------------------------------------------------------------------------------------------------
    st.markdown("#### 5. 雪球回测")
    st.info("合约信息已同步至雪球历史回测页面，请点击该页面进行回测！")
    if st.button("完成雪球回测，生成该雪球合约信息"):
        st.session_state.ready_contract = True
        pass
    else:
        if not "ready_contract" in st.session_state: 
            st.stop()

    # -------------------------------------------------------------------------------------------------------------
    st.markdown("### 最终合约生成")

    recommender = st.radio("推荐人：", options=["陈翔", "刘波"], horizontal=True)
    reason = st.text_area("推荐理由：", placeholder="请输入推荐理由")

    unique_id = ticker + "_" + stock_name + "_" + start_date.replace('-', '') + "_" + recommender
    contract_info = {
        "ID": [unique_id],
        "代码": [ticker],
        "名称": [stock_name],
        "行业": [industry_name],
        "合约本金": [principal],
        "定票息年化波动率": [sigma],
        "票息率": [st.session_state.coupon_rate],
        "底仓Delta": [st.session_state.delta],
        "期初价格": [strike_price],
        "敲入线":[ki],
        "敲出线": [ko],
        "敲入价格": [ki_price],
        "敲出价格": [ko_price],
        "合约创建日": [start_date],
        "合约建仓日": [""],
        "合约结束日": [""],
        "合约期限（天）": [term],
        "底仓是否建立": [False],
        "暂停对冲": [False],
        "一键清仓": [False],
        "推荐人": [recommender],
        "推荐理由": [reason]
    }
    contract_df = pd.DataFrame(contract_info)
    
    st.info("请确认合约信息，如确认创建此合约，请点击下方按钮，系统会在后端自动生成合约文件！")
    st.dataframe(contract_df)

    if st.button("确认创建此合约"):
        folder_path = f"{config.grid_trading_doc_path}/remaining/{unique_id}"
        os.makedirs(folder_path)
        contract_df.to_csv(f"{folder_path}/{unique_id}_contract.csv", index=False)
        st.success("合约创建成功，后端已写入合约文件！")

