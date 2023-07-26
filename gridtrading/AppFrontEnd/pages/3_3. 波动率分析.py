import streamlit as st
import datetime
import plotly.express as px
import plotly.graph_objects as go
from Pricing.volatility_cone_surface import *
from Pricing.predict_volatility import *
from gridtrading.AppFrontEnd.utils import last_n_business_days, read_etf_price, read_stock_price

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    today = datetime.datetime.today()

    st.set_page_config(page_title="波动率分析", page_icon="📈", layout="wide")
    st.title("波动率分析")
    st.write("----------------------------------------------------------------------")

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("#### 参数设置")
        
        if "target" in st.session_state and st.session_state.target:
            target_index = 0 if st.session_state.target == "股票" else 1
            target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True, index=target_index)
        else:
            target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True)
        
        if "ticker" in st.session_state and st.session_state.ticker:
            ticker = st.session_state.ticker
            term = st.session_state.term
        else:
            term = 180
            ticker = "000001" if target == "股票" else "510500"
        
        if target == "股票":
            ticker = st.text_input("请输入股票代码：", ticker)
            price_data = read_stock_price()
        else:
            ticker = st.text_input("请输入ETF代码：", ticker)
            price_data = read_etf_price()
        
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            window_1 = st.number_input("波动率期限1", 30)
        with sub_col2:
            window_2 = st.number_input("波动率期限2", 60)
            
        sub_col3, sub_col4 = st.columns(2)
        with sub_col3:
            window_3 = st.number_input("波动率期限3", 90)
        with sub_col4:
            window_4 = st.number_input("波动率期限4", term)
            
        window = [window_1, window_2, window_3, window_4]    
        
        evaluation_date = st.date_input("评估日期", last_n_business_days(today.strftime("%Y-%m-%d"), n=1)).strftime("%Y-%m-%d")
        while evaluation_date not in price_data.index:
            evaluation_date = last_n_business_days(evaluation_date, n=1).strftime("%Y-%m-%d")

        if ticker not in price_data.columns:
            st.error('标的代码输入错误，请重新输入！', icon="🚨")
            st.stop()
        
        st.markdown("#### 历史走势")
        
        price_series = price_data[ticker].dropna()
        price_series = price_series.loc[:evaluation_date]
        cur_window = st.selectbox("展示波动率期限", window)
        return_series = transfer_price_logreturn(price_series=price_series)
        cur_vola = return_series.rolling(window=cur_window).apply(lambda x: x.std() * 242 ** 0.5).dropna()
        
        fig = px.line(price_series)
        fig.add_trace(go.Scatter(x=cur_vola.index, y=cur_vola, name=f"{cur_window} day volatility (right axis)", 
                                 yaxis='y2', line=dict(color="orange")))
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=''),
                          yaxis2=dict(anchor='x', overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

    # 计算波动率锥
    cone = get_VolatilityCone(price_series=price_series,
                              term=window, 
                              evaluation_date=evaluation_date)

    with col2:
        st.markdown("#### 波动率预测")
        
        tab_1, tab_2 = st.tabs(["GARCH", "Prophet"])
        
        with tab_1:
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                lookback_window = st.number_input("回望窗口长度（天）", value=252)
            with sub_col2:
                p = st.number_input("p（标准残差滞后阶数）", value=1)
            with sub_col3:
                q = st.number_input("q（条件方差滞后阶数）", value=1)
                
            predicted_vola = vol_predict_garch(price_series=price_series.iloc[-lookback_window-1:], term=window_4, p=p, q=q, return_all=True)
            
        fig = px.line(predicted_vola)
        fig.update_layout(height=265)
        st.plotly_chart(fig, use_container_width=True)
            
            
        st.markdown("#### 波动率锥")
        
        tab_1, tab_2 = st.tabs(["图片", "数据"])
        
        with tab_1:
            cone["Volatility Prediction"] = [predicted_vola.iloc[window_1-1, 0], predicted_vola.iloc[window_2-1, 0],
                                             predicted_vola.iloc[window_3-1, 0], predicted_vola.iloc[window_4-1, 0]]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cone.index, y=cone.iloc[:, -2].values, name=cone.columns[-2], line=dict(width=4, color="orange")))
            fig.add_trace(go.Scatter(x=cone.index, y=cone.loc[:, "Volatility Prediction"].values, 
                                    name="Volatility Prediction", line=dict(width=6, color="red")))
            color_list = ["blue", "purple", "green", "pink", "grey"]
            for color, col in zip(color_list, cone.columns[:-2]): 
                fig.add_trace(go.Scatter(x=cone.index, y=cone.loc[:, col].values, name=col, line=dict(width=2, dash="dot", color=color)))
            fig.update_xaxes(type='category')    
            fig.update_layout(title=f"Volatility Cone of {ticker}",
                              title_x=0.35,
                              xaxis_title='Term',
                              yaxis_title='Annual Volatility')
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab_2:
            st.markdown("##### 波动率锥数据")
            st.dataframe(cone, use_container_width=True)

    if "ticker" in st.session_state and st.session_state.ticker and ticker == st.session_state.ticker:
        cur_pred_vola = predicted_vola.iloc[int(st.session_state.term/2)-1, 0]        
        st.info(f"合约标的：{st.session_state.ticker}，"
                f"合约期限：{st.session_state.term}天，"
                f"默认{int(st.session_state.term/2)}日预测波动率：{cur_pred_vola:.2%}")
        adjusted_pred_vola = st.number_input("手动调整波动率预测（%）", value=cur_pred_vola * 100) / 100
        if st.button("确认波动率预测且同步至新建合约页面"):
            st.session_state.pred_vola = adjusted_pred_vola
            st.success("同步成功，请返回新建合约页面！")

    st_dict = st.session_state.to_dict()
    for keys, values in st_dict.items():
        st.session_state[keys] = values        
