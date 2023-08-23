import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.generate_data import DataLoader
from utils.basic import rename_dataframe, Bar
from strategy.stock_strategy import StockIndex, stock_etf_hist_dataloader
from strategy.stock_strategy import return_stockindex, return_indicator
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

def dataframe_display(df):
    st.dataframe(df,
                 column_config={
        "比例": st.column_config.NumberColumn(
            "行权涨跌幅%",
            help="The price of the product in USD",
            min_value=0,
            max_value=1000,
            # step=1,
            format="%.2f %%",
        ),
        "比例绝对值": st.column_config.NumberColumn(
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
    } , height=df.shape[0] * 43)


@st.cache_data
def load_position(axis = 1):
    # dataframe = pd.read_csv('position.csv', encoding = 'utf-8-sig', index_col=0)
    # dataframe = dataframe.replace({'义务' : -1, '权利' : 1})
    # dataframe = dataframe.set_index('合约代码')
    # dataframe1 = dataframe.loc[~dataframe.index.isna()].copy()

    dataframe1 = pd.DataFrame()
    if os.path.exists('huataiposition.csv'):
        try:
            dataframe = pd.read_csv('huataiposition.csv', index_col=0)
        except:
            dataframe = pd.read_csv('huataiposition.csv', index_col=0, encoding='gbk')

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

        dataframe1 = pd.concat([dataframe1, dataframe], axis = 0).sort_index()

        dataframe1.index = dataframe1.index.astype(str)
    return dataframe1


    
if os.path.exists('position.csv') or os.path.exists('huataiposition.csv'):
    dataframe = load_position(1)
    dataframe['under'] = dataframe.合约名称.str[:6]
    # 筛选
    filters = st.selectbox('underlying', [None] + [*dataframe.under.unique()])
    if filters is not None:
        dataframe = dataframe.loc[dataframe.under == filters]

    months = dataframe.合约名称.str.split('月', expand=True)[0].str[-1].unique()
    filters2 = st.selectbox('months', [None] + [*months])
    # filters2 = 9
    if filters2 is not None:
        dataframe = dataframe.loc[dataframe.合约名称.str.contains(f'{filters2}月')]

    cols2  = st.columns(3)
    with cols2[0]:
        contract_split = st.checkbox('按合约')
    with cols2[1]:
        type_split = st.checkbox('按类型')
    with cols2[2]:
        if_edit = st.checkbox('edit')
    # price
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()

    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])

    # greek
    greek = loader.current_risk_em()
    # hs300 = loader.current_hs300risk_sz_em()
    # greek = pd.concat([greek, hs300])
    greek = greek.set_index('期权代码')
    greek = greek.apply(pd.to_numeric,args=['ignore'])


    trad.update_bar(data)
    trad.update_greek(greek)
    
    if if_edit:
        dataframe = st.data_editor(dataframe)
    trad.load_position(dataframe)
    profit = trad.profit()

    trad.update_position()

    # get price of underlying asset
    hs300_price = return_stockindex('sh510300', None).origin_data.iloc[-1,:]['close']
    zz500_price = return_stockindex('sh510500', None).origin_data.iloc[-1,:]['close']
    shs300_price = return_stockindex('sz159919', None).origin_data.iloc[-1,:]['close']
    # calculate scale
    test = trad.position.iloc[:-1].copy()
    test.loc[test.合约名称.str.contains('510300'), '行权价'] = test.loc[test.合约名称.str.contains('510300') , '行权价'] / hs300_price - 1
    test.loc[test.合约名称.str.contains('159919') , '行权价'] = test.loc[ test.合约名称.str.contains('159919') , '行权价'] / shs300_price - 1
    
    test.loc[test.合约名称.str.contains('500ETF')| test.合约名称.str.contains('510500') , '行权价'] = test.loc[test.合约名称.str.contains('500ETF')| test.合约名称.str.contains('510500') , '行权价'] / zz500_price - 1
    trad.position.insert(4, '比例', list((test['行权价'] * 100).values) + [None]) 
    trad.position.insert(4, '比例绝对值', list(abs(test['行权价'] * 100).values) + [None]) 

    if contract_split:
        #按不同合约标的展示
        unders = trad.position.under.dropna().unique()
        for _under in unders:
            temp_df = trad.position.loc[trad.position.under == _under]
            temp_df.loc['统计',['浮动盈亏', '合约市值', '涨跌额','Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ] = (
                            temp_df[ ['浮动盈亏', '合约市值', '涨跌额', 'Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ].sum(axis = 0))
            dataframe_display(temp_df)
        dataframe_display(trad.position.loc['统计'].to_frame().T)
    elif type_split:
        for _under in  ['购', '沽']:
            temp_df = trad.position.drop('统计')
            temp_df = temp_df.loc[temp_df.合约名称.str.contains(_under)]
            temp_df.loc['统计',['浮动盈亏', '合约市值', '涨跌额','Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ] = (
                            temp_df[ ['浮动盈亏', '合约市值', '涨跌额', 'Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ].sum(axis = 0))
            dataframe_display(temp_df)
        dataframe_display(trad.position.loc['统计'].to_frame().T)

    else:
        dataframe_display(trad.position)
    st.info(f"浮动盈亏 {profit}")
    st.info(f"potential earning : {round (trad.position.loc['统计', ['合约市值','浮动盈亏']].sum(), 2)}")
    st.info(f"earned pctg : {round(profit / trad.position.loc['统计', ['合约市值','浮动盈亏']].sum() * 100,3)} %")
    st.info(f"盈亏比例 : {round(trad.position.loc['统计', '涨跌额'] / 120 / 10000,3) }%")


    debug = 1

if st.button('clear'):
    st.cache_data.clear()
    st.session_state.clear()

dataframe = st.file_uploader('持仓文件',  type="csv")

if  st.button('上传'):
    if dataframe is not None :
        dataframe = pd.read_csv(dataframe, dtype=object)
        st.dataframe(dataframe)
        dataframe.to_csv('huataiposition.csv', index = False)