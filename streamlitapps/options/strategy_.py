import streamlit as st
import pandas as pd
from strategy.option.宽跨 import StrangleOption
from streamlitapps.apps_utils import display_returns_scale
from utils.calculate import calculate_mergin
from strategy.option.spred import  Spred

def strangle(data, bar, price, contracts_amount, account_amount):
    cols = st.columns([1,1])
         

    with cols[1]:
        display_returns_scale(bar)

    with cols[0]:
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

    with cols[0]:
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

    return calls, puts


def multichoice_strangle(data, price, contracts_amount, account_amount):
        calls = data.loc[data.名称.str.contains('购')].sort_values('行权价')
        puts =  data.loc[data.名称.str.contains('沽')].sort_values('行权价')

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



def _spred(price, data):
        
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
        contracts_type = st.selectbox('期权类型', ['购' , '沽'], index = 1)
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

        # 计算risk指标
        contracts['pecentage'] = [1, -1]
        risk_indicators = contracts[['实际杠杆比率' ,  'Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']].T.dot(
            contracts['pecentage']) 
        risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] =(
            risk_indicators[['Delta' ,  'Gamma'  ,  'Vega'  ,   'Rho',   'Theta']] * -1
        )

    with tabs2_cols[0]:
        st.write(risk_indicators)

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
