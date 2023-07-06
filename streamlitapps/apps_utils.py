from utils.basic import name_2_symbol, rename_dataframe, Bar
import streamlit as st
import pandas as pd
import numpy as np

def display_returns_scale(bar):
    price = pd.Series(np.arange(int(bar.close * 10 * 0.87),int(bar.close * 10 * 1.13), step=1))/10
    price.index = price
    st.write((price / bar.close - 1) * 100)
    if st.checkbox('倍数'):
        mulit = st.number_input('倍数', 1.0 , 2.0, 1.0157)
        price = np.round(price / mulit, 3)
        price.index = price
        st.write( (price/ bar.close - 1) * 100)