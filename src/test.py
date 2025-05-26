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
    df.to_excel(fileName, index=False)

fileName = ".\\data\\test.xlsx"
pd_toExcel(answer, fileName)




'''
import os
import random
import math


A_B = [-1, 1]

def generateRandomWidth():
  ms = random.randint(0,10)
  v = 2
  command = f"width id=random_1_1 s=1 sh=1 ms={ms} v={v}\n"
  return command
def generateRandomSlope():
  x = [0, 1]
  ms = random.randint(0,10)
  v = 0.1
  mv = random.choice(x)
  command = f"slope id=random_1_0 ms={ms} v={v} ms={ms} mv={mv}\n"
  return command

def generateRandomCurve():
  v0 = (1+random.random())*random.choice(A_B)/4
  v1 = (1+random.random())*random.choice(A_B)/4
  h0, h1 = 0, 0
  if random.random() > 0.95:
    h0 = (1+random.random())*random.choice(A_B)*math.pi/10
    h1 = (1+random.random())*random.choice(A_B)*math.pi/10
  command = f"curve id=random_1_0 v0={v0} v1={v1} h0={h0} h1={h1}\n"
  return command

filenames = [
  "ARG_Carcarana-3_3_I-1-1",
  "ARG_Carcarana-11_2_I-1-1",
  "ARG_Carcarana-12_2_T-1",
  "ARG_Carcarana-1_3_I-1-1",
  "ARG_Carcarana-7_1_I-1-1",
  "BEL_Zwevegem-1_2_T-1",
  "BEL_Wervik-4_2_I-1-1",
  "BEL_Putte-17_1_I-1-1",
  "BEL_Putte-16_2_T-1",
  "BEL_Zwevegem-3_3_T-1",
  "BEL_Zwevegem-8_4_I-1-1",
  "BEL_Zaventem-5_1_T-1",
  "BEL_Zaventem-2_6_I-1-1",
  "BEL_Nivelles-9_2_T-1",
  "BEL_Nivelles-7_1_T-1",
  "BEL_Putte-14_1_I-1-1",
  "BEL_Nivelles-18_1_I-1-1",
  "BEL_Aarschot-5_1_T-1",
  "BEL_Nivelles-16_2_T-1",
  "BEL_Zaventem-1_1_T-1",
  "BEL_Putte-10_1_I-1-1",
  "BEL_Zwevegem-1_1_T-1",
  "BEL_Putte-5_5_T-1",
  "BEL_Putte-2_2_I-1-1",
  "BEL_Beringen-3_4_I-1-1",
  "CHN_Sha-11_1_I-1-1",
  "CHN_Sha-1_8_T-1",
  "CHN_Sha-2_6_T-1",
  "CHN_Sha-5_1_T-1",
  "CHN_Sha-14_1_T-1",
  "USA_Lanker-2_17_I-1-1"
]

with open('.\\data\\script\\testCurve.odrScript', 'w', encoding='utf-8') as f:
  size = len(filenames)
  for i in range(size):
    f.write(f"{filenames[i]}\n")
    f.write(generateRandomCurve())
    f.write("close\n")

print("OK")'''