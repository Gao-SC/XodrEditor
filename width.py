import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *
from collections import deque
import copy

def setWidth(width: ET.Element, value, mode, distance=0):
  a = get(width, 'a')
  b = get(width, 'b')
  c = get(width, 'c')
  d = get(width, 'd')
  match mode:
    case 'add':
      set(width, 'a', value+get(width, 'a'))
    case 'stail1':
      x = distance-get(width, 'sOffset')
      newC = c-3*value/x**2
      newD = d+2*value/x**3
      set(width, 'a', a+value)
      set(width, 'c', newC)
      set(width, 'd', newD)
    case 'shead1':
      x = distance-get(width, 'sOffset')
      newC = c+3*value/x**2
      newD = d-2*value/x**3
      set(width, 'c', newC)
      set(width, 'd', newD)
    case 'stail2':
      x = distance-get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b-value/distance)
    case 'shead2':
      x = get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b+value/distance)

    case 'mul':
      set(width, 'a', value*get(width, 'a'))
      set(width, 'b', value*get(width, 'b'))
      set(width, 'c', value*get(width, 'c'))
      set(width, 'd', value*get(width, 'd'))
    case _:
      return
    
# change specific road width (on lanes)
## 默认仅有一个LaneSection
## TODO 因一些原因暂时删除了按比例拓宽
def editRoadWidth(id, value, smooth=0, maxStep=0, sameHdg=0, laneIds=[]):
  vars.laneEdits = copy.deepcopy(vars.laneBackup)
  # TODO if mode == 'mul':
  if laneIds == []:
    for lid in vars.laneEdits[id].keys():
      vars.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, vars.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, vars.hdgs[id][1])
    value = value/len(vars.laneEdits[id].values())
  else:
    for lid in laneIds:
      vars.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, vars.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, vars.hdgs[id][1])
    value = value/len(laneIds)

  for rid, rEdit in vars.laneEdits.items():
    for lid, info in rEdit.items():
      if info == cons.TAIL_EDITED and smooth:
        editLaneWidth(rid, lid, value, 'addt', smooth)
      elif info == cons.HEAD_EDITED and smooth:
        editLaneWidth(rid, lid, value, 'addh', smooth)
      elif info == cons.BOTH_EDITED:
        editLaneWidth(rid, lid, value, 'add' , smooth)

def editLaneWidth(id, lid, value, mode, smooth):
  for road in vars.root.iter('road'):
    if road.get('id') != id:
      continue
    length = get(road, 'length')
    section = road.find('lanes').find('laneSection')

    for lane in section.findall('.//lane'):
      if lane.get('id') != lid:
        continue
      widths = lane.findall('width')
      widthNum = len(widths)

      for j in range(widthNum):
        match (mode, smooth):
          case ('add', x):
            setWidth(widths[j], value, 'add')
          case ('mul', x):
            setWidth(widths[j], value, 'mul')
          case ('addt', 1):
            if j == 0:
              nextS = get(widths[j+1], 'sOffset')
              setWidth(widths[j], value, 'stail1', distance=nextS)
          case ('addh', 1):
            if j == widthNum-2:
              nextS = get(widths[j+1], 'sOffset')
              setWidth(widths[j], value, 'shead1', distance=nextS)

          case ('addt', 2):
            setWidth(widths[j], value, 'stail2', distance=length)
          case ('addh', 2):
            setWidth(widths[j], value, 'shead2', distance=length)
          case _:
            continue
      return

def setChange(id, lid, di, maxStep, sameHdg, hdg):
  queue = deque()
  step = 0

  for info in vars.laneConnections[id][lid][int(di)]:
    queue.append({"id": info[0], 'lid': info[1], "di": info[2], "step": 0})
    print("here")

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    lid = item['lid']
    di = item['di']
    step = item['step']

    if sameHdg:
      angle0 = (vars.hdgs[id][0]-hdg)%(2*math.pi)
      angle1 = (vars.hdgs[id][1]-hdg)%(2*math.pi)
      m1, m2, m3, m4 = math.pi/4, math.pi/4*3, math.pi/4*5, math.pi/4*7
      if angle0 > m1 and angle0 < m2 or angle0 > m3 and angle0 < m4:
        step = maxStep
      elif angle1 > m1 and angle1 < m2 or angle1 > m3 and angle1 < m4:
        step = maxStep

    if step < maxStep:
      match vars.laneEdits[id][lid]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          vars.laneEdits[id][lid] = cons.BOTH_EDITED
          for info in vars.laneConnections[id][lid][0]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
          for info in vars.laneConnections[id][lid][1]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and not di:
      match vars.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          vars.laneEdits[id][lid] = cons.TAIL_EDITED
        case cons.HEAD_EDITED:
          vars.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.laneConnections[id][lid][int(cons.TAIL)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})
    elif step == maxStep and di:
      match vars.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          vars.laneEdits[id][lid] = cons.HEAD_EDITED
        case cons.TAIL_EDITED:
          vars.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.laneConnections[id][lid][int(cons.HEAD)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})