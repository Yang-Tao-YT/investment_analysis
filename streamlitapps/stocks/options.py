
import streamlit as st
import numpy as np
import pandas as pd
import pathlib
import re
# import time
import sys
import os
from data.generate_data import AkShare
st.set_page_config(
page_title="investing analysis",  #页面标题
# page_icon=":rainbow:",  #icon
layout="wide", #页面布局
initial_sidebar_state="auto" #侧边栏
)

st.title('记录持仓')
sys.path.append(str(pathlib.Path().absolute()).split("/src")[0] )

# df = pd.DataFrame(columns=['持仓数量' , '平均成本'],)
# df.index.name = '名称'
# df.to_csv('stock_position.csv')
# def add_row(grid_table):
#     df = pd.DataFrame(grid_table['data'])

#     new_row = [['', 100, 0]]
#     df_empty = pd.DataFrame(new_row, columns=df.columns)
#     df = pd.concat([df, df_empty], axis=0, ignore_index=True)

#     # Save new df to sample.csv.
#     df.to_csv('stock_position.csv')

# from st_aggrid import AgGrid, GridOptionsBuilder
# from st_aggrid.shared import  ColumnsAutoSizeMode


# dfssss = GridOptionsBuilder.from_dataframe(df)
# dfssss.configure_default_column(editable=True)
# grid_options = dfssss.build()

# dfssss=AgGrid(df, 
#                 gridOptions=grid_options,
#             #   editable =True, 
#             #   width = 1, 
#                 columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW
#                 )

# st.button("加行", on_click=add_row, args=[dfssss])



# if st.button("清除", ):
#     df = dfssss['data'].loc[dfssss['data']['持仓数量'] != 0]
#     df.to_csv('stock_position.csv')
#     st.experimental_rerun()

df = pd.read_csv('stock_position.csv', index_col=0, dtype=object)
# df['名称'] = df['名称'].astype(str)
df.index = df.index.astype(str)
df['平均成本'] = df['平均成本'].astype(float)
df['持仓数量'] = df['持仓数量'].astype(float)
df['持仓成本'] = df['持仓数量'] * df['平均成本']

df_k = AkShare().current_k_etf_dongcai()
df_k = df_k.set_index('代码')
df_k.index = df_k.index.astype(str)
df = df.reset_index().set_index('代码').join(df_k.drop('名称', axis=1), lsuffix='old')
df['市值'] = df['持仓数量'] * df['最新价']
df['持仓收益']  = df['市值'] - df['持仓成本']
df = df.reset_index().set_index('名称')
df.loc['统计', ['持仓成本' , '持仓收益']] = df[ ['持仓成本' , '持仓收益']].sum()

df = df[[ '代码','持仓数量'  , '平均成本', '最新价', '持仓成本' , '市值','持仓收益']]
# df['持仓成本'] = df['持仓成本'].astype(float)
edited_df = st.data_editor(df, 
                    num_rows='dynamic',
                    column_config={
                    "持仓收益": st.column_config.NumberColumn(
                        disabled = True
                        # format="$%d",
                    )
                },
                # hide_index=True
                width=3000
                )
# st.write(edited_df)
if st.button("计算", ):
    
    edited_df['持仓成本'] = edited_df['持仓数量'] * edited_df['平均成本']
    edited_df = edited_df.loc[edited_df['持仓数量'] != 0]
    edited_df.to_csv('stock_position.csv')
    st.experimental_rerun()
# st.write(dfssss['data'])