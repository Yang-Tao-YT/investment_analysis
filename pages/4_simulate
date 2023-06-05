import streamlit as st
import pandas as pd
import time
import option_strategy
from data.genenrate_data import DataLoader
# from tkinter import messagebox
# import win32api
st.title('tracking simulate')
code = st.selectbox('code', ['300etf_2212',  '500etf_2212', '300etf_2212_longvol'])
# code = '500etf_2212'

if 'loader' not in st.session_state:
    trad = option_strategy.Trading()
    st.session_state['loader'] = loader =  DataLoader()
    st.session_state['trad'] = trad = option_strategy.Trading()

else:
    loader =  st.session_state['loader']
    trad =  st.session_state['trad']


cal = st.button('计算净值收益')
cal = True

def generate():
    if '500' in code:
        data = loader.current_option_bar_shangjiao(expire_date= code[code.find('_') + 1 : code.find('_') + 5])
    else:
        # loader.inital_akshare()
        data = loader.current_option_bar_zhongjing_sina(f'io{code[code.find("_") + 1 : code.find("_") + 5]}')
    data = option_strategy.rename_dataframe(data)
    data = data.apply(pd.to_numeric,args=['ignore'])
    
    trad.update_bar(data)
    trad.load_balance(code)

    returns, profit = trad.profit()
    return returns, profit

# generate()    
if cal:
    returns, profit =generate()

    st.write(    
        trad.balance(),
        trad.cost(),)

    st.write(
        f'returns of account is {returns * 100:.2f}% ',
        f"net account is {trad.net_account()} net profit is {profit}"
        )
    stra = option_strategy.Strategy().butterfly(trad.position, 'list', percentage=3750)
    st.dataframe(stra[0])

    # messagebox.showinfo('hi')
    # win32api.MessageBox(0, 'hi')

start = st.button('重复读取')
close = st.button('结束')


placeholder = st.empty()
count = 0

while start and not close:
    returns, profit =generate()
    with placeholder.container():
        st.write(    
            trad.balance(),
            trad.cost(),)
        st.write(
            f'returns of account is {returns * 100:.2f}% ',
            f"net account is {trad.net_account()} net profit is {profit}"
            )
        st.write(f"⏳ {count } seconds have passed")
    count+= 5
    # placeholder.empty()
    time.sleep(5)
