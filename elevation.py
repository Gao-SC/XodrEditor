import copy
import odrparser as odr
from collections import deque
from constants import *

def editRoadSlope(id, value, mode, move, maxStep=0, sameHdg=0, new = True):
  if mode == 'mul' and move == cons.MOVE_BOTH:
    print('Params error!')
    return
  slope, eleva = value, value
  
  road = odr.roads[id]
  elevations = road.find('elevationProfile').findall('elevation')
  geometries = road.find('planView').findall('geometry')
  size = len(geometries)
  length = getData(road, 'length')

  if mode == 'add':
    if move == cons.MOVE_TAIL:
      slope = value/length*-1
    elif move == cons.MOVE_HEAD:
      slope = value/length
    else:
      slope = 0
  elif mode == 'mul':
    if move == cons.MOVE_TAIL:
      eleva = value*length*-1
    elif move == cons.MOVE_HEAD:
      eleva = value*length
    
  for i in range(size):
    g = geometries[i]
    e = elevations[i]
    s = getData(g, 's')

    if mode == 'add':
      setData(e, 'b', getData(e, 'b')+slope)
      if move == cons.MOVE_BOTH:
        setData(e, 'a', getData(e, 'a')+eleva)
      elif move == cons.MOVE_TAIL:
        setData(e, 'a', getData(e, 'a')+slope*(s-length))
      elif move == cons.MOVE_HEAD:
        setData(e, 'a', getData(e, 'a')+slope*s)
      
    elif mode == 'mul':
      setData(e, 'b', getData(e, 'b')+slope)
      if move == cons.MOVE_TAIL:
        setData(e, 'a', getData(e, 'a')+slope*(s-length))
      elif move == cons.MOVE_HEAD:
        setData(e, 'a', getData(e, 'a')+slope*s)

  if not new:
    return
  odr.roadEdits = copy.deepcopy(odr.roadBackup)
  odr.roadEdits[id] = cons.BOTH_LOCKED

  link = road.find('link')
  pre = link.find('predecessor')
  suc = link.find('successor')
  if move == cons.MOVE_HEAD and pre != None: 
    lockChange(cons.TAIL, id)
  if move == cons.MOVE_TAIL and suc != None: 
    lockChange(cons.HEAD, id)

  if move != cons.MOVE_HEAD and pre != None:
    hdg = odr.hdgs[id][0]
    setChange(id, cons.TAIL, maxStep, sameHdg, hdg)
  if move != cons.MOVE_TAIL and suc != None:
    hdg = odr.hdgs[id][1]
    setChange(id, cons.HEAD, maxStep, sameHdg, hdg)

  for r in odr.root.iter('road'):
    newId = r.get('id')
    num = odr.roadEdits[newId]
    if num == cons.TAIL_EDITED or num == cons.TAIL_EDITED2:   # change tail
      # print("move tail" + newId)
      editRoadSlope(newId, eleva, 'add', cons.MOVE_TAIL, new=False)
    elif num == cons.HEAD_EDITED or num == cons.HEAD_EDITED2: # change head
      # print("move head" + newId)
      editRoadSlope(newId, eleva, 'add', cons.MOVE_HEAD, new=False)
    elif num == cons.BOTH_EDITED:                             # change both
      # print("move both" + newId)
      editRoadSlope(newId, eleva, 'add', cons.MOVE_BOTH, new=False)

def lockChange(direction, id):
  for info in odr.roadConnections[id][direction]:
    if info[1]:
      odr.roadEdits[info[0]] = cons.HEAD_LOCKED
    else:
      odr.roadEdits[info[0]] = cons.TAIL_LOCKED

def setChange(id, di, maxStep, sameHdg, hdg):
  queue = deque()

  for info in odr.roadConnections[id][di]:
    queue.append({"id": info[0], "di": info[1], "step": 0})

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    di = item['di']
    step = item['step']

    if sameHdg:
      angle0 = (odr.hdgs[id][0]-hdg)%(2*math.pi)
      angle1 = (odr.hdgs[id][1]-hdg)%(2*math.pi)
      m1, m2, m3, m4 = math.pi/4, math.pi/4*3, math.pi/4*5, math.pi/4*7
      if angle0 > m1 and angle0 < m2 or angle0 > m3 and angle0 < m4:
        step = maxStep
      elif angle1 > m1 and angle1 < m2 or angle1 > m3 and angle1 < m4:
        step = maxStep
  
    if step < maxStep:
      match odr.roadEdits[id]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          odr.roadEdits[id] = cons.BOTH_EDITED
          for info in odr.roadConnections[id][0]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
          for info in odr.roadConnections[id][1]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case cons.TAIL_LOCKED:
          odr.roadEdits[id] = cons.HEAD_EDITED2
          for info in odr.roadConnections[id][cons.HEAD]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case cons.HEAD_LOCKED:
          odr.roadEdits[id] = cons.TAIL_EDITED2
          for info in odr.roadConnections[id][cons.TAIL]:
            queue.append({"id": info[0], "di": info[1], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and di == cons.TAIL:
      match odr.roadEdits[id]:
        case cons.NOT_EDITED:
          odr.roadEdits[id] = cons.TAIL_EDITED
        case cons.HEAD_LOCKED:
          odr.roadEdits[id] = cons.TAIL_EDITED2
        case cons.HEAD_EDITED:
          odr.roadEdits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in odr.roadConnections[id][cons.TAIL]:
        queue.append({"id": info[0], "di": info[1], "step": step})
    elif step == maxStep and di == cons.HEAD:
      match odr.roadEdits[id]:
        case cons.NOT_EDITED:
          odr.roadEdits[id] = cons.HEAD_EDITED
        case cons.TAIL_LOCKED:
          odr.roadEdits[id] = cons.HEAD_EDITED2
        case cons.TAIL_EDITED:
          odr.roadEdits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in odr.roadConnections[id][cons.HEAD]:
        queue.append({"id": info[0], "di": info[1], "step": step})