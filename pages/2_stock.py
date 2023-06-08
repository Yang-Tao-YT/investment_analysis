import copy
import datetime
from pyecharts import options as opts
from pyecharts import charts
import pandas as pd
import streamlit as st
import numpy as np
from basic import name_2_symbol, rename_dataframe, Bar
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



@ st.cache_data(ttl=600)  # 👈 Added this
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

@st.cache_data(ttl=600)    # 👈 Added this
def plot_bar(x_value, value):
        bar = charts.Bar()
        bar.add_xaxis(x_value )
        bar.add_yaxis('区间数量',value)
        
        bar.set_global_opts(
            xaxis_opts=opts.AxisOpts(
                name='bin值'
            ),
            yaxis_opts=opts.AxisOpts(
                name = '数量值'
            ))
        bar = bar.render_embed()
        return bar


def return_index(indicator):
    if len(indicator) > 0:
        result = {}
        for i in indicator:
             _temp = eval(f'stockindex_copy.{i}().iloc[:, :]')
             _temp = _temp.set_index(0)
             result[i] = _temp.squeeze()
        
        
        return pd.concat(result, axis = 1)
    return eval(f'stockindex_copy.{indicator[0]}().iloc[-20:, :]')

def check_date(x):
    return ((pd.to_datetime(x).day_of_week == 2) and ( 21<=pd.to_datetime(x).day)) or (pd.to_datetime(x).day == 1)

def history_return_hist(days):
        df : pd.DataFrame
        pct : pd.Series
        df = stockindex_copy.origin_data.close.copy()
        # df.loc[list(pd.Series(df.index).apply(check_date))]
        df.index  = pd.to_datetime(df.index)
        df = df.loc[pd.to_datetime('2012-06-01' ): ]

        if st.checkbox('exclude extra'):
            df = df.loc[pd.to_datetime('2016-03-01' ): ]

        df = df.to_frame()
        df['month'] = pd.to_datetime(df.index).strftime('%Y-%m')
        
        def returns(x):
            index = list( x.index)

            x = x.loc[:pd.date_range(index[0],index[-1],freq='WOM-4WED')[0]]

            if x.shape[0] < days:
                _days = 0
            else:
                _days = -1 * days
            return x['close'].iloc[-1]/ x['close'].iloc[_days] - 1
        
        df = df.loc[:datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, 1)]
        if datetime.datetime.now().day < 20 :
            df = df.loc[ : (pd.to_datetime(datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)) - 
                        pd.Timedelta(days = 1))]
        df = df.groupby('month').apply(returns)
        # df = df.pct_change(days)
        value = pd.cut(df, 20).value_counts().sort_index()
        # value.sum()
        pct = value / df.dropna().shape[0] 
        pct = pct.to_frame()
        pct['count'] = value
        pcts_col = st.columns([1.5,1,3]) 
        with pcts_col[0]: st.dataframe(pct)
        with pcts_col[1]: 
            area = st.number_input('returns', 0.0, 100.0, 7.5, 0.1) / 100
            st.info(f'区域面积为{df.loc[(df < area) &(df > -1 * area)].shape[0]/ df.shape[0]}')
            st.info(f'上涨区域面积为{df.loc[(df < area)].shape[0]/ df.shape[0]}')
            st.info(f'下跌区域面积为{df.loc[(df > -1 * area)].shape[0]/ df.shape[0]}')
        x_value = [ f'{round(i.left,2)}-{round(i.right,2)}' for i in value.index ]
        
        value= value.tolist() 

        bar = plot_bar(x_value, value)

        with pcts_col[2]: 
            components.html(bar,width=1800, height=500)

        #display specific returns area
        specific_returns = st.number_input('specific_returns', 0.0, 100.0, 7.5, 0.1) / 100
        spreturn_cols = st.columns(3)
        with spreturn_cols[0]:
            st.write(df.loc[(df < -1 * specific_returns)])
        with spreturn_cols[1]:
            st.write(df.loc[(df > specific_returns)])
        # with spreturn_cols[2]:
        #     st.write(df.loc[(df > specific_returns) | (df < -1 * specific_returns)])
with cols[0]:
    with st.container():
        symbol = st.selectbox('code', list( name_2_symbol.keys()))
        symbol = name_2_symbol[symbol]
        # indicator
        indicator =  st.multiselect('indicator', ['risk' , 'rsi'], default= 'risk')
        # indicator = ['risk' , 'rsi']

with cols[1]:
    window = st.number_input('window' , step=1,value=21)
    if window != 0:
        setting = {'ma_window' : window}
    else:
        setting = None

    placeholder = st.empty()
    with placeholder.container():
        
        _columns = st.columns(2)

        with _columns[0]:
            stockindex = return_stockindex(symbol, setting=setting)
            stockindex_copy = copy.deepcopy(stockindex)
            stockindex_copy.origin_data['pre_close'] = stockindex_copy.origin_data.close.shift(1)
            bar = Bar().update_bar(stockindex_copy.origin_data.iloc[-1,:])
            result = return_index(indicator=indicator)
            st.write(bar)
            st.write(result.iloc[::-1, :])
            
        with _columns[1]:
            price = pd.Series(range(int(bar.close * 10 * 0.87),int(bar.close * 10 * 1.13)))/10
            price.index = price
            mulit = st.number_input('倍数', 1.0 , 2.0, 1.0157)
            st.write((price / bar.close - 1) * 100)
            price = np.round(price / mulit, 3)
            price.index = price
            st.write( (price/ bar.close - 1) * 100)

    rerun = st.button('rerun')

if st.button('plot'):
    st.session_state.plot = 1 - st.session_state.plot

tabs = st.tabs(['risk', 'history return'])
with tabs[1]:
    # history returns hist
    # print('yongletab1')
    days = st.number_input('days',0,60,21)
    if 1:
        history_return_hist(days)
    pass
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

if st.button('refresh'):
    st.cache_data.clear()