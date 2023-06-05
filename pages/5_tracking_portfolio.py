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

cols = st.columns([1,1,1])
with cols[0]:
    st.title('tracking portfolio') ; 
    if st.button('refresh'):pass
    
@st.cache_data
def load_position(axis = 1):
    dataframe = pd.read_csv('position.csv', encoding = 'utf-8-sig', index_col=0)
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
    st.dataframe(dataframe)
    dataframe.to_csv('position.csv', encoding = 'utf-8-sig', index = False)

if os.path.exists('position.csv'):
    dataframe = load_position(1)
    # price
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()

    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])
    
    # greek
    greek = loader.current_risk_em()

    hs300 = loader.current_hs300risk_sz_em()
    greek = pd.concat([greek, hs300])
    greek = greek.set_index('期权代码')
    greek = greek.apply(pd.to_numeric,args=['ignore'])


    trad.update_bar(data)
    trad.update_greek(greek)
    trad.load_position(dataframe)
    profit = trad.profit()

    trad.update_position()
    st.write(trad.position)
    st.info(f"浮动盈亏 {profit}")
    st.info(f"potential earning : {trad.position.loc['统计', ['合约市值','浮动盈亏']].sum().round(2)}")
    st.info(f"earned pctg : {round(profit / trad.position.loc['统计', ['合约市值','浮动盈亏']].sum() * 100,3)} %")


    debug = 1

if st.button('clear'):
    st.cache_data.clear()