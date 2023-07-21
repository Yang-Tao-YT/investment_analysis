import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.generate_data import DataLoader
from strategy.factor_cross_section import main as cross_section
st.set_page_config(
page_title="investing analysis",  #页面标题
page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

import sys
import pathlib
sys.path.append(str(pathlib.Path().absolute()).split("/src")[0] )

@st.cache_data
def calcualte_indicator(x, setting = None):
    # 传换成st的缓存格式
    result = cross_section(if_save=False, setting = setting)
    indicator = result.indicator
    bar = result.bar
    percent = result.percent
    percent = {k: str(round(v * 100, 2)) + '%' for k,v in percent.items()}

    df = pd.DataFrame({'risk' : indicator, '当日涨跌' : percent, 'quantile' : result.quantile, 'bar' : bar}).sort_values('risk')

    # df = pd.DataFrame([indicator, bar, result.quantile], index = ['risk', '当日涨跌', 'quantile']).T.sort_values('risk')
    return df



window = st.number_input('window', value=0)

if window == 0:
    setting = None
else:
    setting = {'ma_window' : window}

st.write(setting)
st.dataframe(calcualte_indicator(1, setting))



if st.sidebar.button('run'):
    st.cache_data.clear()
    st.session_state.clear()
    
    st.experimental_rerun()