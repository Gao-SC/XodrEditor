import xml.etree.ElementTree as ET
import src.xodr.xodrParser as Xparser
import src.json.jsonParser as JParser
import test
from src.utils.constants import *
from collections import deque
import copy

def setWidth(width: ET.Element, value, mode, length=0):
  a = getData(width, 'a')
  b = getData(width, 'b')
  c = getData(width, 'c')
  d = getData(width, 'd')
  match mode:
    case 'add':
      setData(width, 'a', value+getData(width, 'a'))
      return [value, 0, 0, 0]
    case 'stail':
      x = length-getData(width, 'sOffset')
      setData(width, 'a', a+value/length*x)
      setData(width, 'b', b-value/length)
      return [value/length*x, -value/length, 0, 0]
    case 'shead':
      x = getData(width, 'sOffset')
      setData(width, 'a', a+value/length*x)
      setData(width, 'b', b+value/length)
      return [value/length*x, value/length, 0, 0]
    case _:
      return
    
# change specific road width (on lanes)
## 默认仅有一个LaneSection
## TODO 因一些原因暂时删除了按比例拓宽
def editRoadWidth(id, value, smooth=0, maxStep=0, sameHdg=0, laneIds=[]):
  if id == "random":
    test.setCandidates()
    id, laneId = random.choice(test.candidateLanes)
    laneIds = [laneId]
    print(id, laneId)

  Xparser.laneEdits = copy.deepcopy(Xparser.laneBackup)
  # TODO if mode == 'mul':
  if laneIds == []:
    for lid in Xparser.laneEdits[id].keys():
      Xparser.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, Xparser.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, Xparser.hdgs[id][1])
    value = value/len(Xparser.laneEdits[id].values())
  else:
    for lid in laneIds:
      Xparser.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, Xparser.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, Xparser.hdgs[id][1])
    value = value/len(laneIds)

  for rid, rEdit in Xparser.laneEdits.items():
    for lid, info in rEdit.items():
      if info == cons.TAIL_EDITED and smooth:
        setLaneWidth(rid, lid, value, 'addt')
      elif info == cons.HEAD_EDITED and smooth:
        setLaneWidth(rid, lid, value, 'addh')
      elif info == cons.BOTH_EDITED:
        setLaneWidth(rid, lid, value, 'add')

def setLaneWidth(id, lid, value, mode):
  road = Xparser.roads[id]
  length = getData(road, 'length')
  section = road.find('lanes').find('laneSection')

  for lane in section.findall('.//lane'):
    if lane.get('id') != lid:
      continue
    widths = lane.findall('width')
    widthNum = len(widths)
      
    for j in range(widthNum):
      delta = [0, 0, 0, 0]
      match mode:
        case 'add':
          delta = setWidth(widths[j], value, 'add')
        case 'addt':
          delta = setWidth(widths[j], value, 'stail', length)
        case 'addh':
          delta = setWidth(widths[j], value, 'shead', length)
      
      s0 = getData(widths[j], "sOffset")
      s1 = getData(road, "length") if j == widthNum-1 else getData(widths[j+1], "sOffset")

      for laneId, infos in JParser.carData[-1][id].items():
        if int(laneId) < 0 < int(lid) or int(laneId) > 0 > int(lid):
          continue
        if int(lid) > int(laneId) > 0 or int(lid) < int(laneId) < 0:
          continue
        for carInfo in infos:
          pos = carInfo["pos"]
          if pos >= s0 and pos < s1:
            hdg = Xparser.findHdg(id, pos)
            ds = pos-s0
            dw = delta[0]+delta[1]*ds+delta[2]*ds**2+delta[3]*ds**3
            dw = dw if laneId != lid else dw/2
            
            ord = JParser.getOrd(carInfo)
            if int(lid) < 0:
              ord["position"]['x'] += dw*math.sin(hdg)
              ord["position"]['z'] -= dw*math.cos(hdg)
              carInfo["dis"] += dw
            else:
              ord["position"]['x'] -= dw*math.sin(hdg)
              ord["position"]['z'] += dw*math.cos(hdg)
              carInfo["dis"] -= dw
    return

def setChange(id, lid, di, maxStep, sameHdg, hdg):
  queue = deque()
  step = 0

  for info in Xparser.laneConnections[id][lid][int(di)]:
    queue.append({"id": info[0], 'lid': info[1], "di": info[2], "step": 0})

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    lid = item['lid']
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
      match Xparser.laneEdits[id][lid]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          Xparser.laneEdits[id][lid] = cons.BOTH_EDITED
          for info in Xparser.laneConnections[id][lid][0]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
          for info in Xparser.laneConnections[id][lid][1]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and not di:
      match Xparser.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          Xparser.laneEdits[id][lid] = cons.TAIL_EDITED
        case cons.HEAD_EDITED:
          Xparser.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in Xparser.laneConnections[id][lid][int(cons.TAIL)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})
    elif step == maxStep and di:
      match Xparser.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          Xparser.laneEdits[id][lid] = cons.HEAD_EDITED
        case cons.TAIL_EDITED:
          Xparser.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in Xparser.laneConnections[id][lid][int(cons.HEAD)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})