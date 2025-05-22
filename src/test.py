dir_path = ".\\log\\"
with open('.\\log\\test.log', 'r') as file:
  lines = file.readlines()
  answer = []
  for i in range(len(lines)):
    if i % 2 == 0:
      x, y = lines[i].split(':')
      x, y = x.split()[1], y.strip()
      answer.append({"time": float(x), "name": y})

  answer.sort(key=lambda x: x["name"])


import pandas as pd
def pd_toExcel(data, fileName):  # pandas库储存数据到excel
    times = []
    names = []
    for i in range(len(data)):
        times.append(data[i]["time"])
        names.append(data[i]["name"])
 
    dfData = {  # 用字典设置DataFrame所需数据
      'time': times,
      'name': names,
    }
    df = pd.DataFrame(dfData)  # 创建DataFrame
    df.to_excel(fileName, index=False)  # 存表，去除原始索引列（0,1,2...）

fileName = ".\\data\\test.xlsx"
pd_toExcel(answer, fileName)