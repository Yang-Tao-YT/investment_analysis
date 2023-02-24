import streamlit as st
from stock_strategy import StockIndex, stock_etf_hist_dataloader,barloader
from option_strategy import Calculation
import datetime
import copy
import pandas as pd
from basic import name_2_symbol,rename_dataframe

today = datetime.datetime.today().date()
test  = [i for i in st.columns(2)]


with test[0]:
    symbol = st.selectbox('code', list( name_2_symbol.keys()))

symbol = name_2_symbol[symbol]

with test[1]:
    window = st.slider('window', 0, 130, 21)
# with st.sidebar:
#     window = st.slider('window', 0, 130, 60)

@st.cache_data()  # 👈 Added this
def return_stockindex(symbol):
    st.write('rerun')
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader(symbol)
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    stockindex.set_am(hist)
    return stockindex

col2 =  [i for i in st.columns(2)]

with col2[0]:
    placeholder = st.empty()
    with placeholder.container():

        stockindex = return_stockindex(symbol)
        stockindex_copy = copy.deepcopy(stockindex)
        # update today bar
        if stockindex.am.date[-1] < today:
            bar = barloader(symbol=symbol)
            stockindex_copy.update_bar(bar)

        # numpy to dataframe
        df = pd.Series(stockindex_copy.am.close_array, index=stockindex_copy.am.date)
        df = df.iloc[-400:]
        # cal result
        result = Calculation.vol(df = df, window = window)
        st.write(result.iloc[::-1])

    if st.button('plot'):
        with col2[1]:
            # result = result.set_index(0)
                result.index.name = 'index'
                st.line_chart(result)

if st.button('rerun'):
    st.experimental_rerun()