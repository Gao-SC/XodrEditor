from collections import deque
import copy

import Xodr.xodrParser as Xparser
import Json.jsonParser as JParser
import Json.vehicleDetector as detector
from utils.constants import *

def editRoadSlope(id, value, mode, move, maxStep=0, sameHdg=0):
  if mode == 'mul' and move == cons.MOVE_BOTH:
    print('Params error!')
    return
  
  if id == "random":
    detector.setCandidates()
    id = random.choice(detector.candidateRoads)
    print(id)

  Xparser.roadEdits = copy.deepcopy(Xparser.roadBackup)
  Xparser.roadEdits[id] = cons.BOTH_LOCKED
  
  road = Xparser.roads[id]
  link = road.find('link')
  pre = link.find('predecessor')
  suc = link.find('successor')
  if move == cons.MOVE_HEAD and pre != None: 
    lockChange(cons.TAIL, id)
  if move == cons.MOVE_TAIL and suc != None: 
    lockChange(cons.HEAD, id)

  if move != cons.MOVE_HEAD and pre != None:
    hdg = Xparser.hdgs[id][0]
    setChange(id, cons.TAIL, maxStep, sameHdg, hdg)
  if move != cons.MOVE_TAIL and suc != None:
    hdg = Xparser.hdgs[id][1]
    setChange(id, cons.HEAD, maxStep, sameHdg, hdg)
  
  value = value if mode != 'mul' else value*getData(road, 'length')
  setRoadSlope(id, value, move)
  for r in Xparser.root.iter('road'):
    newId = r.get('id')
    num = Xparser.roadEdits[newId]
    if num == cons.TAIL_EDITED or num == cons.TAIL_EDITED2:   # change tail
      setRoadSlope(newId, value, cons.MOVE_TAIL)
    elif num == cons.HEAD_EDITED or num == cons.HEAD_EDITED2: # change head
      setRoadSlope(newId, value, cons.MOVE_HEAD)
    elif num == cons.BOTH_EDITED:                             # change both
      setRoadSlope(newId, value, cons.MOVE_BOTH)

def setRoadSlope(id, value, move):
  print(id, value, move)
  
  road = Xparser.roads[id]
  elevations = road.find('elevationProfile').findall('elevation')
  elevaNum = len(elevations)
  length = getData(road, 'length')

  slope = 0
  if move == cons.MOVE_TAIL:
    slope = value/length*-1
  elif move == cons.MOVE_HEAD:
    slope = value/length
    
  for i in range(elevaNum):
    e = elevations[i]
    s0 = getData(e, 's')
    s1 = getData(road, "length") if i == elevaNum-1 else getData(elevations[i+1], "s")

    setData(e, 'b', getData(e, 'b')+slope)
    if move == cons.MOVE_BOTH:
      setData(e, 'a', getData(e, 'a')+value)
    elif move == cons.MOVE_TAIL:
      setData(e, 'a', getData(e, 'a')+slope*(s0-length))
    elif move == cons.MOVE_HEAD:
      setData(e, 'a', getData(e, 'a')+slope*s0)

    for infos in JParser.carData[-1][id].values():
      for carInfo in infos:
        pos = carInfo["pos"]
        if pos >= s0 and pos < s1:
          de = value
          if move == cons.MOVE_TAIL:
            de = slope*(s0-length)
          elif move == cons.MOVE_HEAD:
            de = slope*s0

          ord = JParser.getOrd(carInfo)
          ord["position"]['y'] += de
          if ord.get("angle") != None:
            ord["angle"]["x"] += math.atan(slope)
          else:
            ord["rotation"]["x"] += math.atan(slope)*180/math.pi

def lockChange(direction, id):
  for info in Xparser.roadConnections[id][direction]:
    if info[1]:
      Xparser.roadEdits[info[0]] = cons.HEAD_LOCKED
    else:
      Xparser.roadEdits[info[0]] = cons.TAIL_LOCKED

def setChange(id, di, maxStep, sameHdg, hdg):
  queue = deque()

  for info in Xparser.roadConnections[id][di]:
    queue.append({"id": info[0], "di": info[1], "step": 0})

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    di = item['di']
    step = item['step']

    if sameHdg:
      angle0 = (Xparser.hdgs[id][0]-hdg)%(2*math.pi)
      angle1 = (Xparser.hdgs[id][1]-hdg)%(2*math.pi)
      m1, m2, m3, m4 = math.pi/4, math.pi/4*3, math.pi/4*5, math.pi/4*7
      if angle0 > m1 and angle0 < m2 or angle0 > m3 and angle0 < m4:
        step = maxStep
      elif angle1 > m1 and angle1 < m2 or angle1 > m3 and angle1 < m4:
        step = maxStep
  
    if step < maxStep:
      match Xparser.roadEdits[id]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          Xparser.roadEdits[id] = cons.BOTH_EDITED
          for info in Xparser.roadConnections[id][0]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
          for info in Xparser.roadConnections[id][1]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case cons.TAIL_LOCKED:
          Xparser.roadEdits[id] = cons.HEAD_EDITED2
          for info in Xparser.roadConnections[id][cons.HEAD]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case cons.HEAD_LOCKED:
          Xparser.roadEdits[id] = cons.TAIL_EDITED2
          for info in Xparser.roadConnections[id][cons.TAIL]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and di == cons.TAIL:
      match Xparser.roadEdits[id]:
        case cons.NOT_EDITED:
          Xparser.roadEdits[id] = cons.TAIL_EDITED
        case cons.HEAD_LOCKED:
          Xparser.roadEdits[id] = cons.TAIL_EDITED2
        case cons.HEAD_EDITED:
          Xparser.roadEdits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in Xparser.roadConnections[id][cons.TAIL]:
        queue.append({"id": info[0], "di": info[1], "step": step})
    elif step == maxStep and di == cons.HEAD:
      match Xparser.roadEdits[id]:
        case cons.NOT_EDITED:
          Xparser.roadEdits[id] = cons.HEAD_EDITED
        case cons.TAIL_LOCKED:
          Xparser.roadEdits[id] = cons.HEAD_EDITED2
        case cons.TAIL_EDITED:
          Xparser.roadEdits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in Xparser.roadConnections[id][cons.HEAD]:
        queue.append({"id": info[0], "di": info[1], "step": step})