"""
Author：查伦
Date：2023年04月21日
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import QuantLib as ql
import matplotlib.pyplot as plt
from matplotlib import cm


def get_IVSurface(strikes: list[float] | np.ndarray,
                  expiration_dates: list[ql.Date] | np.ndarray,
                  implied_volatility: list[list[float]] | np.ndarray,
                  interpolation_method: str = "bicubic",
                  calculation_date: ql.Date = ql.Date().todaysDate(),
                  day_count = ql.Actual365Fixed(),
                  calendar = ql.China(ql.China.SSE)) -> ql.BlackVarianceSurface:
    """
    strikes: 行权价
    expiration_dates: 到期日期
    implied_volatility: 波动率曲面矩阵
    interpolation_method: 波动率曲面插值方法
        "bilinear": 双线性插值
        "bicubic": 双立方插值（更平滑）
    calculation_date: 当前评估日日期
    """
    implied_vols_matrix = ql.Matrix(len(strikes), len(expiration_dates))
    for i in range(implied_vols_matrix.rows()):
        for j in range(implied_vols_matrix.columns()):
            implied_vols_matrix[i][j] = implied_volatility[i][j]

    black_var_surface = ql.BlackVarianceSurface(
        calculation_date, calendar,
        expiration_dates, strikes,
        implied_vols_matrix, day_count)

    black_var_surface.setInterpolation(interpolation_method)

    return black_var_surface


def plot_IVSurface(black_var_surface: ql.BlackVarianceSurface,
                   plot_years: list[float] | np.ndarray,
                   plot_strikes: list[float] | np.ndarray) -> None:
    """
    black_var_surface: QuantLib波动率曲面对象
    plot_years: 波动率曲面时间轴
    plot_strikes: 波动率行权价轴
    """
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(projection='3d')
    X, Y = np.meshgrid(plot_strikes, plot_years)
    Z = np.array([black_var_surface.blackVol(float(y), float(x))
                  for xr, yr in zip(X, Y)
                  for x, y in zip(xr, yr)]
                 ).reshape(len(X), len(X[0]))
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm, linewidth=0.1)
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show(block=True)


def get_VolatilityCone(price_series: pd.DataFrame | pd.Series,
                       term: list[int] | np.ndarray,
                       evaluation_date: str,
                       black_var_surface: Optional[ql.BlackVarianceSurface] = None,
                       strike_price: Optional[float] = None) -> pd.DataFrame:
    """
    price_series: 标的指数价格序列
    term: 期限列表-波动率锥横轴
    black_var_surface: 标的指数隐含波动率曲面
    strike_price: 目标行权价格，将该行权价格下的隐含波动率与历史波动率作比较
    """
    log_return = transfer_price_logreturn(price_series=price_series)  # 转换为对数收益率序列
    vol_ts = pd.DataFrame()
    if strike_price:
        implied_vol = []
    # 计算不同到期期限下的历史波动率分位数
    for ter in term:
        temp_rolling_vol = get_rolling_volatility(log_return=log_return,
                                                  window=ter)
        vol_ts[ter] = temp_rolling_vol
        if strike_price:
            implied_vol.append(black_var_surface.blackVol(ter / 365, strike_price))

    cone = vol_ts.loc[:evaluation_date, :]
    cone = cone.describe().loc["min":, :].T  # 波动率锥
    cone[f"HV at {evaluation_date}"] = vol_ts.loc[evaluation_date, :]  # 当前评估日期下的历史波动率

    if strike_price:
        cone[f"IV at {strike_price}"] = implied_vol

    return cone


def plot_VolatilityCone(cone_df: pd.DataFrame):
    """
    volatility_cone: 波动率锥
    """
    evaluation_date = cone_df.columns[5][6:]

    cone = cone_df.loc[:, :"max"]
    cv = cone_df.iloc[:, 5]
    cone.plot(marker="o")
    cv.plot(marker="+", linestyle="--")

    if len(cone_df.columns) == 7:
        iv = cone_df.iloc[:, -1]
        iv.plot(marker="x", linestyle="--", label=cone_df.columns[-1])

    plt.legend(loc="best")
    plt.title(f"Volatility Cone at {evaluation_date}")
    plt.xlabel("Maturity")
    plt.ylabel("Historical Volatility")
    
    return plt.gcf()


def transfer_price_logreturn(price_series: pd.DataFrame | pd.Series):
    return (price_series.pct_change() + 1).apply(np.log).dropna()


def get_rolling_volatility(log_return: pd.DataFrame | pd.Series,
                           window: int):
    temp_rolling_vol = log_return.rolling(window=window).apply(lambda x: x.std() * 242 ** 0.5).dropna()
    temp_rolling_vol[temp_rolling_vol == 0] = np.nan
    
    return temp_rolling_vol.dropna() 


if __name__ == "__main__":
    # 读取波动率曲面数据
    ivs = pd.read_excel("data/Implied Volatility Surface.xlsx", index_col=0)
    strikes = list(ivs.index)
    expiration_dates = [ql.Date(dt.day, dt.month, dt.year) for dt in ivs.columns]

    # 构造波动率曲面数据，并绘制图像
    black_var_surface = get_IVSurface(strikes=strikes,
                                      expiration_dates=expiration_dates,
                                      implied_volatility=ivs.values,
                                      interpolation_method="bilinear")
    plot_IVSurface(black_var_surface=black_var_surface,
                   plot_years=np.arange(0, black_var_surface.maxTime(), 0.05),
                   plot_strikes=strikes)

    # 读取标的指数历史收盘价序列
    price_series = pd.read_excel("data/510050.xlsx", index_col=0)

    cone = get_VolatilityCone(price_series=price_series,
                              term=[22, 44, 66, 138],
                              evaluation_date="2023-03-31",
                              black_var_surface=black_var_surface,
                              strike_price=2.7)

    plot_VolatilityCone(cone)
