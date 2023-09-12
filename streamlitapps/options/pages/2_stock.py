import sys
print(sys.path)
from utils.basic import name_2_symbol, rename_dataframe, Bar
import copy
import datetime
import os

from pyecharts import options as opts
from pyecharts import charts
import pandas as pd

import numpy as np

from strategy.stock_strategy import return_stockindex, return_indicator
from strategy.factor_cross_section import calculate_indicator


import streamlit.components.v1 as components
from utils.plot import plot_kline_volume_signal_adept
import streamlit as st

st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)


today = datetime.datetime.today().date()
cols  = st.columns(2)

debug = 0
if debug:
    st.session_state = {}

if 'init' not in st.session_state:
    st.session_state['init'] = 1
    st.session_state['plot'] = 0
    st.session_state['risk_quantile'] = 0

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

def check_date(x):
    return ((pd.to_datetime(x).day_of_week == 2) and ( 21 <= pd.to_datetime(x).day)) or (pd.to_datetime(x).day == 1)

def history_return_hist(days):
        df : pd.DataFrame
        pct : pd.Series
        df = stockindex.origin_data.close.copy()

        df.index  = pd.to_datetime(df.index)
        df = df.loc[pd.to_datetime('2010-06-01'): ]


        df = df.to_frame()
        df['month'] = pd.to_datetime(df.index).strftime('%Y-%m')
        
        def returns(x):
            index = list( x.index)

            if len(pd.date_range(index[0],index[-1],freq='WOM-4WED')) == 0:
                return None
            x = x.loc[:pd.date_range(index[0],index[-1],freq='WOM-4WED')[0]]

            if x.shape[0] < days:
                _days = 0
            else:
                _days = -1 * days
            return x['close'].iloc[-1]/ x['close'].iloc[_days] - 1
        
        df = df.loc[:pd.date_range(df.index[0],df.index[-1],freq='WOM-4WED')[-1]]

        df = df.groupby('month').apply(returns)

        # 在历史上按月份做统计
        month_states = df.to_frame('returns').copy() ; month_states.index.name = 'date'
        month_states['month'] = pd.to_datetime(month_states.index).month

        # if 1:
        if st.checkbox('exclude extra'):
            #剔除极端收益
            def _outlier(df):
                df = df.loc[(df.returns != df.returns.min()) & (df.returns != df.returns.max())]
                return df
            
            month_states = month_states.groupby('month').apply(_outlier).droplevel(0)

        month_col = st.columns(2)
        stats = pd.DataFrame()
        stats['median'] = month_states.groupby('month').median()
        stats['mean'] = month_states.groupby('month').mean()
        stats['min'] = month_states.groupby('month').min()
        stats['max'] = month_states.groupby('month').max()
        stats['std'] = month_states.groupby('month').std()
        
        with month_col[0]:
            st.dataframe(stats)
        
        with month_col[1]:
        # 展示特定年份
            target_month = st.number_input('特定月份', value = 0)
            if target_month != 0:
                target_stats = month_states.loc[month_states.month == target_month]
                st.bar_chart(target_stats['returns'])

                value = pd.cut(target_stats['returns'], 4).value_counts().sort_index() # 切分后求数量
                x_value = [ f'{round(i.left,2)}-{round(i.right,2)}' for i in value.index ]
                value= value.tolist() 
                components.html( plot_bar(x_value, value),width=1800, height=500)

            target_year = st.number_input('特定年份', value = 0)
            if target_year != 0:
                target_stats = month_states.loc[ pd.to_datetime(month_states.index).year == target_year]
                st.bar_chart(target_stats['returns'])

                # value = pd.cut(target_stats['returns'], 4).value_counts().sort_index() # 切分后求数量
                # x_value = [ f'{round(i.left,2)}-{round(i.right,2)}' for i in value.index ]
                # value= value.tolist() 
                # components.html( plot_bar(x_value, value),width=1800, height=500)

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

