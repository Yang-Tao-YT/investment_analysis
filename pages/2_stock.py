import copy
import datetime

import pandas as pd
import streamlit as st

from basic import name_2_symbol, rename_dataframe
from stock_strategy import StockIndex, barloader, stock_etf_hist_dataloader

import streamlit.components.v1 as components
from utils.plot import plot_kline_volume_signal_adept

st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)


today = datetime.datetime.today().date()
cols  = st.columns(2)


if 'init' not in st.session_state:
    st.session_state.init = 1
    st.session_state.plot = 0



@ st.cache_data()  # 👈 Added this
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


def return_index(indicator):
    if len(indicator) > 0:
        result = {}
        for i in indicator:
             _temp = eval(f'stockindex_copy.{i}().iloc[:, :]')
             _temp = _temp.set_index(0)
             result[i] = _temp.squeeze()
        
        
        return pd.concat(result, axis = 1)
    return eval(f'stockindex_copy.{indicator[0]}().iloc[-20:, :]')
    
with cols[0]:
    with st.container():
        symbol = st.selectbox('code', list( name_2_symbol.keys()))
        symbol = name_2_symbol[symbol]
        # indicator
        indicator =  st.multiselect('indicator', ['risk' , 'rsi'], default= 'risk')
        # indicator = ['risk' , 'rsi']

with cols[1]:
    window = st.number_input('window' , step=1,value=0)
    if window != 0:
        setting = {'ma_window' : window}
    else:
        setting = None

    placeholder = st.empty()
    with placeholder.container():
        
        stockindex = return_stockindex(symbol, setting=setting)
        
            
        stockindex_copy = copy.deepcopy(stockindex)
        if stockindex.am.date[-1] < today:
            bar = barloader(symbol=symbol)
            
            stockindex_copy.update_bar(bar)

        result = return_index(indicator=indicator)
        st.write(barloader(symbol=symbol))
        st.write(result.iloc[::-1, :])
    
    rerun = st.button('rerun')

if st.button('plot'):
    st.session_state.plot = 1 - st.session_state.plot

if st.session_state.plot:
# if 1:
        # stockindex.origin_data['risk'] = list(stockindex.risk()[1].squeeze())
        stockindex.origin_data = stockindex.origin_data.join(result)
        result = plot_kline_volume_signal_adept(stockindex.origin_data, indicator )
        # result = result.set_index(0)
        # result.index.name = 'index'
        # st.line_chart(result)
        result = result.render_embed()
        st.write('##### plotting')
        components.html(result,width=1800, height=3000)
        
if rerun:
    return_stockindex.clear()
    st.experimental_rerun()