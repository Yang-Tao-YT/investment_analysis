import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from gridtrading.AppFrontEnd.utils import snowball_backtest, read_stock_price, read_etf_price, snowball_hedger, format_money

if "authentication_status" in st.session_state and st.session_state.authentication_status:
    st.set_page_config(page_title="雪球历史回测", page_icon="❄️", layout="wide")
    st.title("雪球历史回测")

    if "target" in st.session_state and st.session_state.target:
        target_index = 0 if st.session_state.target == "股票" else 1
        target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True, index=target_index)
    else:
        target = st.radio("请选择标的类型：", ('股票', 'ETF'), horizontal=True)

    if "ticker" in st.session_state and st.session_state.ticker:
        ticker = st.session_state.ticker
        term = st.session_state.term
        ki = st.session_state.ki
        ko = st.session_state.ko
        principal = st.session_state.principal
        coupon_rate = st.session_state.coupon_rate
    else:
        term = 180
        ticker = "000001" if target == "股票" else "510500"
        ki, ko = 0.85, 1.05
        principal = 1000000
        coupon_rate = 0.2

    if target == "股票":
        ticker = st.text_input("请输入股票代码：", ticker)
        price_data = read_stock_price()
    else:
        ticker = st.text_input("请输入ETF代码：", ticker)
        price_data = read_etf_price()

    if ticker not in price_data.columns:
        st.error('标的代码输入错误，请重新输入！', icon="🚨")
        st.stop()
        
    price_series = price_data[ticker].dropna()

    col_1, col_2 = st.columns([1, 3])

    with col_1:
        st.markdown("##### 雪球合约参数")
        ki = st.number_input("敲入比率", value=ki)
        ko = st.number_input("敲出比率", value=ko)
        principal = st.number_input("名义本金", value=principal)
        st.markdown(format_money(principal))
        

    with col_2:

        tab_1, tab_2 = st.tabs(["滚动回测雪球合约", "雪球动态对冲回测"])

        with tab_1:
            st.markdown("##### 滚动回测雪球合约参数设置")
            st.caption("固定间隔下新建雪球合约，统计所有雪球合约的盈亏情况")
            
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                start_date = st.date_input("回测起始日期", datetime.datetime(2016, 1, 1)).strftime("%Y-%m-%d")
                window = st.number_input("单份合约期限（天）", value=term)
            with sub_col2:
                end_date = st.date_input("回测结束日期").strftime("%Y-%m-%d")
                coupon_rate = st.number_input("雪球票息率（%）", value=coupon_rate * 100) / 100
            with sub_col3:
                step = st.number_input("滚动回测间隔（天）", value=5)
                discount_rate = st.number_input("折现率（%）", value=3.0) / 100
                
            if st.button("开始回测"):
                with st.spinner():
                    result = snowball_backtest(price_series=price_series.loc[start_date:end_date], window=window, step=step)
                    record = pd.merge(price_series.loc[start_date:], result["Profit"], how="left", left_index=True, right_index=True)
                
                st.markdown("##### 回测结果")
                
                sub_tab_1, sub_tab_2, sub_tab_3 = st.tabs(["历史序列图", "盈亏分布图", "敲入敲出统计"])
                
                with sub_tab_1:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=record.index, y=record["Profit"], name="雪球合约盈亏"))
                    fig.add_trace(go.Scatter(x=record.index, y=record[ticker].values, name=f"{ticker}（右轴）", 
                                            yaxis="y2", line=dict(color="orange")))
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=''),
                                      yaxis2=dict(anchor='x', overlaying='y', side='right'),
                                      title="雪球合约滚动回测结果", title_x=0.43, xaxis_title="Time", 
                                      yaxis_title="Snowball PnL", yaxis2_title="Price")
                    st.plotly_chart(fig, use_container_width=True)

                with sub_tab_2:
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        fig = px.histogram(record, y="Profit")
                        fig.update_layout(title="PnL Histogram", title_x=0.5)
                        st.plotly_chart(fig, use_container_width=True)
                    with sub_col2:
                        fig2 = px.box(record, y="Profit")
                        fig2.update_layout(title="PnL BoxPlot", title_x=0.5)
                        st.plotly_chart(fig2, use_container_width=True)

                with sub_tab_3:
                    knock_out = result["KO Date"]
                    knock_in = result["KI Date"]
                    ko_ratio = knock_out.count() / knock_out.shape[0]
                    ki_ratio = knock_in.count() / knock_in.shape[0]
                    none_kiko_ratio = 1 - ko_ratio - ki_ratio
                    res_df = pd.DataFrame({"Value": [ko_ratio, ki_ratio, none_kiko_ratio]}, 
                                        index=["敲出占比", "敲入未敲出占比", "未敲出未敲入占比"])
                    st.dataframe(res_df)

        with tab_2:
            st.markdown("##### 动态对冲参数设置")
            st.caption("对一份雪球合约进行Delta对冲，每日根据Delta值对对冲仓位进行调仓，直至雪球敲出或到期")
            
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                start_date = st.date_input("合约开始日期", datetime.datetime.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
                end_date = st.date_input("合约结束日期", 
                                        value=datetime.datetime.today() - datetime.timedelta(days=1),
                                        max_value=datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                risk_free_rate = st.number_input("无风险利率（BSM定价中的漂移项 %）", value=3) / 100
                trade_cost = st.number_input("双边交易成本（%）", value=0.15, step=0.01) / 100
            with sub_col2:
                if_pre_define_sigma = st.radio("是否采用自定义输入的波动率", [True, False], horizontal=False)
                pre_define_sigma = constant_sigma = sigma_window = None
                if if_pre_define_sigma:
                    pre_define_sigma = st.number_input("请输入波动率（%）", value=15) / 100
                else:
                    sigma_window = st.number_input("波动率预测回望窗口长度（年）", value=1)
                    constant_sigma = st.selectbox("在定价日后计算delta是否采用定价日的波动率，否则采用最新时点的波动率预测值", [True, False])
            
            hedge_method = {
                0: "日频固定时点对冲", 
                1: "日频Delta敞口对冲"
            }
            choice = st.radio("定价选项", (0, 1), format_func=lambda x: hedge_method[x])
            num_paths = st.slider("单次定价模拟路径数量", 50000, 500000, step=10000)
            st.caption("选用过小的模拟路径数量可能导致delta计算不稳定，过大则导致回测速度过慢")
            
            exp_upper_limit = exp_down_limit = 0
            if choice == 1:
                ch1, ch2 = st.columns(2)
                with ch1:
                    exp_upper_limit = st.number_input("敞口上限", value=0.01)
                with ch2:
                    exp_down_limit = st.number_input("敞口下限", value=-0.01)
                st.caption("敞口 = 最新雪球Delta - 当前对冲仓位Delta，当敞口在上下限之间时，不做对冲操作")   
            
            price_series.index = [datetime.datetime.strptime(i, "%Y-%m-%d") for i in price_series.index]

            if st.button("开始动态对冲回测"):
                backtest_record, metrics = snowball_hedger(
                    price_series=price_series,
                    risk_free_rate=risk_free_rate,
                    sigma_window=sigma_window,
                    pre_define_sigma=pre_define_sigma,
                    principal=principal,
                    trade_cost=trade_cost,
                    constant_sigma=constant_sigma,
                    ki=ki,
                    ko=ko,
                    start_date=start_date,
                    end_date=end_date,
                    num_paths=num_paths,
                    choice=choice,
                    exp_upper_limit=exp_upper_limit,
                    exp_down_limit=exp_down_limit
                )

                sub_tab_4, sub_tab_5, sub_tab_6 = st.tabs(["净值曲线图", "回测指标", "回测记录"])
                
                with sub_tab_4:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=backtest_record.index, 
                                            y=backtest_record["total account"] / principal, 
                                            name="复制仓位"))
                    fig.add_trace(go.Scatter(x=backtest_record.index, 
                                            y=backtest_record["snowball value"] / principal, 
                                            name="雪球"))
                    fig.add_trace(go.Scatter(x=backtest_record.index, 
                                            y=backtest_record["target asset"] / backtest_record["target asset"][0], 
                                            name="标的资产"))
                    fig.add_trace(go.Scatter(x=backtest_record.index,
                                            y=backtest_record["pos_delta"],
                                            name="复制仓位Delta（右轴）",
                                            yaxis="y2",
                                            line=dict(dash="dot")))
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=''),
                                      yaxis2=dict(anchor='x', overlaying='y', side='right'),
                                      title="雪球动态对冲回测结果", title_x=0.4, xaxis_title="Time", 
                                      yaxis_title="净值", yaxis2_title="Delta")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                with sub_tab_5:
                    st.dataframe(metrics)

                with sub_tab_6:
                    st.dataframe(backtest_record)
                    
    st_dict = st.session_state.to_dict()
    for keys, values in st_dict.items():
        st.session_state[keys] = values 