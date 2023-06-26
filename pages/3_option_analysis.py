import streamlit as st
import pandas as pd
import option_strategy
from data.genenrate_data import DataLoader
from strategy.宽跨 import StrangleOption
import pandas as pd
import streamlit as st

from basic import rename_dataframe
from stock_strategy import StockIndex, stock_etf_hist_dataloader
from utils.calculate import calculate_mergin


st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

# @ st.cache_data(ttl=600)  # 👈 Added this
def return_stockindex(symbol, setting : dict = None):
    '''下载历史数据'''
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader(symbol)
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    #转换成stockindex的形式
    stockindex.set_am(hist)
    setattr(stockindex, 'origin_data', hist.set_index('date')) 
    # update setting
    if setting is not None:
        stockindex.update_setting(setting=setting)
    return stockindex

if 'loader' not in st.session_state:
    trad = option_strategy.Trading()
    st.session_state['loader'] = loader =  DataLoader()
    st.session_state['trad'] = trad = option_strategy.Trading()

else:
    loader =  st.session_state['loader']
    trad =  st.session_state['trad']

cols = st.columns([1,1,1])
with cols[0]:
    st.title('tracking portfolio') ; 
    if st.button('refresh'):pass
    
    # price
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()

    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])
    price = return_stockindex('sh510300', None)
    data = data.loc[data.名称.str.startswith('300')]

    days = data['剩余日'].unique() ; days.sort()
    
    #select 
    days = st.selectbox('剩余日' , days) #剩余日
    account_amount = st.number_input('成本', value = 700000)

    data = data.loc[data['剩余日'] ==  days]

with cols[1]:
    #select contracts
    calls = data.loc[data.名称.str.contains('购')].sort_values('行权价')
    puts =  data.loc[data.名称.str.contains('购')].sort_values('行权价')
    contracts = pd.concat( StrangleOption().chose_contract(data, price.origin_data['close'][-1]))
    contracts.insert(3, '比例', contracts['执行价'] / price.origin_data['close'][-1] - 1)

with cols[0]:
    _price = price.origin_data; _price['前收盘'] = _price['close'].shift()
    contracts = calculate_mergin(contracts, _price.iloc[-1, :])
    combine_margin = max(contracts['保证金']) + min(contracts['最新价'])
    st.write(contracts)
    returns = (contracts["最新价"].sum() - 0.0006) / combine_margin 
    st.info(f'收益率为{returns * 100} %')
    st.info(f'收益为{round(returns * account_amount / 10000, 3)} 万')