from __future__ import annotations

import QuantLib as ql
import config as config
import streamlit as st
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import locale
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from ..Backtest.snowball_backtest import snowball_valuation
from ..Hedge.snowball_dynamic_delta_hedge import SnowballHedger
from ..Pricing.quantlib_pricing import calculate_coupon_snowball, snowball_pricing_mcm_mp

def last_n_business_days(current_date: str, 
                         n: int):
    """
    获取当前日期之前第n个交易日
    """
    cur_date = ql.Date(current_date, "%Y-%m-%d")
    count = 0
    while count < n:
        cur_date = cur_date - ql.Period("1d")
        if ql.China().isBusinessDay(cur_date):
            count += 1

    return cur_date.to_date()

@st.cache_data(ttl=30000, show_spinner=False)
def read_stock_price():
    price_data = pd.read_csv(config.stock_close_price_path, index_col=0)
    col = []
    for i in price_data.columns:
       col.append(i[:6])
    price_data.columns = col
    
    return price_data

@st.cache_data(ttl=30000, show_spinner=False)
def read_etf_price():
    price_data = pd.read_csv(config.etf_close_price_path, index_col=0)
    col = []
    for i in price_data.columns:
       col.append(i[:6])
    price_data.columns = col
    
    return price_data

def snowball_backtest(price_series: pd.DataFrame | pd.Series,
                      window: int = 240,
                      step: int = 1,
                      **kwargs):
    res_dim0 = len(price_series) - window + 1
    result_values = list()
    my_bar = st.progress(0)
    for i in range(0, res_dim0, step):
        current_path = price_series[i:i + window].squeeze()
        result_values.append(snowball_valuation(sample_path=current_path, **kwargs))
        my_bar.progress((i + step) / (step + (res_dim0-1) - (res_dim0-1) % step))
    st.info("回测完成！")

    return pd.DataFrame(result_values,
                        index=price_series.index[np.arange(0, res_dim0, step)],
                        columns=["Profit", "KO Date", "KI Date"])
    
@st.cache_data(show_spinner=False)
def snowball_hedger(price_series, risk_free_rate, sigma_window, principal, 
                    constant_sigma, pre_define_sigma, trade_cost, num_paths,
                    ki, ko,
                    start_date, end_date, 
                    choice, exp_upper_limit = None, exp_down_limit = None):
    sb = SnowballHedger(price_series=price_series.squeeze(),
                        risk_free_rate = risk_free_rate,
                        sigma_window=f"{sigma_window}y",
                        pre_define_sigma=pre_define_sigma,
                        trade_cost=trade_cost,
                        ki=ki,
                        ko=ko,
                        ko_lock=0,
                        start_date=start_date,
                        maturity_date=end_date,
                        initial_position=principal,
                        num_paths=num_paths)
    if choice == 0:
        backtest_record = sb.backtest_engine(method="fixed",
                                             constant_sigma=constant_sigma)
    else:
        backtest_record = sb.backtest_engine(method="exposure",
                                             constant_sigma=constant_sigma,
                                             exp_upper_limit=exp_upper_limit,
                                             exp_down_limit=exp_down_limit)
        
    metrics = sb.metrics_backtest(backtest_record)

    return backtest_record, metrics

@st.cache_data(show_spinner=False)
def cal_coupon(**kwargs):
    return calculate_coupon_snowball(**kwargs)

@st.cache_data(show_spinner=False)
def cal_delta(current_price, return_price=False, **kwargs):
    h = 0.1
    current_price = round(current_price / kwargs["strike_price"] * 100, 2)
    kwargs["principal"] = kwargs["strike_price"] = 100  # 一份雪球合约对应一只个股
    if return_price:
        p_plus, p, p_minus = snowball_pricing_mcm_mp(current_price=[current_price + h,
                                                                    current_price,
                                                                    current_price - h], 
                                                     **kwargs)        
    else:
        p_plus, p_minus = snowball_pricing_mcm_mp(current_price=[current_price + h,
                                                                 current_price - h], 
                                                  **kwargs)

    # 差分法计算delta
    delta = (p_plus - p_minus) / (2 * h)
    
    return (p, delta) if return_price else delta

