import streamlit as st
import pandas as pd
import numpy as np
from time import sleep
import datetime
import os
import shutil
import config as config
from utils import *
import plotly.graph_objects as go
from Pricing.predict_volatility import vol_predict_garch

if "authentication_status" in st.session_state and st.session_state.authentication_status:    
    st.set_page_config(page_title="持仓和对冲", page_icon="💰", layout="wide")
    st.write("""
                <style>
                    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                    font-size:200%;
                    font-weight:bold;
                    }
                </style>
            """, 
            unsafe_allow_html=True)

    # 当前日期
    today_ = datetime.datetime.today().strftime("%Y-%m-%d")
    today = datetime.datetime.today().strftime("%Y%m%d")
    st.sidebar.markdown(f"#### 当前日期：{today_}")

    # 获取当前存续合约信息
    remaining_contract = os.listdir(f"{config.grid_trading_doc_path}/remaining")
    def extract_date(contract_id):
        first = contract_id.index("_")
        second = contract_id.index("_", first+1)
        date = int(contract_id[second+1:second+9])
        return date
    remaining_contract.sort(key=lambda x:extract_date(x), reverse=True)  # 合约按照创建日期降序排列
    
    num_remaining_contract = len(remaining_contract)
    st.sidebar.markdown(f"#### 当前存续合约数量：{num_remaining_contract}")

    position, hedge, update_position, net_value = st.tabs(["持仓分析", "对冲交易", "上传交易记录", "盘后更新净值"])

    with position:
        contract_id = st.sidebar.radio("请选择合约（标的代码_名称_起始日期_推荐人）：", 
                                    remaining_contract, 
                                    format_func=lambda x: get_contract_color_name(x),
                                    on_change=stop_update3)
        st.sidebar.write("🟩:未建仓 🟦:已建仓")
        st.sidebar.write("🟥:需清仓 🟨:暂停对冲")
        contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
        contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})

        def save_contract(contract_info):
            contract_info.to_csv(contract_info_path, index=False) 

        st.markdown("##### 合约信息")

        ticker = contract_info.loc[0, "代码"]
        recommender = contract_info.loc[0, "推荐人"]
        reason = contract_info.loc[0, "推荐理由"]
        st.text(f"推荐人：{recommender}\n"
                f"推荐理由：{reason}")

        tab_1, tab_2 = st.tabs(["## 展示合约信息", "## 修改合约信息"])

        with tab_1:
            st.dataframe(contract_info.iloc[:, :-5], use_container_width=True, hide_index=True)
            st.dataframe(contract_info.iloc[:, -5:-2], hide_index=True)
        with tab_2:
            modified_contract_info = st.data_editor(contract_info, use_container_width=True, hide_index=True)
            if (contract_info.fillna(0) == modified_contract_info.fillna(0)).sum(axis=1).squeeze() < len(contract_info.columns):
                updated_contract_info = update_contract_boundary(contract_info, modified_contract_info)
                st.info("修改后的合约信息如下，点击下方确认按钮将写入后端文件")
                st.dataframe(updated_contract_info, hide_index=True)
            
                if st.button("确认修改合约信息"):
                    save_contract(updated_contract_info)
                    st.experimental_rerun()
            
        st.markdown("##### 合约状态")

        base_position_state = contract_info.loc[0, "底仓是否建立"]
        stop_hedge_state = contract_info.loc[0, "暂停对冲"]
        clear_position_state = contract_info.loc[0, "一键清仓"]

        if not base_position_state:
            st.warning("该合约目前底仓未建立，尚未开始对冲，请按照底仓delta和期初价格建立底仓！")
            if st.button("一键删除该合约，此操作将删除合约后端文件且无法恢复，确认删除"):
                shutil.rmtree(f"{config.grid_trading_doc_path}/remaining/{contract_id}")
                st.success("删除成功，刷新该页面后该合约将不可见！")
            
            # 下载建仓指令文件
            real_time_data = read_real_time()
            cur_price = real_time_data.loc[ticker, "最新价"]
            exchange_id = 0 if real_time_data.loc[ticker, "交易所"] == "SSE" else 1
            target_pos = contract_info.loc[0, "合约本金"] / cur_price * contract_info.loc[0, "底仓Delta"]
            cur_trade_dos = pd.DataFrame(
                {
                    "TradingDay": [today],
                    "UserID": ["66622"],
                    "InvestorID": ["216806801"],
                    "ExchangeID":[exchange_id],
                    "InstrumentID": [ticker],
                    "StrategyID": ["grid"],
                    "TargetNetPosition": [target_pos],
                    "StartTradingTime": [""],
                    "AlgoType": [3],
                    "UserCustom": [""],
                    "StrategyIsTrading": [0], 
                    "StrategyPrice": ["A"],
                    "AddPositionType": [1],
                    "MactchTrdVol": [0],
                    "MactchTrdPriceType": ["X"],
                    "VwapMaxVolume": [50000],
                    "TotalTimeAvail": [3600]
                }
            )
            trading_docs = pd.DataFrame(cur_trade_dos)
            st.download_button("下载建仓指令文件", trading_docs.to_csv(index=False).encode("utf-8"), file_name=f"grid_{today}_{ticker}_建仓指令文件.csv")
        else:
            if clear_position_state:
                st.info("合约已进入等待清仓状态！")
                if st.button("取消一键清仓"):
                    clear_position_state = contract_info.loc[0, "一键清仓"] = False
                    save_contract(contract_info) 
                    st.experimental_rerun()     
            else:
                if not stop_hedge_state:
                    st.info("该合约底仓已建立，已开始对冲！")
                    if st.button("暂停对冲"):
                        stop_hedge_state = contract_info.loc[0, "暂停对冲"] = True
                        save_contract(contract_info) 
                        st.experimental_rerun()
                else:
                    st.info("该合约已暂停对冲！")
                    if st.button("恢复对冲"):
                        stop_hedge_state = contract_info.loc[0, "暂停对冲"] = False
                        save_contract(contract_info) 
                        st.experimental_rerun()
                if st.button("一键清仓"):
                    clear_position_state = contract_info.loc[0, "一键清仓"] = True
                    save_contract(contract_info) 
                    st.experimental_rerun()
        
        real_time_data = read_real_time()
        ticker_data = real_time_data.loc[ticker]
        cur_price = ticker_data["最新价"]
        pct_change = ticker_data["涨跌幅"]
    
        if base_position_state:
            st.markdown("##### 当前持仓盈亏")
            fig_tab, chart_tab = st.tabs(["## 盈亏数据", "## 历史盈亏走势"])

            with fig_tab:
                cur_price, current_volume, pnl, last_volume, last_pnl, today_pnl, _ = contract_pnl_volume(contract_id, ticker)
                volume_col, delta_col, cur_position_col, pnl_col, pnl_percent_col = st.columns(5)
                with volume_col:
                    st.metric("当前持仓股数", value=int(current_volume))
                with delta_col:
                    pos_delta = current_volume / (contract_info.loc[0, "合约本金"] / contract_info.loc[0, "期初价格"])
                    st.metric("当前持仓Delta", value=f"{pos_delta:.4f}")
                with cur_position_col:
                    st.metric("最新市值", value=format_money(cur_price * current_volume))
                with pnl_col:
                    st.metric("累计盈亏", value=format_money(pnl), delta=f"{today_pnl:.0f}", delta_color="inverse")
                    
                with pnl_percent_col:
                    pnl_percent = pnl / contract_info.loc[0, "合约本金"]
                    st.metric("累计盈亏 / 名义本金", value=f"{pnl_percent :.2%}")
                    
            with chart_tab:
                try:
                    net_value_series = pd.read_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_netvalue_record.csv",
                                                index_col=0)
                    last_bd = last_n_business_days(net_value_series.index[0], 1).strftime("%Y-%m-%d")
                    net_value_series.loc[last_bd, :] = [0, 0, 0]
                    net_value_series = net_value_series.sort_index()
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=net_value_series.index, y=net_value_series["持仓股数"], name="持仓股数"))
                    fig.add_trace(go.Scatter(x=net_value_series.index, y=net_value_series["累计盈亏"], name="累计盈亏（右轴）", 
                                            yaxis="y2", line=dict(color="orange")))
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=''),
                                    yaxis2=dict(anchor='x', overlaying='y', side='right'),
                                    title="历史盈亏图", title_x=0.46, xaxis_title="时间", 
                                    yaxis_title="持仓股数", yaxis2_title="PnL",
                                    xaxis=dict(type="category"))
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
                
            st.markdown("##### 当前估值盈亏")
            
            price_tab, delta_series_tab = st.tabs(["## 定价估值", "## 当日Delta序列"])
            
            with price_tab:
                if st.button("以当前最新价格对合约进行定价估值"):
                    with st.spinner("定价中.."):
                        pricing_pnl, real_time_delta = price_contract(contract_id)
                        real_time_delta = get_delta(contract_id, cur_price)
                        price_pnl_col, price_delta_col = st.columns(2)
                        with price_pnl_col:
                            st.metric("估值盈亏", f"{pricing_pnl:.2f}")
                        with price_delta_col:
                            st.metric("估值delta", f"{real_time_delta:.4f}")
            with delta_series_tab:
                try:
                    delta_series = pd.read_csv(f"{config.delta_path}/{contract_id}.csv", index_col=0)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=delta_series.index, y=delta_series["Delta"], name="原始Delta"))
                    fig.add_trace(go.Scatter(x=delta_series.index, y=delta_series["平滑Delta"], name="平滑Delta"))
                    cur_delta = get_delta(contract_id, cur_price)
                    fig.add_annotation(x=cur_price, y=cur_delta, 
                                       text=f"当前价格平滑Delta：{cur_delta:.4f}", 
                                       showarrow=True,
                                       arrowhead=1,
                                       ax=0, ay=-40)
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                                      title=f"{ticker}当日Delta序列", title_x=0.44)
                    
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
                if st.button("重新计算当日Delta序列"):
                    with st.spinner("计算中"):
                        delta_series = contract_delta_list_nocache(contract_id)
                        delta_series.to_csv(f"{config.delta_path}/{contract_id}.csv")
                        st.success("计算成功！")
                
                    
        st.markdown(f"##### 标的资产 {ticker} 当前行情")

        strike_price = contract_info.loc[0, "期初价格"]
        ratio = cur_price / strike_price

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="最新价格", value=cur_price, delta=f"{pct_change:.2%}", delta_color="inverse")
        with col2:
            st.metric(label="最新价格 / 期初价格", value=f"{ratio:.3f}")
        with col3:
            pass
        
        if st.button("每三秒刷新价格"):
            st.session_state.update3 = True
        if st.button("暂停刷新"):
            st.session_state.update3 = False
            
        if "update3" in st.session_state and st.session_state.update3:
            sleep(3)
            st.experimental_rerun()

    with hedge:
        st.markdown("##### 计算所有已建仓合约当日Delta序列")
        st.caption("请于每日盘前计算！")
        if st.button("开始计算"):
            my_bar = st.progress(0)
            for i, contract_id in enumerate(remaining_contract):
                contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
                contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
                if contract_info.loc[0, "底仓是否建立"]:
                    delta_series = contract_delta_list(contract_id)
                    delta_series.to_csv(f"{config.delta_path}/{contract_id}.csv")
                my_bar.progress((i + 1) / num_remaining_contract)
            st.success("计算完成！")
                    
        st.write("----")       
        
        st.markdown("##### 生成交易指令文件")
        
        if st.button("开始按当前最新价格计算所有合约delta值， 并生成交易指令文件"):
            st.session_state.update3 = False
            # 读取最新价格和历史价格序列
            real_time_data = read_real_time()
            price_data = read_stock_price()
            # 生成交易文件
            trade_docs = pd.DataFrame()
            
            my_bar = st.progress(0)
            for i, contract_id in enumerate(remaining_contract):
                contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
                contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
                
                # 提取合约参数
                ticker = contract_info.loc[0, "代码"]
                principal = contract_info.loc[0, "合约本金"]
                coupon_rate = contract_info.loc[0, "票息率"]
                strike_price = contract_info.loc[0, "期初价格"]
                ki = contract_info.loc[0, "敲入线"]
                ko = contract_info.loc[0, "敲出线"]
                start_date = contract_info.loc[0, "合约建仓日"]
                end_date = contract_info.loc[0, "合约结束日"]
                sigma = contract_info.loc[0, "定票息年化波动率"]
                cur_price = real_time_data.loc[ticker, "最新价"]
                exchange_id = 0 if real_time_data.loc[ticker, "交易所"] == "SSE" else 1
                
                if not contract_info.loc[0, "底仓是否建立"]:
                    my_bar.progress((i + 1) / num_remaining_contract)
                    continue
                if contract_info.loc[0, "暂停对冲"]:
                    my_bar.progress((i + 1) / num_remaining_contract)
                    continue
                if contract_info.loc[0, "一键清仓"]:
                    cur_trade_dos = pd.DataFrame(
                        {
                            "TradingDay": [today],
                            "UserID": ["66622"],
                            "InvestorID": ["216806801"],
                            "ExchangeID": [exchange_id],
                            "InstrumentID": [ticker],
                            "StrategyID": ["grid"],
                            "TargetNetPosition": [0],
                            "StartTradingTime": [""],
                            "AlgoType": [3],
                            "UserCustom": [""],
                            "StrategyIsTrading": [0],                        
                            "StrategyPrice": ["A"],
                            "AddPositionType": [1],
                            "MactchTrdVol": [0],
                            "MactchTrdPriceType": ["X"],
                            "VwapMaxVolume": [50000],
                            "TotalTimeAvail": [120]
                        }
                    )
                    trade_docs = pd.concat([trade_docs, cur_trade_dos], axis=0)
                    my_bar.progress((i + 1) / num_remaining_contract)
                    
                    continue

                # 当日定价波动率
                # price_series = price_data[ticker].dropna()
                # vola_start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d") - datetime.timedelta(days=252)
                # predicted_vola = vol_predict_garch(price_series=price_series.loc[vola_start_date.strftime("%Y-%m-%d"):], term=90, return_all=False)
                # # cur_sigma = (predicted_vola + sigma) / 2
                cur_sigma = sigma

                snowball_kwargs = {
                    "strike_price": strike_price,
                    "principal": principal,
                    "risk_free_rate": 0.03,
                    "coupon_rate": coupon_rate,
                    "sigma": cur_sigma,
                    "ki": ki,
                    "ko": ko,
                    "start_date": start_date,
                    "maturity_date": end_date,
                    "evaluation_date": today_,
                    "num_paths":300000,
                    "num_cores": 20,
                } 
                
                # delta = cal_delta(cur_price, **snowball_kwargs)
                delta = get_delta(contract_id, cur_price)
                target_pos = int(delta * principal / strike_price)

                cur_trade_dos = pd.DataFrame(
                    {
                        "TradingDay": [today],
                        "UserID": ["66622"],
                        "InvestorID": ["216806801"],
                        "ExchangeID":[exchange_id],
                        "InstrumentID": [ticker],
                        "StrategyID": ["grid"],
                        "TargetNetPosition": [target_pos],
                        "StartTradingTime": ["14:45:00"],
                        "AlgoType": [3],
                        "UserCustom": [""],
                        "StrategyIsTrading": [0], 
                        "StrategyPrice": ["A"],
                        "AddPositionType": [1],
                        "MactchTrdVol": [0],
                        "MactchTrdPriceType": ["X"],
                        "VwapMaxVolume": [50000],
                        "TotalTimeAvail": [120]
                    }
                )
                trade_docs = pd.concat([trade_docs, cur_trade_dos], axis=0)
                
                my_bar.progress((i + 1) / num_remaining_contract)
            
            trade_docs.to_csv(f"{config.grid_trading_doc_path}/trading_docs/指令文件/{today}_指令文件.csv", index=False)
            st.success("交易指令文件生成成功！")
        
        st.write("---")
        
        st.markdown("##### 下载交易指令文件")
        try:
            trading_docs = pd.read_csv(f"{config.grid_trading_doc_path}/trading_docs/指令文件/{today}_指令文件.csv")
            create_time = os.path.getmtime(f"{config.grid_trading_doc_path}/trading_docs/指令文件/{today}_指令文件.csv")
            st.info(f"已读取到交易指令文件, 创建时间为{datetime.datetime.fromtimestamp(create_time)}")
            st.download_button("下载交易指令文件", trading_docs.to_csv(index=False).encode("utf-8"), file_name=f"grid_{today}_指令文件.csv")
        except:
            st.info("未读取到交易指令文件！")

    with update_position:
        uploaded_file = st.file_uploader("上传交易记录(trade_list)")
        if uploaded_file:
            try:
                trade_list = pd.read_csv(uploaded_file, encoding="gbk", dtype={"证券代码": str})
            except:
                trade_list = pd.read_csv(uploaded_file, encoding="utf-8", dtype={"证券代码": str})
            
            trade_list = trade_list.loc[1:, ["证券代码", "成交结果", "成交价格", "成交数量", "交易费用"]]
            
            if st.button("确认上传交易清单文件"):
                trade_list_path = f"{config.grid_trading_doc_path}/trading_docs/交易清单/{today}_交易清单.csv"
                trade_list.to_csv(trade_list_path, index=False)
                st.success("上传成功！")
        
        st.write("--------")
        
        try:
            create_time = os.path.getmtime(f"{config.grid_trading_doc_path}/trading_docs/交易清单/{today}_交易清单.csv")
            st.info(f"已读取到交易清单文件, 创建时间为{datetime.datetime.fromtimestamp(create_time)}")
        except:
            st.info("未读取到交易清单文件！")
            
        if st.button("根据当日交易清单更新各合约交易记录"):
            trade_list = pd.read_csv(f"{config.grid_trading_doc_path}/trading_docs/交易清单/{today}_交易清单.csv", 
                                    dtype={"证券代码": str, "成交数量": str})
            trade_list['成交数量'] = trade_list['成交数量'].str.replace(',' , '').astype(int)
            trade_list = trade_list[trade_list["成交结果"].isin(["买入成交", "卖出成交"])]

            for i, contract_id in enumerate(remaining_contract):
                contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
                contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
                ticker = contract_info.loc[0, "代码"]

                if ticker in trade_list["证券代码"].tolist(): # 如果当日有交易
                    cur_trade_list = trade_list[trade_list["证券代码"] == ticker]
                    average_price = (cur_trade_list["成交价格"] * cur_trade_list["成交数量"]).sum() / (cur_trade_list["成交数量"].sum())
                    volume = cur_trade_list["成交数量"].sum()
                    trade_cost = cur_trade_list["交易费用"].sum()
                    direction = cur_trade_list["成交结果"].iloc[0]
                    
                    # 生成当日交易记录
                    cur_trade_record = pd.DataFrame(
                            {
                                "日期": [today],
                                "成交数量": [volume],
                                "平均成交价格": [average_price],
                                "交易费用": [trade_cost],
                                "方向": [direction] 
                            }
                        )
                    
                    # 今日建立底仓，生成交易记录文件
                    if not contract_info.loc[0, "底仓是否建立"]:
                        cur_trade_record.to_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_trade_record.csv", 
                                                index=False)
                        contract_info.loc[0, "底仓是否建立"] = True
                        contract_info.loc[0, "合约建仓日"] = today_
                        end_date = datetime.datetime.today() + datetime.timedelta(days=int(contract_info.loc[0, "合约期限（天）"]))
                        contract_info.loc[0, "合约结束日"] = end_date.strftime("%Y-%m-%d")
                        contract_info.to_csv(contract_info_path, index=False)
                    # 已有底仓，加入原交易记录文件
                    else:   
                        trade_record = pd.read_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_trade_record.csv",
                                                dtype={"日期": str})   
                        if today in trade_record["日期"].tolist():
                            trade_record.loc[trade_record["日期"]==today] = cur_trade_record.values  # 若当日已有交易记录，则对其进行替换
                        else:
                            trade_record = trade_record.append(cur_trade_record)  # 若当日无交易记录，则在底部新增一行
                        trade_record.to_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_trade_record.csv", 
                                            index=False)
                    
                else: # 当日无交易
                    continue
            
            st.success("所有合约交易记录更新完成！")
        
    with net_value:
        cur_time = datetime.datetime.now()
        if cur_time > datetime.datetime(cur_time.year, cur_time.month, cur_time.day, 15, 10):
            st.info("请确认已上传并更新各合约当日交易记录后，再点击下方按钮更新净值")
            if st.button("一键更新净值"):
                for contract_id in remaining_contract:
                    contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
                    contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
                    ticker = contract_info.loc[0, "代码"]
                    
                    if contract_info.loc[0, "底仓是否建立"]:    
                        cur_price, current_volume, pnl, last_volume, last_pnl, today_pnl, _ = contract_pnl_volume(contract_id, ticker)
                        cur_net_value_record = pd.DataFrame(
                            {
                                "日期": [today_],
                                "持仓股数": [current_volume],
                                "当日盈亏": [today_pnl],
                                "累计盈亏": [pnl]
                            }
                        )
                        try:
                            # 能读取到净值文件
                            net_value_record = pd.read_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_netvalue_record.csv",
                                                           dtype={"日期": str})   
                            if today_ in net_value_record["日期"].tolist():
                                net_value_record.loc[net_value_record["日期"]==today_] = cur_net_value_record.values  # 若当日已有净值记录，则对其进行替换
                            else:
                                net_value_record = net_value_record.append(cur_net_value_record)  # 若当日无净值记录，则在底部新增一行
                            net_value_record.to_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_netvalue_record.csv", 
                                                    index=False)
                        except:
                            # 无净值文件，说明是底仓建立日，直接写入创建净值文件
                            cur_net_value_record.to_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_netvalue_record.csv", 
                                                        index=False)
                st.success("净值更新成功！")
                        
        else:
            st.warning("请于每个交易日15点10分后更新净值！")
            st.button("一键更新净值", disabled=True)