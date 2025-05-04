import random

from jsons.carDetector import detector

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

def getRandomId(id, lane=False):
  ego, npc = 1, 0
  idList = id.split('_')

  try:
    value = int(idList[0])
    if lane: 
      return idList[0], []
    return idList[0]
  
  except ValueError:
    if idList[0] == "random":
      try:
        ego, npc = int(idList[1]), int(idList[2])  
      except Exception:
        pass
  
      detector.setCandidates(ego, npc)
      if lane: 
        rid, lid = detector.getRandomId2()
        return rid, [lid]
      return detector.getRandomId1()
    
    else:
      print("Invalid id! Choose default 0.")
      if lane: 
        return "0", ["0"]
      return "0"