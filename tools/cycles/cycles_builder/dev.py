# S&P 500 distance above its own 10-year average (AI bubble page chart)
import json, numpy as np
from cdata import merged
r=merged('sp_long','sp','1871-01'); v=np.array([x[1] for x in r]); o=[]
for i in range(120,len(r)): o.append((r[i][0],round(float((v[i]/v[i-120:i].mean()-1)*100),1)))
json.dump([x for x in o if x[0]>='1950'],open('work/dev.json','w'))
