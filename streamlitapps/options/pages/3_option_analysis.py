import streamlit as st
import pandas as pd
import option_strategy
from data.generate_data import DataLoader
from strategy.option.宽跨 import StrangleOption
from strategy.option.spred import  Spred
import pandas as pd
import streamlit as st
from streamlitapps.apps_utils import display_returns_scale
from utils.basic import name_2_symbol, rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader
from utils.calculate import calculate_mergin


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

tabs = st.tabs(['宽跨' , '宽跨定制', '看涨价差', '看涨价差定制'])


with tabs[0]:
    cols = st.columns([1,1,1])
         

    with cols[2]:
        display_returns_scale(bar)

    with cols[1]:
        #select contracts
        calls = data.loc[data.名称.str.contains('购')].sort_values('行权价')
        puts =  data.loc[data.名称.str.contains('沽')].sort_values('行权价')
        call = st.selectbox('call',[None]  + list(calls.行权价), )
        put = st.selectbox('put',[None]  + list(puts.行权价))
        # var
        # call = 3.4

        contracts = pd.concat( StrangleOption().chose_contract(data, price.origin_data['close'][-1]))

        if call is not None:
            contracts.loc[contracts.名称.str.contains('购'), calls.loc[calls.行权价 == call].rename(columns = {'行权价' : '执行价'}).columns] = list( calls.loc[calls.行权价 == call].squeeze())

        if put is not None:
            contracts.loc[contracts.名称.str.contains('沽'), puts.loc[puts.行权价 == put].rename(columns = {'行权价' : '执行价'}).columns] = list( puts.loc[puts.行权价 == put].squeeze())


        contracts.insert(3, '比例', contracts['执行价'] / price.origin_data['close'][-1] - 1)

    with cols[1]:
        _price = price.origin_data; _price['前收盘'] = _price['close'].shift()
        contracts = calculate_mergin(contracts, _price.iloc[-1, :])
        combine_margin = max(contracts['保证金']) + min(contracts['最新价'])
        st.write(contracts)
        returns = (contracts["最新价"].sum() - 0.0006) / combine_margin 

        # 计算risk指标
        contracts['pecentage'] = 1
        risk_indicators = contracts[['实际杠杆比率' ,  'Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']].T.dot(
            contracts['pecentage']) 
        risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] =(
            risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] * -1
        )

        st.dataframe(risk_indicators)
        
        if contracts_amount != 0:
            st.info(f'收益为{round((contracts["最新价"].sum() - 0.0006) * contracts_amount, 3)} 万')
            st.info(f'使用保证金{round(combine_margin * contracts_amount, 3)} 万')
        st.info(f'收益率为{returns * 100} %')
        st.info(f'收益为{round(returns * account_amount / 10000, 3)} 万')


with tabs[1]:
        '''多个选择'''
        contracts = pd.concat( StrangleOption().chose_contract(data, price.origin_data['close'][-1]))
        _call = contracts.loc[contracts.名称.str.contains('购')]

        _put = contracts.loc[contracts.名称.str.contains('沽')]

        #select calls and puts
        call = st.multiselect('calls', list(calls.行权价), default = _call.执行价.squeeze())
        put = st.multiselect('puts', list(puts.行权价), default = _put.执行价.squeeze())
        #var
        # call = [3.4, 3.446]
        # put = [3.5, 3.6]
        if len(call) > 1 or _call.执行价.squeeze() not in call:
            _call =  data.loc[(data.名称.str.contains('购')) &( data.行权价.isin(call))]

        if len(put) > 1 or _put.执行价.squeeze() not in put:
            _put =  data.loc[(data.名称.str.contains('沽')) &( data.行权价.isin(put))]

        contracts =  pd.concat([_call.rename(columns = {'行权价' : '执行价'}), _put.rename(columns = {'行权价' : '执行价'})])

        contracts['pecentage'] = 1

        contracts.loc[contracts.名称.str.contains('沽'), 'pecentage'] = (contracts.loc[contracts.名称.str.contains('沽'), 'pecentage']/
                                                                      contracts.loc[contracts.名称.str.contains('沽'), 'pecentage'].sum()) * 1
        contracts.loc[contracts.名称.str.contains('购'), 'pecentage'] = (contracts.loc[contracts.名称.str.contains('购'), 'pecentage']/
                                                                      contracts.loc[contracts.名称.str.contains('购'), 'pecentage'].sum()) * 1

        contracts.insert(3, '比例', contracts['执行价'] / price.origin_data['close'][-1] - 1)

        contracts.loc[contracts.名称.str.contains('购'), '期权类型'] = 'C' ; contracts.loc[contracts.名称.str.contains('沽'), '期权类型'] = 'P'

        _price = price.origin_data; _price['前收盘'] = _price['close'].shift()
        contracts = calculate_mergin(contracts, _price.iloc[-1, :])
        combine_margin = max(contracts['保证金']) + min(contracts['最新价'])
        st.write(contracts)
        returns = (contracts["最新价"].dot(contracts['pecentage']) - 0.0006) / combine_margin 
        # 计算risk指标
        risk_indicators = contracts[['实际杠杆比率' ,  'Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']].T.dot(
            contracts['pecentage']) 
        risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] =(
            risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] * -1
        )
        st.dataframe(risk_indicators)

        contracts_amount = st.number_input('手数', value = 0, key='123')
        if contracts_amount != 0:
            st.info(f'收益为{round((contracts["最新价"].dot(contracts["pecentage"]) - 0.0006) * contracts_amount, 3)} 万')
            st.info(f'使用保证金{round(combine_margin * contracts_amount, 3)} 万')

        st.info(f'收益率为{returns * 100} %')
        st.info(f'收益为{round(returns * account_amount / 10000, 3)} 万')

with tabs[2]:
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
