import streamlit as st
import pandas as pd
import time
import os
import option_strategy
from data.genenrate_data import DataLoader
from strategy.factor_cross_section import main as cross_section
st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)



result = cross_section(if_save=False)
indicator = result.indicator
bar = result.bar
st.dataframe(pd.DataFrame([indicator, bar], index = ['risk', '当日涨跌']).T.sort_values('risk'))

if st.button('run'):
    st.experimental_rerun()