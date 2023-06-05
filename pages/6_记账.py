import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.genenrate_data import DataLoader

st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

def to_num(x):
    try:
        return float(x)
    except:
        return x
    
with st.form("my-form", clear_on_submit=True):

    check_sales_file = st.file_uploader('流水')

    submitted = st.form_submit_button("UPLOAD!")
    
    if (submitted):
        st.write("UPLOADED!")
        check_sales = pd.read_csv(check_sales_file, dtype=object,encoding='gbk', skiprows=7)
        check_sales.to_csv(f'Position.csv', index = False,encoding='gbk')

tabs = st.tabs(['修改','下载'])

with tabs[0]:
    if os.path.exists(f'Position.csv'):
        check_sales = pd.read_csv(f'Position.csv', dtype=object,encoding='gbk')
        # check_sales.to_csv(f'Position.csv', index = False)
        check_sales = st.experimental_data_editor(check_sales, height = 1000, num_rows = 'dynamic')
        if st.button('save Position file'):
            check_sales.to_csv(f'Position.csv', index = False)

    else:
        st.warning('no position')

with tabs[1]:
    if os.path.exists(f'Position.csv'):
        check_sales = pd.read_csv(f'Position.csv', dtype=object,encoding='gbk')
        # check_sales.to_csv(f'Position.csv', index = False)
        st.download_button('position', 
                            data = check_sales.astype(object).to_csv(index=0),
                            file_name=f'position.csv',
                            mime='csv',
                           )


