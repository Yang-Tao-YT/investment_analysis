import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.genenrate_data import DataLoader

st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

if 'loader' not in st.session_state:
    trad = option_strategy.Trading()
    st.session_state['loader'] = loader =  DataLoader()
    st.session_state['trad'] = trad = option_strategy.Trading()

else:
    loader =  st.session_state['loader']
    trad =  st.session_state['trad']

st.title('tracking portfolio')

@st.cache_data
def load_position(axis = 1):
    dataframe = pd.read_csv('position.csv', encoding = 'utf-8-sig')
    dataframe = dataframe.replace({'义务' : -1, })
    dataframe = dataframe.set_index('合约代码')
    dataframe = dataframe.loc[~dataframe.index.isna()]
    return dataframe

dataframe = st.file_uploader('持仓文件',  type="xls")

if dataframe is not None:
    import xlrd
    dataframe = dataframe.getvalue()
    with open('position.txt', 'wb') as f:
        f.write(dataframe)
    # st.write(dataframe)
    dataframe = xlrd.open_workbook('position.txt', encoding_override='gbk')
    dataframe = pd.read_excel(dataframe, engine='xlrd')
    st.write(dataframe)
    dataframe.to_csv('position.csv', encoding = 'utf-8-sig', index = False)

if os.path.exists('position.csv'):
    dataframe = load_position(1)
    
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()
    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])
    
    trad.update_bar(data)
    trad.load_position(dataframe)
    profit = trad.profit()

    trad.update_position()
    st.write(trad.position)
    st.write(profit)

    if st.button('refresh'):
        pass
    debug = 1