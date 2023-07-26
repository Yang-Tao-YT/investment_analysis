import streamlit as st
import os
import pandas as pd
import plotly.graph_objs as go
from utils import format_money, contract_pnl_volume, stock_last_price, highlight_rows
import config
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="总览", layout="wide")

with open('AppFrontEnd/auth.yaml') as file:
    auth = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    auth['credentials'],
    auth['cookie']['name'],
    auth['cookie']['key'],
    auth['cookie']['expiry_days']
)
_, authentication_status, _ = authenticator.login('Login', 'main')
st.session_state.authentication_status = authentication_status

if st.session_state.authentication_status:
    st.markdown("## 总览")
    st.write("---")
    
    if st.sidebar.button("刷新总市值和盈亏"):
        st.experimental_rerun()

    # 获取当前存续合约信息
    remaining_contract = os.listdir(f"{config.grid_trading_doc_path}/remaining")
    all_position = {
        "contract_id": [],
        "代码": [],
        "名称": [],
        "行业": [],
        "昨日持仓股数": [],
        "当前持仓股数": [],
        "持仓市值": [],
        "名义市值": [],
        "持仓均价": [],
        "累计盈亏": [],
        "当日盈亏": []
    }
    unpositioned_contract = {
        "contract_id": [],
        "行业": [],
        "当前价格/期初价格": []
    }
    
    num_positioned_contract, num_unpositioned_contract = 0, 0
    for contract_id in remaining_contract:
        contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
        contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
        
        base_position_state = contract_info.loc[0, "底仓是否建立"]
        ticker = contract_info.loc[0, "代码"]
        name = contract_info.loc[0, "名称"]
        industry = contract_info.loc[0, "行业"]
        nominal_market_value = contract_info.loc[0, "合约本金"]
        strike_price = contract_info.loc[0, "期初价格"]
        
        if base_position_state:
            num_positioned_contract += 1
            
            # 持仓量，累积盈亏，持仓市值
            cur_price, current_volume, pnl, last_volume, last_pnl, today_pnl, cur_average_price = contract_pnl_volume(contract_id, ticker)
            current_position = current_volume * cur_price
            
            all_position["contract_id"].append(contract_id)
            all_position["代码"].append(ticker)
            all_position["名称"].append(name)
            all_position["昨日持仓股数"].append(int(last_volume))
            all_position["当前持仓股数"].append(int(current_volume))
            all_position["持仓市值"].append(int(current_position))
            all_position["名义市值"].append(nominal_market_value)
            all_position["持仓均价"].append(cur_average_price * current_volume)
            all_position["累计盈亏"].append(round(pnl))
            all_position["当日盈亏"].append(round(today_pnl))
            all_position["行业"].append(industry)
        else:
            num_unpositioned_contract += 1
            cur_price, _ = stock_last_price(ticker)
            
            unpositioned_contract["contract_id"].append(contract_id)
            unpositioned_contract["行业"].append(industry)
            unpositioned_contract["当前价格/期初价格"].append(cur_price/strike_price)
            
    all_position_df = pd.DataFrame(all_position)
    unpositioned_contract_df = pd.DataFrame(unpositioned_contract)
    unpositioned_contract_df.sort_values("当前价格/期初价格", inplace=True)

    st.markdown("### 持仓盈亏总览")
    st.markdown(f"##### 已建仓合约数量：{num_positioned_contract}")
    
    check_col, df_col = st.columns([1, 10])
    display_df = all_position_df[["contract_id", "名称", "行业", "昨日持仓股数", "当前持仓股数", "持仓市值", "当日盈亏", "累计盈亏"]]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    total_position = all_position_df["持仓市值"].sum()
    total_pnl = all_position_df["累计盈亏"].sum()
    today_pnl = all_position_df["当日盈亏"].sum()
    total_nominal_mv = all_position_df["名义市值"].sum()
    
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.metric("持仓总市值", value=format_money(total_position))
    with col_2:
        st.metric("名义总市值", value=format_money(total_nominal_mv))
    with col_3:
        st.metric("总盈亏", value=format_money(total_pnl), delta=f"{today_pnl:.2f}", delta_color="inverse")
    
    industry_portion = all_position_df.groupby("行业")["持仓市值"].sum() / total_position
    
    st.markdown("##### 行业持仓分布")
    fig = go.Figure(data=go.Pie(labels=industry_portion.index, values=industry_portion.values))
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    
    st.markdown("### 未建仓合约")
    st.markdown(f"##### 未建仓合约数量：{num_unpositioned_contract}")
    
    st.dataframe(unpositioned_contract_df, use_container_width=True, hide_index=True)
            

    
    
        
        
    