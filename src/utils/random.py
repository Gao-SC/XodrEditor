import random

from Json.carDetector import detector

def getRandomValue(string):
  valueList = string.split('_')
  
  if valueList[0] == 'random':
    try:
      v = random.uniform(float(valueList[1]), float(valueList[2]))
      print('v=', v)
    except IndexError:
      print("The number of params is too small!")
      return 0
    except ValueError:
      print("The string cannot be transformed into a number!")
      return 0
    except Exception:
      print("Unknown error!")
      return 0
  else:
    try:
      v = float(valueList[0])
    except ValueError:
      print("The string cannot be transformed into a number!")
      return 0
    except Exception:
      print("Unknown error!")
      return 0
  return v

def getRandomInt(num):
  return random.randrange(0, num)

def getRandomId1(id):
  try:
    value = int(id)
    return id
  except ValueError:
    if id == "random":
      detector.setCandidates()
      return detector.getRandomId1()
    else:
      print("Invalid id! Choose default 0.")
      return "0"

def getRandomId2(id):
  try:
    value = int(id)
    return id, []
  except ValueError:
    if id == "random":
      detector.setCandidates()
      id, lid = detector.getRandomId2()
      return id, [lid]
    else:
      print("Invalid id! Choose default 0.")
      return "0", []