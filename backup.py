import os

with os.popen('f: && cd F:/BaiduSyncdisk/投资/app/investment_analysis&& git add . && git commit --message update && git push') as result:

    result.readlines()
with open(r'F:\BaiduSyncdisk\投资' + '/logs.txt', 'w') as f:
    f.write(result)
