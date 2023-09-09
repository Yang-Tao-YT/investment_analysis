import pandas as pd
from streamlitapps.options.account_record import return_account



current_account  = return_account()
stress_change_pct = 0.01

# 根据delta和gamma算出stress下的盈亏
current_price = current_account.position['行权价'] / (1 + current_account.position['比例']/100)
stress_price =  current_price - current_price * stress_change_pct 
stress_change_amount =  current_price * stress_change_pct 
stress_change_amount = ((stress_change_amount * current_account.position.sDelta 
                        # + 1/2 * current_account.position.sGamma ** 2 
                        )
                        * current_account.position.实际持仓 * current_account.position.持仓类型 * 10000).sum()

22