def snowball_delta_list(min_price: int,
                        max_price: int,
                        h: float = 0.1,
                        num_paths: int = 300000,
                        **kwargs):
    kwargs["num_paths"] = num_paths
    strike_price = kwargs["strike_price"]
    kwargs["principal"] = kwargs["strike_price"] = 100

    price_range = np.linspace(min_price, max_price, 80)  # 价格序列
    price_list = np.zeros(len(price_range) * 3)
    for i in range(len(price_range)):
        temp_price = round(price_range[i], 2)
        temp_price = round(temp_price / strike_price * 100, 2)
        price_list[3*i:3*i+3] = temp_price - h, temp_price, temp_price + h  # 差分法计算delta，插入变动价格

    value_list = snowball_pricing_mcm_mp(current_price=price_list, **kwargs)  # 计算所有价格
    res = dict()

    for i in range(len(price_range)):
        p_plus, _, p_minus = value_list[3*i+2], value_list[3*i+1], value_list[3*i]  # 提取价格
        delta = (p_plus - p_minus) / (2 * h)  # 计算delta
        res[round(price_range[i], 2)] = delta
        
    return res
        
def read_real_time(last_trading_day=False):
    today = datetime.datetime.today().strftime("%Y%m%d")
    today_real_time_path = f"{config.real_time_path}/{today}.csv"
    if last_trading_day:
        prev_trading_day = last_n_business_days(datetime.datetime.today().strftime("%Y-%m-%d"), n=1).strftime("%Y%m%d")  # 上一交易日
        real_time_data = pd.read_csv(f"{config.real_time_path}/{prev_trading_day}.csv", index_col=0)
        return real_time_data
    while True:
        try:
            real_time_data = pd.read_csv(today_real_time_path, index_col=0)
            break
        except FileNotFoundError:
            prev_trading_day = last_n_business_days(datetime.datetime.today().strftime("%Y-%m-%d"), n=1).strftime("%Y%m%d")  # 上一交易日
            real_time_data = pd.read_csv(f"{config.real_time_path}/{prev_trading_day}.csv", index_col=0)
            break
        except:
            continue
    
    return real_time_data

def stock_last_price(ticker):
    while True:
        try:    
            real_time_data = read_real_time()
            cur_price = real_time_data.loc[ticker, "最新价"]
            pct_change = real_time_data.loc[ticker, "涨跌幅"]
            
            return cur_price, pct_change
        except:
            if len(real_time_data.columns) != 0:
                return 0, 0
            continue

def format_money(res: float):
    locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
    currentcy_str = locale.currency(res, grouping=True)
    if res < 0:
        currentcy_str = currentcy_str[0] + "-" + currentcy_str[1:-1]
    
    return currentcy_str[:-3]

@st.cache_data(show_spinner=False)
def get_stock_name(ticker):
    stock_name_df = pd.read_excel(config.stock_name_path)[["证券代码", "证券简称"]]
    stock_name_df["证券代码"] = stock_name_df["证券代码"].apply(lambda x: x[:6])
    stock_name = stock_name_df.loc[stock_name_df["证券代码"] == ticker, "证券简称"].squeeze()
    
    return stock_name

@st.cache_data(show_spinner=False)
def get_industry_name(ticker):
    stock_industry_df = pd.read_excel(config.stock_industry_path, index_col=0)
    stock_industry_df["TICKER_SYMBOL"] = stock_industry_df["TICKER_SYMBOL"].apply(lambda x:x[:6])
    industry = stock_industry_df.loc[stock_industry_df["TICKER_SYMBOL"]==ticker, "一级行业"].squeeze()
    
    return industry

def get_contract_color_name(contract_id):
    contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
    contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
    base_state = contract_info.loc[0, "底仓是否建立"]
    if not base_state:
        return "🟩" + contract_id
    clear_state = contract_info.loc[0, "一键清仓"]
    if clear_state:
        return "🟥" + contract_id
    stop_state = contract_info.loc[0, "暂停对冲"]
    if stop_state:
        return "🟨" + contract_id
    if not clear_state:
        return "🟦" + contract_id

def stop_update3():
    if "update3" in st.session_state:
        st.session_state.update3 = False

