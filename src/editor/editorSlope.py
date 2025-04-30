from collections import deque
import copy

from editor.editor import editor
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from Json.carDetector import detector

from utils.constants import *

class editorSlope(editor):
  def __init__(self):
    pass

  def edit(self, id, value, mode, move, maxStep=0, sameHdg=0):
    if mode == 'mul' and move == cons.MOVE_BOTH:
      print('Params error!')
      return
    
    if id == "random":
        detector.setCandidates()
        id = detector.getRandomId1()

    XParser.roadEdits = copy.deepcopy(XParser.roadBackup)
    XParser.roadEdits[id] = cons.BOTH_LOCKED
    
    road = XParser.roads[id]
    link = road.find('link')
    pre = link.find('predecessor')
    suc = link.find('successor')
    if move == cons.MOVE_HEAD and pre != None: 
      self.lockChange(cons.TAIL, id)
    if move == cons.MOVE_TAIL and suc != None: 
      self.lockChange(cons.HEAD, id)

    if move != cons.MOVE_HEAD and pre != None:
      hdg = XParser.hdgs[id][0]
      self.setChange(id, cons.TAIL, maxStep, sameHdg, hdg)
    if move != cons.MOVE_TAIL and suc != None:
      hdg = XParser.hdgs[id][1]
      self.setChange(id, cons.HEAD, maxStep, sameHdg, hdg)
    
    value = value if mode != 'mul' else value*getData(road, 'length')
    self.setRoadSlope(id, value, move)
    for r in XParser.root.iter('road'):
      newId = r.get('id')
      num = XParser.roadEdits[newId]
      if num == cons.TAIL_EDITED or num == cons.TAIL_EDITED2:   # change tail
        self.setRoadSlope(newId, value, cons.MOVE_TAIL)
      elif num == cons.HEAD_EDITED or num == cons.HEAD_EDITED2: # change head
        self.setRoadSlope(newId, value, cons.MOVE_HEAD)
      elif num == cons.BOTH_EDITED:                             # change both
        self.setRoadSlope(newId, value, cons.MOVE_BOTH)

  def setRoadSlope(self, id, value, move):
    print(id, value, move)
    
    road = XParser.roads[id]
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

      for infos in JParser.carPosition[-1][id].values():
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

  def lockChange(self, direction, id):
    for info in XParser.roadConnections[id][direction]:
      if info[1]:
        XParser.roadEdits[info[0]] = cons.HEAD_LOCKED
      else:
        XParser.roadEdits[info[0]] = cons.TAIL_LOCKED

  def setChange(self, id, di, maxStep, sameHdg, hdg):
    queue = deque()

    for info in XParser.roadConnections[id][di]:
      queue.append({"id": info[0], "di": info[1], "step": 0})

    while len(queue) > 0:
      item = queue.popleft()
      id = item['id']
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
        match XParser.roadEdits[id]:
          case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
            XParser.roadEdits[id] = cons.BOTH_EDITED
            for info in XParser.roadConnections[id][0]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
            for info in XParser.roadConnections[id][1]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case cons.TAIL_LOCKED:
            XParser.roadEdits[id] = cons.HEAD_EDITED2
            for info in XParser.roadConnections[id][cons.HEAD]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case cons.HEAD_LOCKED:
            XParser.roadEdits[id] = cons.TAIL_EDITED2
            for info in XParser.roadConnections[id][cons.TAIL]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case _:
            continue
      
      elif step == maxStep and di == cons.TAIL:
        match XParser.roadEdits[id]:
          case cons.NOT_EDITED:
            XParser.roadEdits[id] = cons.TAIL_EDITED
          case cons.HEAD_LOCKED:
            XParser.roadEdits[id] = cons.TAIL_EDITED2
          case cons.HEAD_EDITED:
            XParser.roadEdits[id] = cons.BOTH_EDITED
          case _:
            continue
        for info in XParser.roadConnections[id][cons.TAIL]:
          queue.append({"id": info[0], "di": info[1], "step": step})
      elif step == maxStep and di == cons.HEAD:
        match XParser.roadEdits[id]:
          case cons.NOT_EDITED:
            XParser.roadEdits[id] = cons.HEAD_EDITED
          case cons.TAIL_LOCKED:
            XParser.roadEdits[id] = cons.HEAD_EDITED2
          case cons.TAIL_EDITED:
            XParser.roadEdits[id] = cons.BOTH_EDITED
          case _:
            continue
        for info in XParser.roadConnections[id][cons.HEAD]:
          queue.append({"id": info[0], "di": info[1], "step": step})