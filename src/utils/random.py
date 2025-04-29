import random

def getRandomValue(string):
  valueList = string.split('_')
  if valueList[0] == 'random':
    v = random.uniform(float(valueList[1]), float(valueList[2]))
    print('v=', v)
  else:
    v = float(valueList[0])
  return v