def pnl_contract(contract_id, cur_price, date=datetime.datetime.today()):
    trade_record = pd.read_csv(f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_trade_record.csv", dtype={"日期": str})
    
    trade_record["日期"] = pd.to_datetime(trade_record["日期"], format="%Y%m%d")
    trade_record = trade_record.set_index("日期")
    trade_record = trade_record.loc[:date]
    
    if len(trade_record) == 0:
        return 0, 0, 0
    
    trade_record["多空"] = np.where(trade_record["方向"]=="买入成交", 1, -1)
    current_volume = (trade_record["成交数量"] * trade_record["多空"]).sum()
    total_trade_cost = trade_record["交易费用"].sum()

    if current_volume != 0:
        average_current_price = (trade_record["成交数量"] * trade_record["平均成交价格"] * trade_record["多空"]).sum() / current_volume
        pnl = (cur_price - average_current_price) * current_volume - total_trade_cost
    else:
        pnl = (trade_record["成交数量"] * trade_record["平均成交价格"] * trade_record["多空"]).sum() - total_trade_cost
        
    return current_volume, pnl, average_current_price + total_trade_cost / current_volume

def update_contract_boundary(contract_info, modified_contract_info):
    old_ki, old_ko, old_ki_price, old_ko_price, old_strike_price = contract_info[["敲入线", "敲出线", "敲入价格", "敲出价格", "期初价格"]].squeeze()
    new_ki, new_ko, new_ki_price, new_ko_price, new_strike_price = modified_contract_info[["敲入线", "敲出线", "敲入价格", "敲出价格", "期初价格"]].squeeze()
    ki_state, ki_price_state, ko_state, ko_price_state = (new_ki == old_ki), (new_ki_price == old_ki_price), (new_ko == old_ko), (new_ko_price == old_ko_price)
    
    if ki_state ^ ki_price_state:
        if ki_price_state:
            new_ki_price = new_ki * new_strike_price
        else:
            new_ki = new_ki_price / new_strike_price
    else:
        if ki_state:
            new_ki_price = new_ki * new_strike_price
        else:
            pass

    if ko_state ^ ko_price_state:
        if ko_price_state:
            new_ko_price = new_ko * new_strike_price
        else:
            new_ko = new_ko_price / new_strike_price
    else:
        if ko_state:
            new_ko_price = new_ko * new_strike_price
        else:
            pass
    
    modified_contract_info[["敲入线", "敲出线", "敲入价格", "敲出价格", "期初价格"]] = new_ki, new_ko, new_ki_price, new_ko_price, new_strike_price
    
    return modified_contract_info

def contract_pnl_volume(contract_id, ticker):
    real_time_data = read_real_time()  # 实时数据
    history_data = read_real_time(last_trading_day=True)  # 历史数据
    
    ticker_data = real_time_data.loc[ticker]
    history_ticker_data = history_data.loc[ticker]
    
    # 提取价格
    cur_price = ticker_data["最新价"]  # 实时价格
    last_price = history_ticker_data["最新价"]  # 昨收
    
    # 持仓量，累积盈亏，持仓市值
    current_volume, pnl, cur_average_price = pnl_contract(contract_id, cur_price)
    yesterday = datetime.datetime.today() - timedelta(days=1)
    last_volume, last_pnl, _ = pnl_contract(contract_id, last_price, yesterday)
    
    today_pnl = pnl - last_pnl  # 当日盈亏
    
    return cur_price, current_volume, pnl, last_volume, last_pnl, today_pnl, cur_average_price

def price_contract(contract_id):
    real_time_data = read_real_time()
    contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
    contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
    
    # 提取合约参数
    ticker = contract_info.loc[0, "代码"]
    principal = contract_info.loc[0, "合约本金"]
    coupon_rate = contract_info.loc[0, "票息率"]
    strike_price = contract_info.loc[0, "期初价格"]
    ki = contract_info.loc[0, "敲入线"]
    ko = contract_info.loc[0, "敲出线"]
    start_date = contract_info.loc[0, "合约建仓日"]
    end_date = contract_info.loc[0, "合约结束日"]
    sigma = contract_info.loc[0, "定票息年化波动率"]

    cur_price = real_time_data.loc[ticker, "最新价"]
    
    snowball_kwargs = {
        "strike_price": strike_price,
        "principal": principal,
        "risk_free_rate": 0.03,
        "coupon_rate": coupon_rate,
        "sigma": sigma,
        "ki": ki,
        "ko": ko,
        "start_date": start_date,
        "maturity_date": end_date,
        "evaluation_date": datetime.datetime.today().strftime("%Y-%m-%d"),
        "num_paths":300000,
        "num_cores": 20,
    } 

    price, delta = cal_delta(cur_price, return_price=True, **snowball_kwargs)
    price = price * principal / 100
    
    return price, delta

@st.cache_data(show_spinner=False, ttl=30000)
def contract_delta_list(contract_id):
    """
    计算一份合约的delta曲线
    """
    real_time_data = read_real_time()
    contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
    contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
    
    # 提取合约参数
    ticker = contract_info.loc[0, "代码"]
    principal = contract_info.loc[0, "合约本金"]
    coupon_rate = contract_info.loc[0, "票息率"]
    strike_price = contract_info.loc[0, "期初价格"]
    ki = contract_info.loc[0, "敲入线"]
    ko = contract_info.loc[0, "敲出线"]
    start_date = contract_info.loc[0, "合约建仓日"]
    end_date = contract_info.loc[0, "合约结束日"]
    sigma = contract_info.loc[0, "定票息年化波动率"]

    cur_price = real_time_data.loc[ticker, "最新价"]
    snowball_kwargs = {
        "strike_price": strike_price,
        "principal": principal,
        "risk_free_rate": 0.03,
        "coupon_rate": coupon_rate,
        "sigma": sigma,
        "ki": ki,
        "ko": ko,
        "start_date": start_date,
        "maturity_date": end_date,
        "evaluation_date": datetime.datetime.today().strftime("%Y-%m-%d"),
        "num_cores": 20,
    } 
    
    delta_list = snowball_delta_list(min_price=cur_price*0.8,
                                     max_price=cur_price*1.2,
                                     **snowball_kwargs)
    
    smooth_delta = savgol_filter(np.array(list(delta_list.values())), len(delta_list), int(0.25*len(delta_list)))  # Delta平滑
    delta_series = pd.DataFrame({"Delta": delta_list.values(), "平滑Delta": smooth_delta}, index=delta_list.keys())
    
    return delta_series

def contract_delta_list_nocache(contract_id):
    """
    计算一份合约的delta曲线，无cache
    """
    real_time_data = read_real_time()
    contract_info_path = f"{config.grid_trading_doc_path}/remaining/{contract_id}/{contract_id}_contract.csv"
    contract_info = pd.read_csv(contract_info_path, dtype={"代码": str})
    
    # 提取合约参数
    ticker = contract_info.loc[0, "代码"]
    principal = contract_info.loc[0, "合约本金"]
    coupon_rate = contract_info.loc[0, "票息率"]
    strike_price = contract_info.loc[0, "期初价格"]
    ki = contract_info.loc[0, "敲入线"]
    ko = contract_info.loc[0, "敲出线"]
    start_date = contract_info.loc[0, "合约建仓日"]
    end_date = contract_info.loc[0, "合约结束日"]
    sigma = contract_info.loc[0, "定票息年化波动率"]

    cur_price = real_time_data.loc[ticker, "最新价"]
    snowball_kwargs = {
        "strike_price": strike_price,
        "principal": principal,
        "risk_free_rate": 0.03,
        "coupon_rate": coupon_rate,
        "sigma": sigma,
        "ki": ki,
        "ko": ko,
        "start_date": start_date,
        "maturity_date": end_date,
        "evaluation_date": datetime.datetime.today().strftime("%Y-%m-%d"),
        "num_cores": 20,
    } 
    
    delta_list = snowball_delta_list(min_price=cur_price*0.8,
                                     max_price=cur_price*1.2,
                                     **snowball_kwargs)
    
    smooth_delta = savgol_filter(np.array(list(delta_list.values())), len(delta_list), int(0.25*len(delta_list)))  # Delta平滑
    delta_series = pd.DataFrame({"Delta": delta_list.values(), "平滑Delta": smooth_delta}, index=delta_list.keys())
    
    return delta_series

def get_delta(contract_id, cur_price):
    delta_series = pd.read_csv(f"{config.delta_path}/{contract_id}.csv", index_col=0)["平滑Delta"]
    delta = interp1d(delta_series.index, delta_series.values.reshape(1, -1), "cubic")
    
    return delta(cur_price)[0]

def highlight_rows(x):
    if x["高亮显示"]:
        return ['background-color: pink'] * len(x)
    else:
        return ['background-color: white'] * len(x)