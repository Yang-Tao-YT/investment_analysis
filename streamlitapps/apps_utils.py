
import streamlit as st
import pandas as pd
import numpy as np

def display_returns_scale(bar, key1 = 'bat'):
    price = pd.Series(np.arange(int(bar.close * 10 * 0.87),int(bar.close * 10 * 1.13), step=1))/10
    price.index = price
    st.write((price / bar.close - 1) * 100)
    if st.checkbox('倍数', key = key1 + 'scale'):
        mulit = st.number_input('倍数', 1.0 , 2.0, 1.0157, key = key1 + 'scale1')
        price = np.round(price / mulit, 3, key = key1 + 'scale2')
        price.index = price
        st.write( (price/ bar.close - 1) * 100)