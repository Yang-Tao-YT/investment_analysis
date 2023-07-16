import streamlit as st
import pandas as pd
import option_strategy
from data.generate_data import DataLoader
from strategy.option.宽跨 import StrangleOption
from strategy.option.spred import  Spred
import pandas as pd
import streamlit as st
from streamlitapps.options.strategy_ import strangle, multichoice_strangle
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
symbol = st.selectbox('code',['中证500' , '沪深300'], index = 1)
symbol = name_2_symbol[symbol]

# 读取标的行情
price = return_stockindex(symbol, None)
price.origin_data['pre_close'] = price.origin_data.close.shift(1)
bar = Bar().update_bar(price.origin_data.iloc[-1,:])

if symbol == 'sh510300':
    data = data.loc[data.名称.str.startswith('300')]
elif symbol == 'sh510500':
    data = data.loc[data.名称.str.startswith('500')]

#添加risk指标
data = data.join(greek.set_index('期权代码')[['实际杠杆比率' ,  'Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']])
days = data['剩余日'].unique() ; days.sort()

#读取剩余日
days = st.selectbox('剩余日' , days, index = 1) #剩余日
account_amount = st.number_input('成本/万', value = 70) * 10000
contracts_amount = st.number_input('手数', value = 0)

data = data.loc[data['剩余日'] ==  days].copy()

tabs = st.selectbox('类型', ['宽跨' , '宽跨定制', '看涨价差', '看涨价差定制'])


if tabs ==  '宽跨':
    strangle(data, bar, price, contracts_amount, account_amount)

if tabs ==  '宽跨定制':
    '''多个选择'''
    multichoice_strangle(data, price, contracts_amount, account_amount)

if tabs ==  '看涨价差':
    #读取剩余日
    spred = Spred()
    tabs2_cols = st.columns(3)
    # days = st.selectbox('剩余日' , days, index = 0) #剩余日
    # account_amount = st.number_input('成本/万', value = 70) * 10000
    # contracts_amount = st.number_input('手数', value = 0)

    # data = data.loc[data['剩余日'] ==  days].copy()
    # with cols[2]:
    #     display_returns_scale(bar, '23')

    with tabs2_cols[1]:
        #select contracts types
        contracts_type = st.selectbox('期权类型', ['购' , '沽'])
        #select contracts
        spred_contracts =  data.loc[data.名称.str.contains(contracts_type)].sort_values('行权价')
        up = st.selectbox('up', [None] + list(spred_contracts.行权价), index=0)
        down = st.selectbox('down', [None] + list(spred_contracts.行权价), index=0)
        # var
        # up = 3.7
        # down = 3.6

        contracts = pd.concat( spred.chose_contract(data, spred_type=contracts_type.replace('购', 'C').replace('沽', 'P'),current_price= price.origin_data['close'][-1]))

        if up is not None:
            contracts.loc[contracts.index[0], 
                          spred_contracts.loc[spred_contracts.行权价 == up].rename(columns = {'行权价' : '执行价'}
                                                              ).columns] = list( spred_contracts.loc[spred_contracts.行权价 == up].squeeze())

        if down is not None:
            contracts.loc[contracts.index[1], 
                          spred_contracts.loc[spred_contracts.行权价 == down].rename(columns = {'行权价' : '执行价'}
                                                           ).columns] = list( spred_contracts.loc[spred_contracts.行权价 == down].squeeze())

        contracts.insert(3, '比例', contracts['执行价'] / price.origin_data['close'][-1] - 1)

    with tabs2_cols[1]:
        # 计算保证金和收益
        margin = spred.margin(contracts['执行价'].iloc[1], contracts['执行价'].iloc[0], contracts['最新价'].iloc[1], contracts['最新价'].iloc[0])
        st.write(contracts)
        if contracts_type == '购':

            returns = spred.bullspread_call(
                    K1 = contracts['执行价'].iloc[1],
                    K2 = contracts['执行价'].iloc[0],
                    C1 = contracts['最新价'].iloc[1],
                    C2 = contracts['最新价'].iloc[0],
                    P0 = price.origin_data['close'][-1],
                    P0_index=price.origin_data['close'][-1],
                    Pt_index= contracts['执行价'].iloc[0] * 1.1,
                    N1=1,
                    N2=1,
                    N_underlying=1
            )[-1]
            returns = returns / margin

            equanpoint = spred.equant_point_call(                    
                        K1 = contracts['执行价'].iloc[1],
                        # K2 = contracts['执行价'].iloc[0],
                        C1 = contracts['最新价'].iloc[1],
                        C2 = contracts['最新价'].iloc[0],)
            
            stats = pd.Series({'收益率' : returns * 100, '均衡价' : equanpoint , '均衡率' : equanpoint / price.origin_data['close'][-1] - 1})

            st.write(stats)
        else:
            returns = spred.bullspread_put(
                    K1 = contracts['执行价'].iloc[1],
                    K2 = contracts['执行价'].iloc[0],
                    P1 = contracts['最新价'].iloc[1],
                    P2 = contracts['最新价'].iloc[0],
                    P0 = price.origin_data['close'][-1],
                    P0_index=price.origin_data['close'][-1],
                    Pt_index= contracts['执行价'].iloc[0] * 1.1,
                    N1=1,
                    N2=1,
                    N_underlying=1
            )[-1]
            returns = returns / margin

            equanpoint = spred.equant_point_put(                    
                        # K1 = contracts['执行价'].iloc[1],
                        K2 = contracts['执行价'].iloc[0],
                        P1 = contracts['最新价'].iloc[1],
                        P2 = contracts['最新价'].iloc[0],)
            
            stats = pd.Series({'收益率' : returns * 100, 
                               '均衡价' : equanpoint , 
                               '均衡率' : equanpoint / price.origin_data['close'][-1] - 1,
                               '保证金' : margin},)

            st.write(stats)
