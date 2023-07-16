import streamlit as st
import pandas as pd
from strategy.option.宽跨 import StrangleOption
from streamlitapps.apps_utils import display_returns_scale
from utils.calculate import calculate_mergin

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