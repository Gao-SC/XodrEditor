import xml.etree.ElementTree as ET
from collections import deque
import copy

from editor.editor import editor
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from Json.carDetector import detector
from utils.constants import *

class editorWidth(editor):
  def __init__(self):
    pass
      
  ## 修改指定道路的指定车道的宽度.
  ## 默认仅有一个LaneSection.
  ## 因车道宽度不均匀可能导致按比例改变宽度时, 可能会出现道路宽度无法对齐的情况, 因此删除了按比例拓宽选项.
  def edit(self, id, value, smooth=0, maxStep=0, sameHdg=0, laneIds=[]):
    if id == "random":
      detector.setCandidates()
      id, lid = detector.getRandomId2()
      laneIds = [lid]

    XParser.laneEdits = copy.deepcopy(XParser.laneBackup)
    if laneIds == []:
      for lid in XParser.laneEdits[id].keys():
        XParser.laneEdits[id][lid] = cons.BOTH_EDITED
        self.setChange(id, lid, cons.TAIL, maxStep, sameHdg, XParser.hdgs[id][0])
        self.setChange(id, lid, cons.HEAD, maxStep, sameHdg, XParser.hdgs[id][1])
      value = value/len(XParser.laneEdits[id].values())
    else:
      for lid in laneIds:
        XParser.laneEdits[id][lid] = cons.BOTH_EDITED
        self.setChange(id, lid, cons.TAIL, maxStep, sameHdg, XParser.hdgs[id][0])
        self.setChange(id, lid, cons.HEAD, maxStep, sameHdg, XParser.hdgs[id][1])
      value = value/len(laneIds)

    for rid, rEdit in XParser.laneEdits.items():
      for lid, info in rEdit.items():
        if info == cons.TAIL_EDITED and smooth:
          self.setLaneWidth(rid, lid, value, 'addt')
        elif info == cons.HEAD_EDITED and smooth:
          self.setLaneWidth(rid, lid, value, 'addh')
        elif info == cons.BOTH_EDITED:
          self.setLaneWidth(rid, lid, value, 'add')

  def setLaneWidth(self, id, lid, value, mode):
    road = XParser.roads[id]
    length = getData(road, 'length')
    # 选取所有sections (默认情况下, 道路将仅有一个laneSection).
    sections = road.find('lanes').findall('laneSection')
    for section in sections:
      section = road.find('lanes').find('laneSection')
      S = getData(section, 's')

      for lane in section.findall('.//lane'):
        if lane.get('id') != lid:
          continue
        widths = lane.findall('width')
        widthNum = len(widths)
          
        for j in range(widthNum):
          delta = [0, 0, 0, 0]
          match mode:
            case 'add':
              delta = self.editWidth(widths[j], value, 'add')
            case 'addt':
              delta = self.editWidth(widths[j], value, 'stail', length)
            case 'addh':
              delta = self.editWidth(widths[j], value, 'shead', length)
          
          s0 = S+getData(widths[j], "sOffset")
          s1 = S+getData(road, "length") if j == widthNum-1 else getData(widths[j+1], "sOffset")

          for laneId, infos in JParser.carPosition[-1][id].items():
            if int(laneId) < 0 < int(lid) or int(laneId) > 0 > int(lid):
              continue
            if int(lid) > int(laneId) > 0 or int(lid) < int(laneId) < 0:
              continue
            for carInfo in infos:
              pos = carInfo["pos"]
              if pos >= s0 and pos < s1:
                hdg = XParser.findHdg(id, pos)
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
        break

  def setChange(self, id, lid, di, maxStep, sameHdg, hdg):
    queue = deque()
    step = 0

    for info in XParser.laneConnections[id][lid][int(di)]:
      queue.append({"id": info[0], 'lid': info[1], "di": info[2], "step": 0})

    while len(queue) > 0:
      item = queue.popleft()
      id = item['id']
      lid = item['lid']
      di = item['di']
      step = item['step']

      if sameHdg:
        angle0 = (XParser.hdgs[id][0]-hdg)%(2*math.pi)
        angle1 = (XParser.hdgs[id][1]-hdg)%(2*math.pi)
        m1, m2, m3, m4 = math.pi/4, math.pi/4*3, math.pi/4*5, math.pi/4*7
        if angle0 > m1 and angle0 < m2 or angle0 > m3 and angle0 < m4:
          step = maxStep
        elif angle1 > m1 and angle1 < m2 or angle1 > m3 and angle1 < m4:
          step = maxStep

      if step < maxStep:
        match XParser.laneEdits[id][lid]:
          case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
            XParser.laneEdits[id][lid] = cons.BOTH_EDITED
            for info in XParser.laneConnections[id][lid][0]:
              queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
            for info in XParser.laneConnections[id][lid][1]:
              queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step+1})
          case _:
            continue
      
      elif step == maxStep and not di:
        match XParser.laneEdits[id][lid]:
          case cons.NOT_EDITED:
            XParser.laneEdits[id][lid] = cons.TAIL_EDITED
          case cons.HEAD_EDITED:
            XParser.laneEdits[id][lid] = cons.BOTH_EDITED
          case _:
            continue
        for info in XParser.laneConnections[id][lid][int(cons.TAIL)]:
          queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})
      elif step == maxStep and di:
        match XParser.laneEdits[id][lid]:
          case cons.NOT_EDITED:
            XParser.laneEdits[id][lid] = cons.HEAD_EDITED
          case cons.TAIL_EDITED:
            XParser.laneEdits[id][lid] = cons.BOTH_EDITED
          case _:
            continue
        for info in XParser.laneConnections[id][lid][int(cons.HEAD)]:
          queue.append({"id": info[0], "lid": info[1], "di": info[2], "step": step})

  def editWidth(self, width: ET.Element, value, mode, length=0):
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
      
## TODO: 将修改json和xodr的部分集成到jsonParser和xodrParser中