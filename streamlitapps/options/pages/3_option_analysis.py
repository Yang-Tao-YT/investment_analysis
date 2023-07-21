import streamlit as st
import pandas as pd
import option_strategy
from data.generate_data import DataLoader
from strategy.option.宽跨 import StrangleOption

import pandas as pd
import streamlit as st
from streamlitapps.options.strategy_ import strangle, multichoice_strangle, _spred
from utils.basic import name_2_symbol, rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader



st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

# @st.cache_data
def obtain_option_data(hax):
        # 获取option价格
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()
    greek = loader.current_risk_em()

    return data, hs300, greek
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

st.title('portfolio construction') 

if st.button('refresh'):pass

# 获取option价格
data ,hs300 ,greek = obtain_option_data(1)

data = pd.concat([data, hs300])
data = data.set_index('代码')
data = data.apply(pd.to_numeric,args=['ignore'])
# 选择标的
symbol_chs = st.selectbox('code',['中证500' , '沪深300', '上证50', '创业板指', '科创50'], index = 1)
symbol = name_2_symbol[symbol_chs]

# 读取标的行情
price = return_stockindex(symbol, None)
price.origin_data['pre_close'] = price.origin_data.close.shift(1)
bar = Bar().update_bar(price.origin_data.iloc[-1,:])

if symbol == 'sh510300':
    data = data.loc[data.名称.str.startswith('300')]
elif symbol == 'sh510500':
    data = data.loc[data.名称.str.startswith('500')]
elif symbol_chs == '上证50':
    data = data.loc[data.名称.str.startswith('50ETF')]
elif symbol_chs == '创业板指':
    data = data.loc[data.名称.str.startswith('创业板')]
elif symbol_chs == '科创50':
    data = data.loc[data.名称.str.startswith('科创50')]

#添加risk指标
data = data.join(greek.set_index('期权代码')[['实际杠杆比率' ,  'Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']])
days = data['剩余日'].unique() ; days.sort()

#选择剩余日，或者设置手数，或者设置成本
set_cols = st.columns(4)
with set_cols[0]:
    days = st.selectbox('剩余日' , days, index = 1) #剩余日
with set_cols[1]:
    account_amount = st.number_input('成本/万', value = 70) * 10000
with set_cols[2]:
    contracts_amount = st.number_input('手数', value = 0)
with set_cols[3]:
    fees = st.number_input('fees / 万', value = 3.0) / 10000

data = data.loc[data['剩余日'] ==  days].copy()

tabs = st.selectbox('类型', ['宽跨' , '宽跨定制', '看涨价差', '看涨价差定制', '多个功能'])

st.write('-' * 20)
if tabs ==  '宽跨':
    strangle(data, bar, price, contracts_amount, account_amount, fees)

if tabs ==  '宽跨定制':
    '''多个选择'''
    multichoice_strangle(data, price, contracts_amount, account_amount, fees)

if tabs ==  '看涨价差':
    #读取剩余日
    _spred(price, data, contracts_amount, fees)

if tabs ==  '多个功能':
    mulfun = st.columns(2)
    with mulfun[0]:
        mulfun_tabs1 = st.selectbox('类型', ['宽跨' , '宽跨定制', '看涨价差'], key='mulfun0')
        if mulfun_tabs1 ==  '宽跨':
            strangle(data, bar, price, contracts_amount, account_amount, fees)

        if mulfun_tabs1 ==  '宽跨定制':
            '''多个选择'''
            multichoice_strangle(data, price, contracts_amount, account_amount, fees)

        if mulfun_tabs1 ==  '看涨价差':
            #读取剩余日
            _spred(price, data, contracts_amount, fees)

    with mulfun[1]:
        mulfun_tabs1 = st.selectbox('类型', ['宽跨' , '宽跨定制', '看涨价差'], key='mulfun1', index = 2)
        if mulfun_tabs1 ==  '宽跨':
            strangle(data, bar, price, contracts_amount, account_amount, fees)

        if mulfun_tabs1 ==  '宽跨定制':
            '''多个选择'''
            multichoice_strangle(data, price, contracts_amount, account_amount, fees)

        if mulfun_tabs1 ==  '看涨价差':
            #读取剩余日
            _spred(price, data, contracts_amount, fees)