with cols[0]:
    #select symbol
    with st.container():
        symbol = st.selectbox('code', list( name_2_symbol.keys()), index= len(list( name_2_symbol.keys()))-1)
        symbol = name_2_symbol[symbol]
        # indicator
        indicator =  st.multiselect('indicator', ['risk' , 'rsi'], default= 'risk')


with cols[1]:
    #select window
    window = st.number_input('window' , step=1,value=0)
    if_comeback = st.checkbox('反弹趋势', value=True)
    if window != 0:
        setting = {'ma_window' : window}
    else:
        setting = None

    placeholder = st.empty()
    with placeholder.container():
        
        _columns = st.columns(2)
        end_date = st.date_input('end_date', value= pd.to_datetime('today') 
                                #  - pd.Timedelta(days = 1)
                                 )
        with _columns[0]:
            _result = calculate_indicator(symbol, 
                                          setting=setting, 
                                          if_return_stockindex=True, 
                                          if_analysis_risk_after_first_comeback=if_comeback,
                                          end_date = end_date,
                                          if_analysis_down_risk=True,)
            
            bar = _result['bar']
            result = _result['indicator']
            st.write(bar)
            st.write(result.iloc[::-1, :])
            stockindex = _result['stockindex']

        if if_comeback:
            with cols[0]:
                st.write(_result['comeback'])
        with _columns[1]:
            price = pd.Series(range(int(bar.close * 10 * 0.87),int(bar.close * 10 * 1.13)))/10
            price.index = price
            st.write((price / bar.close - 1) * 100)
            if st.checkbox('倍数'):
                mulit = st.number_input('倍数', 1.0 , 2.0, 1.0157)
                price = np.round(price / mulit, 3)
                price.index = price
                st.write( (price/ bar.close - 1) * 100)

    rerun = st.button('rerun')

if st.button('plot'):
    st.session_state['plot'] = 1 - st.session_state['plot']

tabs = st.tabs(['risk', 'history return', 'risk_quantile'])

with tabs[1]:
    # 计算历史收益分布
    days = st.number_input('days',0,60,21)
    if 1:
        history_return_hist(days)
    pass

with tabs[2]:
    # 计算risk收益分布
    if st.button('risk_quantile'):
        st.session_state['risk_quantile'] = 1 - st.session_state['risk_quantile']
        
    if st.session_state['risk_quantile']:
        result = result.dropna()
        # np.histogram(result, density=True)[0]

        st.write((result < result.iloc[-1]).sum() / result.shape[0])
        value = pd.cut(result.squeeze(), 100).value_counts().sort_index() # 切分后求数量
        x_value = [ f'{round(i.left,2)}-{round(i.right,2)}' for i in value.index ]
        value= value.tolist() 
        components.html( plot_bar(x_value, value),width=1800, height=500)

    if 'down_risk' in _result:
        st.write(_result['down_risk']['summary'])
        st.write(_result['down_risk']['returns'])

if st.session_state['plot'] or debug:
# if 1:
        start = st.date_input('start', datetime.date(2023,1,1))
        end = st.date_input('end', pd.to_datetime('today'))

        
        st.write(stockindex.origin_data.loc[:end, 'close'][-1]/ stockindex.origin_data.loc[start:, 'open'][0] - 1)
        # pic_col = st.columns([5,1])
        # stockindex.origin_data['risk'] = list(stockindex.risk()[1].squeeze())
        stockindex.origin_data = stockindex.origin_data.join(result)
        result = plot_kline_volume_signal_adept(stockindex.origin_data, indicator )
        # result = result.set_index(0)
        # result.index.name = 'index'
        # st.line_chart(result)
        result = result.render_embed()
        # with pic_col[0]:
        st.write('##### plotting')

        components.html(result,width=1800, height=3000)

        # with pic_col[1]:




if rerun:
    # return_stockindex.clear()
    st.experimental_rerun()

if st.button('refresh'):
    st.cache_data.clear()