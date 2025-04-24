import xml.etree.ElementTree as ET
import odrparser as odr
import detector as det
from constants import *
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
    case 'stail1':
      x = length
      newC = c-3*value/x**2
      newD = d+2*value/x**3
      setData(width, 'a', a+value)
      setData(width, 'c', newC)
      setData(width, 'd', newD)
      return [value, 0, -3*value/x**2, 2*value/x**3]
    case 'shead1':
      x = length
      newC = c+3*value/x**2
      newD = d-2*value/x**3
      setData(width, 'c', newC)
      setData(width, 'd', newD)
      return [0, 0, 3*value/x**2, -2*value/x**3]
    case 'stail2':
      x = length-getData(width, 'sOffset')
      setData(width, 'a', a+value/length*x)
      setData(width, 'b', b-value/length)
      return [value/length*x, -value/length, 0, 0]
    case 'shead2':
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
  odr.laneEdits = copy.deepcopy(odr.laneBackup)
  # TODO if mode == 'mul':
  if laneIds == []:
    for lid in odr.laneEdits[id].keys():
      odr.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, odr.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, odr.hdgs[id][1])
    value = value/len(odr.laneEdits[id].values())
  else:
    for lid in laneIds:
      odr.laneEdits[id][lid] = cons.BOTH_EDITED
      setChange(id, lid, cons.TAIL, maxStep, sameHdg, odr.hdgs[id][0])
      setChange(id, lid, cons.HEAD, maxStep, sameHdg, odr.hdgs[id][1])
    value = value/len(laneIds)

  for rid, rEdit in odr.laneEdits.items():
    for lid, info in rEdit.items():
      if info == cons.TAIL_EDITED and smooth:
        editLaneWidth(rid, lid, value, 'addt', smooth)
      elif info == cons.HEAD_EDITED and smooth:
        editLaneWidth(rid, lid, value, 'addh', smooth)
      elif info == cons.BOTH_EDITED:
        editLaneWidth(rid, lid, value, 'add' , smooth)

def editLaneWidth(id, lid, value, mode, smooth):
  print("here")
  road = odr.roads[id]
  length = getData(road, 'length')
  section = road.find('lanes').find('laneSection')

  for lane in section.findall('.//lane'):
    if lane.get('id') != lid:
      continue
    widths = lane.findall('width')
    widthNum = len(widths)

    dis = 0
    if smooth == 1 and mode == 'addt':
      for j in range(widthNum):
        if getData(widths[j], 'sOffset') >= value*2:
          dis = getData(widths[j], 'sOffset')
          break
    if smooth == 1 and mode == 'addh':
      for j in range(widthNum-1, 0, -1):
        if length-getData(widths[j], 'sOffset') >= value*2:
          dis = getData(widths[j], 'sOffset')
          break
      
    for j in range(widthNum):
      delta = None
      match (mode, smooth):
        case ('add', x):
          delta = setWidth(widths[j], value, 'add')
        case ('addt', 1):
          if getData(widths[j], 'sOffset') < dis:
            delta = setWidth(widths[j], value, 'stail1', dis)
        case ('addh', 1):
          if getData(widths[j], 'sOffset') >= dis:
            delta = setWidth(widths[j], value, 'shead1', length-dis)
        case ('addt', 2):
          delta = setWidth(widths[j], value, 'stail2', length)
        case ('addh', 2):
          delta = setWidth(widths[j], value, 'shead2', length)
      
      s0 = getData(widths[j], "sOffset")
      s1 = getData(road, "length") if j == widthNum-1 else getData(widths[j+1], "sOffset")

      for laneId, infos in det.carInfos[id].items():
        if int(laneId) < 0 < int(lid) or int(laneId) > 0 > int(lid):
          continue
        if int(lid) > int(laneId) > 0 or int(lid) < int(laneId) < 0:
          continue
        for carInfo in infos:
          pos = carInfo["pos"]
          if pos >= s0 and pos < s1:
            hdg = odr.findHdg(id, pos)
            ds = pos-s0
            dw = delta[0]+delta[1]*ds+delta[2]*ds**2+delta[3]*ds**3
            dw = dw if laneId != lid else dw/2
            carId = carInfo["carId"]
            ordId = carInfo["ordId"]
            car = det.data["agents"][carId]
            ord = None

            if car['uid'] != None:
              if ordId == 0:
                ord = car['transform']
              else:
                ord = car['destinationPoint']
            else:
              if ordId == 0:
                ord = car['transform']
              else:
                ord = car['waypoints'][ordId-1]
            ord["position"]['x'] += dw*math.cos(hdg)
            ord["position"]['z'] += dw*math.sin(hdg)
            print(hdg, dw)
    return

def setChange(id, lid, di, maxStep, sameHdg, hdg):
  queue = deque()
  step = 0

  for info in odr.laneConnections[id][lid][int(di)]:
    queue.append({"id": info[0], 'lid': info[1], "di": info[2], "step": 0})

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    lid = item['lid']
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
      match odr.laneEdits[id][lid]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          odr.laneEdits[id][lid] = cons.BOTH_EDITED
          for info in odr.laneConnections[id][lid][0]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
          for info in odr.laneConnections[id][lid][1]:
            queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and not di:
      match odr.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          odr.laneEdits[id][lid] = cons.TAIL_EDITED
        case cons.HEAD_EDITED:
          odr.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in odr.laneConnections[id][lid][int(cons.TAIL)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})
    elif step == maxStep and di:
      match odr.laneEdits[id][lid]:
        case cons.NOT_EDITED:
          odr.laneEdits[id][lid] = cons.HEAD_EDITED
        case cons.TAIL_EDITED:
          odr.laneEdits[id][lid] = cons.BOTH_EDITED
        case _:
          continue
      for info in odr.laneConnections[id][lid][int(cons.HEAD)]:
        queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})