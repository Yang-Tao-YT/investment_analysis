"""
Author：查伦
Date：2023年05月04日
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Pricing.quantlib_pricing import snowball_pricing_mcm_mp


def calculate_snowball_delta_gamma(current_price: float,
                                   num_paths: int = 300000,
                                   seed: int = 20,
                                   h: float = 0.1,
                                   **kwargs):
    """ 
    蒙特卡洛方法下，基于差分法计算雪球的delta和gamma
    ---------------------------------------------
    current_price: 标的当前价格
    num_paths: 模拟路径数量
    seed: 随机种子
    h: 计算delta和gamma的变动距离
    kwargs: 雪球产品参数
    """
    kwargs["num_paths"], kwargs["seed"] = num_paths, seed

    initial_price = kwargs["strike_price"]
    current_price = round(current_price / initial_price * 100, 2)
    kwargs["principal"] = kwargs["strike_price"] = 100


    p_plus, p, p_minus = snowball_pricing_mcm_mp(current_price=[current_price + h,
                                                                current_price,
                                                                current_price - h],
                                                 **kwargs)

    # 差分法计算delta和gamma
    delta = (p_plus - p_minus) / (2 * h)
    gamma = (p_plus + p_minus - 2 * p) / h ** 2
    p = p * initial_price / 100  # 一份雪球合约的价格（名义本金等于期初标的资产的价格）

    return delta, gamma, p


def snowball_delta_gamma_list(min_price: int,
                              max_price: int,
                              step: float,
                              h: float = 0.01,
                              num_paths: int = 300000,
                              delta_plot: bool = False,
                              **kwargs):
    """
    在输入标的价格上下限范围内，生成雪球delta，gamma序列
    ------------------------------------------------
    min_price: 标的价格下限
    max_price: 标的价格上限
    step: 价格步长
    h: 蒙特卡洛模拟计算greeks的变动幅度
    num_paths: 蒙特卡洛模拟路径数
    delta_plot: 是否输出delta序列图
    kwargs: 雪球产品其余参数
    """
    kwargs["num_paths"] = num_paths
    kwargs["principal"] = kwargs["strike_price"]

    price_range = np.arange(min_price, max_price, step)  # 价格序列
    price_list = np.zeros(len(price_range) * 3)
    for i in range(len(price_range)):
        temp_price = price_range[i]
        price_list[3*i:3*i+3] = temp_price-h, temp_price, temp_price+h  # 差分法计算delta，插入变动价格

    value_list = snowball_pricing_mcm_mp(current_price=price_list, **kwargs)  # 计算所有价格
    res = np.zeros([len(price_range), 2])

    for i in range(len(price_range)):
        p_plus, p, p_minus = value_list[3*i+2], value_list[3*i+1], value_list[3*i]  # 提取价格
        delta = (p_plus - p_minus) / (2 * h)  # 计算delta，gamma
        gamma = (p_plus + p_minus - 2 * p) / h ** 2
        res[i, ] = delta, gamma

    res_df = pd.DataFrame(res, columns=["delta", "gamma"], index=price_range / kwargs["strike_price"])

    if delta_plot:
        delta_max, delta_min = res_df["delta"].max(), res_df["delta"].min()
        res_df["delta"].plot(color="red", label="Delta")
        plt.plot([kwargs["ki"], kwargs["ki"]], [delta_min-0.2, delta_max+0.2], "g--", label="KI")
        plt.plot([kwargs["ko"], kwargs["ko"]], [delta_min-0.2, delta_max+0.2], "b--", label="KO")
        plt.title("Snowball Delta")
        plt.xlabel("Underlying Price")
        plt.ylabel("Delta")
        plt.ylim([delta_min-0.2, delta_max+0.2])
        plt.legend()
        plt.show(block=True)


    return res_df


if __name__ == "__main__":
    snowball_kwargs = {
        "seed": 2023,
        "strike_price": 100,
        "risk_free_rate": 0.03,
        "sigma": 0.3416,
        "coupon_rate": 0.4,
        "ki": 0.85,
        "ko": 1.05,
        "ko_lock": 0,
        "evaluation_date": "2023-01-13",
        "start_date": "2022-06-21",
        "maturity_date": "2023-06-20",
        "verbose": False,
        "is_ki": True
    }

    delta, _, _ = calculate_snowball_delta_gamma(current_price=50, **snowball_kwargs)
    print(delta)
    # snowball_greeks = snowball_delta_gamma_list(min_price=4400,
    #                                             max_price=4600,
    #                                             step=100,
    #                                             delta_plot=True,
    #                                             **snowball_kwargs)
