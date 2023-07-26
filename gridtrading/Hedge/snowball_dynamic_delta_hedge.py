"""
Author：查伦
Date：2023年05月11日
"""

from __future__ import annotations
from ..Hedge.snowball_greeks import calculate_snowball_delta_gamma
from ..Pricing.predict_volatility import vol_predict_garch
from ..Pricing.quantlib_pricing import last_trade_date_month, calculate_coupon_snowball
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import datetime
import numpy as np
import pandas as pd
import QuantLib as ql
import streamlit as st


class SnowballHedger:
    def __init__(self,
                 price_series: pd.Series,
                 ki: float,
                 ko: float,
                 ko_lock: int,
                 start_date: str,
                 maturity_date: str,
                 sigma_window: str = None,
                 pre_define_sigma: float = None,
                 risk_free_rate: float = 0.03,
                 risk_free_rate_series: pd.Series = None,
                 initial_position: float = 10000000,
                 trade_cost: float = 0.0001,
                 num_paths: int = 300000):
        """
        滚动回测一个雪球合约的delta对冲损益
        -----------------------------------
        """
        self.price_series = price_series  # 标的资产价格序列
        self.risk_free_rate_series = risk_free_rate_series
        self.date_index = price_series[start_date:maturity_date].index  # 交易日序列
        self.sigma_window = sigma_window
        self.start_date = start_date
        self.maturity_date = maturity_date
        self.pre_define_sigma = pre_define_sigma
        self.risk_free_rate = risk_free_rate
        self.initial_price = price_series[self.date_index[0]] # 标的资产期初价格
        self.contract_number = np.floor(initial_position / self.initial_price)  # 合约数
        self.snowball_kwargs = {
            "strike_price": self.initial_price,
            "principal": self.initial_price,  # 一份雪球合约的名义本金等于一份标的资产期初价格
            "ki": ki,
            "ko": ko,
            "ko_lock": ko_lock,
            "start_date": start_date,
            "maturity_date": maturity_date,
            "is_ki": False,
            "num_paths": num_paths
        }

        # 计算期初雪球估值为0时的票息
        start_snowball_kwargs = self.snowball_kwargs.copy()
        if risk_free_rate_series:
            start_snowball_kwargs["risk_free_rate"] = self.risk_free_rate_series[start_date]
        else:
            start_snowball_kwargs["risk_free_rate"] = risk_free_rate
        # 预测期初定价时波动率
        with st.spinner("根据合约建立日的预测波动率计算票息中..."):
            start_snowball_kwargs["sigma"] = start_sigma = self.get_sigma(start_date)
            self.snowball_kwargs["coupon_rate"] = coupon_rate = calculate_coupon_snowball(**start_snowball_kwargs,
                                                                            current_price=self.initial_price)
            st.info(f"票息计算完成！合约建立日预测波动率为{start_sigma:.2%}，票息率为{coupon_rate:.2%}")
        self.initial_position = initial_position  # 初始持仓金额
        self.trade_cost = trade_cost  # 交易成本

        # 潜在敲出日序列
        start_date, maturity_date = ql.Date(
            start_date, "%Y-%m-%d"), ql.Date(maturity_date, "%Y-%m-%d")
        trade_date = ql.China().businessDayList(start_date + 1, maturity_date)
        self.ko_observation_date = np.array(
            [dt for dt in trade_date if last_trade_date_month(dt, start_date.dayOfMonth())
             and dt > start_date + ql.Period(f"{ko_lock}m")])

    def get_sigma(self,
                  predict_date: str):
        """
        获取预测日当天的预测波动率
        """
        if self.pre_define_sigma:
            return self.pre_define_sigma
        
        predict_date, maturity_date = ql.Date(predict_date, "%Y-%m-%d"), ql.Date(self.maturity_date, "%Y-%m-%d")
        lookback_start_date = (ql.Date(self.start_date, "%Y-%m-%d") - ql.Period(self.sigma_window)).to_date()
        lookback_end_date = (predict_date - ql.Period("1d")).to_date()
        term = ql.China().businessDaysBetween(predict_date, maturity_date)
        if term == 0:
            return 0
        sigma_predicition = vol_predict_garch(self.price_series[lookback_start_date:lookback_end_date],
                                              term=term)

        return sigma_predicition

    def get_delta(self,
                  hedge_price: float,
                  hedge_date: str,
                  constant_sigma: bool = True,
                  constant_rf: bool = True,
                  return_price: bool = False):
        """
        获取对冲日当天以对冲价格计算的Delta值
        ----------------------------------
        hedge_price: 对冲日当日价格
        hedge_date: 对冲日期
        constant_sigma: 是否在雪球存续期间，采用恒定波动率
        return_price: 是否返回雪球价格
        """
        snowball_kwargs = self.snowball_kwargs.copy()
        snowball_kwargs["evaluation_date"] = hedge_date
        if constant_rf:
            snowball_kwargs["risk_free_rate"] = self.risk_free_rate
        else:
            snowball_kwargs["risk_free_rate"] = self.risk_free_rate_series[hedge_date]
            
        if constant_sigma:
            snowball_kwargs["sigma"] = self.get_sigma(self.start_date)
        else:
            snowball_kwargs["sigma"] = self.get_sigma(hedge_date)
        current_delta, _, current_price = calculate_snowball_delta_gamma(current_price=hedge_price,
                                                                         **snowball_kwargs)
        current_delta = np.clip(current_delta, 0, 1)  # 对delta进行截尾，限制在0,1之间

        return current_delta if not return_price else (current_delta, current_price)

    def plot_backtest(self,
                      backtest_df: pd.DataFrame):
        """
        输出回测结果图
        -------------------------------
        backtest_df:
                    total account  delta   snowball value  target asset
        date
        2009-12-31    10000000     0.2165    10000000        248.98
        """
        delta_nv = backtest_df["total account"] / self.initial_position
        snowball_nv = backtest_df["snowball value"] / self.initial_position
        asset_nv = backtest_df["target asset"] / self.initial_price

        plt.figure(figsize=(15, 6))
        ax1 = plt.gca()
        ax1.plot(delta_nv, label="Delta Neutral Portfolio")
        ax1.plot(snowball_nv, label="Snowball")
        ax1.plot(asset_nv, label="Target Asset")
        plt.legend(loc="upper left")
        ax2 = ax1.twinx()
        ax2.plot(backtest_df["delta"],
                 label="Delta",
                 color="r",
                 linewidth=1,
                 linestyle='--',
                 marker='o',
                 markersize=5,
                 markerfacecolor='r')
        plt.title("Snowball Delta Hedge Backtest Result")
        plt.legend(loc="upper right")
        plt.savefig("Hedge/Backtest Result")
        
    def plotly_backtest(self,
                        backtest_record: pd.DataFrame,
                        date_index):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date_index, 
                                 y=backtest_record["total account"], 
                                 name="复制仓位"))
        fig.add_trace(go.Scatter(x=date_index, 
                                 y=backtest_record["snowball value"], 
                                 name="雪球"))
        fig.add_trace(go.Scatter(x=date_index, 
                                 y=backtest_record["target asset"], 
                                 name="标的资产"))
        fig.add_trace(go.Scatter(x=date_index,
                                 y=backtest_record["pos_delta"],
                                 name="复制仓位Delta（右轴）",
                                 yaxis="y2",
                                 line=dict(dash="dot")))
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=''),
                          yaxis2=dict(anchor='x', overlaying='y', side='right'),
                          title="雪球动态对冲回测结果", title_x=0.4, xaxis_title="Time", 
                          yaxis_title="净值", yaxis2_title="Delta")
        
        return fig

    def metrics_backtest(self,
                         backtest_df: pd.DataFrame):
        """
        输出回测组合各项指标
        -------------------------------
        backtest_df:
                    total account  snowball value  target asset
        date
        2009-12-31    10000000       10000000        248.98
        """
        df = backtest_df[["total account", "snowball value", "target asset"]]
        trade_days = len(backtest_df)
        def md(series):
            max_val, max_drawdown = series[0], 0
            for i in series:
                cd = (max_val - i) / max_val
                max_drawdown = max(cd, max_drawdown)
                max_val = max(max_val, i)
            return max_drawdown

        annual_return = (df.iloc[-1] / df.iloc[0]) ** (242 / trade_days) - 1
        annual_volatility = df.pct_change().std() * (242)**0.5
        sharpe_ratio = annual_return / annual_volatility
        maximum_drawdown = df.apply(md, axis=0)
        calmar_ratio = annual_return / (maximum_drawdown)

        result = pd.concat([annual_return, annual_volatility, sharpe_ratio, maximum_drawdown, calmar_ratio], axis=1)
        result.columns = ["annual return", "annual volatility", "sharpe ratio", "maximum drawdown", "calmar ratio"]

        return result

    def backtest_engine(self,
                        method: str = "fixed",
                        constant_sigma: bool = True,
                        exp_upper_limit: float = 0.03,
                        exp_down_limit: float = -0.03):
        """
        回测引擎
        --------------------
        method: delta对冲方法: fixed: 固定时间对冲法，以每日收盘价对冲
                              exposure: 敞口对冲，每日按收盘价计算delta敞口，只有超出容许范围时再进行调仓
        constant_sigma: 是否在雪球存续期间，采用恒定波动率
        exp_upper_limit: delta敞口上界
        exp_down_limit: delta敞口下界
        """
        # 寻找该合约到期日期
        end_date = self.date_index[-1]
        for ko_date in self.ko_observation_date:
            ko_date = ko_date.to_date()
            ko_date = datetime.datetime(ko_date.year, ko_date.month, ko_date.day)
            temp_price = self.price_series[ko_date]
            if temp_price >= self.snowball_kwargs["strike_price"] * self.snowball_kwargs["ko"]:
                end_date = ko_date
                break
        end_index = np.where(self.date_index == end_date)[0][0]
        
        # 回测进度条
        my_bar = st.progress(0)
        my_bar.progress(1 / (end_index + 1), text=f"合约建立日{self.start_date}，计算Delta建立底仓")
        
        # 期初雪球delta值，价格，和底仓持股数
        delta, snowball_price = self.get_delta(self.initial_price, self.start_date, return_price=True)  # 合约建立日雪球的delta值
        position_number = np.floor(self.contract_number * delta)  # 持仓股票数
        # 期初账户
        position_account = position_number * self.initial_price  # 持仓股票账户
        money_account = self.initial_position - position_account * (1 + self.trade_cost)  # 现金账户
        total_account = position_account + money_account  # 总账户
        # 期初delta
        pos_delta = delta
        # 用于plotly绘图的dataframe
        backtest_df = pd.DataFrame(index=self.date_index[:end_index+1], columns=["total account", "snowball value", "target asset", "pos_delta"])
        fig = self.plotly_backtest(backtest_record=backtest_df, date_index=backtest_df.index)
        fig.data[0]["y"][0] = total_account / self.initial_position
        fig.data[1]["y"][0] = (snowball_price * self.contract_number + self.initial_position) / self.initial_position
        fig.data[2]["y"][0] = self.initial_price / self.initial_price
        fig.data[3]["y"][0] = pos_delta
        placeholder = st.empty()
        placeholder.plotly_chart(fig, use_container_width=True)
        # 回测记录
        backtest_record = {
            "date": [self.date_index[0]],
            "total account": [total_account],
            "position account": [position_account],
            "money account": [money_account],
            "sigma": [self.get_sigma(self.start_date)],
            "delta": [delta],
            "pos_delta": [pos_delta],
            "delta_exposure": [delta-pos_delta],
            "snowball value": [snowball_price * self.contract_number + self.initial_position],
            "target asset": [self.initial_price]
        }

        # 日频回测，从雪球合约建立后一日开始
        for i, dt in enumerate(self.date_index[1:end_index+1]):
            # print("雪球合约起始截止日期：", self.start_date, self.maturity_date, "当前回测日期:", dt.strftime("%Y-%m-%d"))
            my_bar.progress((i + 2) / (end_index + 1), text="动态Delta对冲回测中，当前回测日期：" + dt.strftime("%Y-%m-%d"))
            temp_price = self.price_series[dt]  # 当前日期价格
            # 按照当日收盘价计算雪球delta和价格
            delta, snowball_price = self.get_delta(temp_price, dt.strftime("%Y-%m-%d"), constant_sigma=constant_sigma, return_price=True)

            # 判断是否敲出到期，或持有至到期日
            is_ko, is_last = False, False
            # 敲出到期
            if temp_price >= self.snowball_kwargs["strike_price"] * self.snowball_kwargs["ko"] and ql.Date(dt.strftime("%Y-%m-%d"), "%Y-%m-%d") in self.ko_observation_date:
                delta = 0
                is_ko = True
            # 若雪球持有至合约最后一日，则清掉所有仓位
            if i == len(self.date_index[1:]) - 1:
                is_last = True

            # delta敞口
            delta_exposure = delta - pos_delta

            # 判断当日是否要调仓
            if method == "fixed" or delta_exposure >= exp_upper_limit or delta_exposure <= exp_down_limit or is_ko or is_last:
                if_change_position = True
            else:
                if_change_position = False
            # 执行调仓
            if if_change_position:
                target_position_number = np.floor(self.contract_number * delta)  # 目标持仓数
                if is_last:
                    target_position_number = 0 # 持仓至到期日，清掉仓位
                position_number_change = target_position_number - position_number  # 变动仓位
                position_number = target_position_number
                temp_trade_cost = abs(position_number_change * temp_price * self.trade_cost)  # 调仓交易成本
                # 计算调仓后的账户净值
                money_account = money_account - position_number_change * temp_price - temp_trade_cost
                position_account = position_number * temp_price
                total_account = position_account + money_account
                # 记录当前持仓delta
                pos_delta = delta
            # 不执行调仓
            else:
                position_account = position_number * temp_price
                total_account = position_account + money_account
            # 记录组合每一日变动
            backtest_record["date"].append(dt)
            backtest_record["total account"].append(total_account)
            backtest_record["position account"].append(position_account)
            backtest_record["money account"].append(money_account)
            backtest_record["sigma"].append(self.get_sigma(dt.strftime("%Y-%m-%d")))
            backtest_record["delta"].append(delta)
            backtest_record["pos_delta"].append(pos_delta)
            backtest_record["delta_exposure"].append(delta - pos_delta)
            backtest_record["snowball value"].append(snowball_price * self.contract_number + self.initial_position)
            backtest_record["target asset"].append(temp_price)
            
            fig.data[0]["y"][i+1] = total_account / self.initial_position
            fig.data[1]["y"][i+1] = (snowball_price * self.contract_number + self.initial_position) / self.initial_position
            fig.data[2]["y"][i+1] = temp_price / self.initial_price
            fig.data[3]["y"][i+1] = pos_delta
            
            placeholder.empty()
            placeholder.plotly_chart(fig, use_container_width=True)
            
            # 判断是否敲入敲出，如敲出，则结束回测
            if is_ko:
                break
            elif temp_price <= self.snowball_kwargs["strike_price"] * self.snowball_kwargs["ki"]:
                self.snowball_kwargs["is_ki"] = True
        
        if end_date < self.date_index[-1]:
            end_date = end_date.strftime("%Y-%m-%d")
            st.info(f"标的资产在{end_date}敲出，回测完成！")
        else:
            st.info("标的资产持有期未发生敲出，回测完成！")
        
        placeholder.empty()
        # 回测结果输出至dataframe
        backtest_df = pd.DataFrame(backtest_record).set_index("date")

        return backtest_df


if __name__ == "__main__":
    zz500 = pd.read_excel("Hedge/000905.xlsx", index_col=0)
    shibor = pd.read_excel("SHIBOR_1年.xlsx", index_col=0)
    risk_free_rate_series = shibor.squeeze() / 100
    sb = SnowballHedger(price_series=zz500.squeeze(),
                        risk_free_rate_series=risk_free_rate_series,
                        sigma_window="1y",
                        ki=0.85,
                        ko=1.05,
                        ko_lock=0,
                        start_date="2018-01-03",
                        maturity_date="2019-01-03")
    sb.backtest_engine(method="fixed",
                       exp_upper_limit=0.03,
                       exp_down_limit=-0.03)
    pass
