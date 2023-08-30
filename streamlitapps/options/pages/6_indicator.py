import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.generate_data import DataLoader
from strategy.factor_cross_section import main as cross_section
import datetime
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
def calcualte_indicator(x, setting = None, end_date = None):
    # 传换成st的缓存格式
    result = cross_section(if_save=False, setting = setting, end_date = end_date)
    indicator = result.indicator
    bar = result.bar
    percent = result.percent
    percent = {k: str(round(v * 100, 2)) + '%' for k,v in percent.items()}
    last_indicator = result.last_indicator

    df = pd.DataFrame({'risk' : indicator, 
                       '当日涨跌' : percent, 
                       'quantile' : result.quantile, 
                       'bar' : bar,
                       'last_indicator' : last_indicator}).sort_values('risk')

    df['risk_diff'] = df['risk'] - df['last_indicator']
    df = df.drop('last_indicator', axis=1)
    return df

# def colored_text(var):
#     return f'<span style="color:{color}">{text}</span>'

window = st.number_input('window', value=0)

if window == 0:
    setting = None
else:
    setting = {'ma_window' : window}

st.write(setting)

end_date = st.date_input('end_date', value= pd.to_datetime('today') 
                        #  - pd.Timedelta(days = 1)
                         )
if __name__ == '__main__':

    df = calcualte_indicator(1, setting, end_date = end_date)
    st.dataframe(df.style.background_gradient(cmap = 'Blues', axis = 0, subset = (  'risk' )))



    if st.sidebar.button('run'):
        st.cache_data.clear()
        st.session_state.clear()
        
        st.experimental_rerun()