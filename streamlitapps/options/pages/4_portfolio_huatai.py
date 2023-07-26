import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.generate_data import DataLoader
from utils.basic import rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader

st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

if 'loader' not in st.session_state:
    st.session_state['loader'] = loader =  DataLoader()
    st.session_state['trad'] = trad = option_strategy.Trading()

else:
    loader =  st.session_state['loader']
    trad =  st.session_state['trad']

cols = st.columns([1,1,1])
with cols[0]:
    st.title('tracking portfolio') ; 
    if st.button('refresh'):pass

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

@st.cache_data
def load_position(axis = 1):
    dataframe = pd.read_csv('huataiposition.csv', index_col=0)
    dataframe = dataframe.dropna(axis=1)
    def trans(x:str):
        if isinstance(x, str):
            x = x.strip('=')
            x = x.strip('"')
        return x
    dataframe = dataframe.applymap(trans)
    dataframe = dataframe.replace({'义务' : -1, '权利' : 1, })
    dataframe = dataframe.rename(columns={'定价' : '定价价栳n','开仓均价' :'成本价',
                                   '净仓' : '实际持仓'})
    dataframe = dataframe.astype({'成本价' : float, '实际持仓' : int,})

    dataframe['持仓类型'] = 1 ; dataframe.loc[dataframe['实际持仓'] < 0 , '持仓类型'] = -1
    dataframe['实际持仓'] = abs(dataframe['实际持仓'])

    dataframe = dataframe.set_index('合约编码')
    dataframe = dataframe.loc[~dataframe.index.isna()]
    return dataframe

dataframe = st.file_uploader('持仓文件',  type="csv")

if  st.button('上传'):
    if dataframe is not None :
        dataframe = pd.read_csv(dataframe, dtype=object)
        st.dataframe(dataframe)
        dataframe.to_csv('huataiposition.csv', index = False)

if os.path.exists('huataiposition.csv'):
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

    # get price of underlying asset
    hs300_price = return_stockindex('sh510300', None).origin_data.iloc[-1,:]['close']
    zz500_price = return_stockindex('sh510500', None).origin_data.iloc[-1,:]['close']

    # calculate scale
    test = trad.position.iloc[:-1].copy()
    test.loc[test.合约名称.str.contains('300ETF'), '行权价'] = test.loc[test.合约名称.str.contains('300ETF'), '行权价'] / hs300_price - 1
    test.loc[test.合约名称.str.contains('500ETF'), '行权价'] = test.loc[test.合约名称.str.contains('500ETF'), '行权价'] / zz500_price - 1
    trad.position.insert(4, '比例', list((test['行权价'] * 100).values) + [None]) 

    if '行权盈亏' in trad.position.columns:
        trad = trad.position.drop(['行权价值' ,'行权盈亏', '备兑数量','可用'], axis = 1)
    st.dataframe(trad.position,
                 column_config={
        "比例": st.column_config.NumberColumn(
            "行权涨跌幅%",
            help="The price of the product in USD",
            min_value=0,
            max_value=1000,
            # step=1,
            format="%.2f %%",
        ),
        "涨跌幅": st.column_config.NumberColumn(
            "涨跌幅%",
            help="The price of the product in USD",
            min_value=0,
            max_value=1000,
            # step=1,
            format="%.2f %%",
        )
    } , height=trad.position.shape[0] * 50)
    st.info(f"浮动盈亏 {profit}")
    st.info(f"potential earning : {trad.position.loc['统计', ['合约市值','浮动盈亏']].sum().round(2)}")
    st.info(f"earned pctg : {round(profit / trad.position.loc['统计', ['合约市值','浮动盈亏']].sum() * 100,3)} %")


    debug = 1

if st.button('clear'):
    st.cache_data.clear()
    st.session_state.clear()