from data.generate_data import AkShare
from utils.basic import name_2_symbol

for key, value in name_2_symbol.items():
    symbol = value
    data = AkShare().download_stock_etf_hist_k(symbol, if_save=True)
    print(symbol)
    print('----------------')
