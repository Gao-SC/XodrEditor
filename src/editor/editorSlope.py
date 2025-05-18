from collections import deque
import copy
import math

from editor.editor import editor
from xodrs.xodrParser import XParser
from jsons.jsonParser import JParser
from jsons.jsonDataGetter import jDataGetter

from utils.definitions import *
from utils.lambdas import *

class editorSlope(editor):
  def __init__(self):
    editor.__init__(self)

  def edit(self, id, value, mode, move, maxStep=0, sameHdg=0):
    if mode == 'mul' and move == defs.MOVE_BOTH:
      print('Params error!')
      return

    XParser.roadEdits = copy.deepcopy(XParser.roadBackup)
    XParser.roadEdits[id] = defs.BOTH_LOCKED
    
    road = XParser.roads[id]
    link = road.find('link')
    pre = link.find('predecessor')
    suc = link.find('successor')
    if move == defs.MOVE_HEAD and pre != None: 
      self.lockChange(defs.TAIL, id)
    if move == defs.MOVE_TAIL and suc != None: 
      self.lockChange(defs.HEAD, id)

    if move != defs.MOVE_HEAD and pre != None:
      hdg = XParser.hdgs[id][0]
      self.setChange(id, defs.TAIL, maxStep, sameHdg, hdg)
    if move != defs.MOVE_TAIL and suc != None:
      hdg = XParser.hdgs[id][1]
      self.setChange(id, defs.HEAD, maxStep, sameHdg, hdg)
    
    value = value if mode != 'mul' else value*getData(road, 'length')
    self.setRoadSlope(id, value, move)
    for newId in XParser.roads.keys():
      num = XParser.roadEdits[newId]
      if num == defs.TAIL_EDITED or num == defs.TAIL_EDITED2:   # change tail
        self.setRoadSlope(newId, value, defs.MOVE_TAIL)
      elif num == defs.HEAD_EDITED or num == defs.HEAD_EDITED2: # change head
        self.setRoadSlope(newId, value, defs.MOVE_HEAD)
      elif num == defs.BOTH_EDITED:                             # change both
        self.setRoadSlope(newId, value, defs.MOVE_BOTH)

  def setRoadSlope(self, id, value, move):
    road = XParser.roads[id]
    elevations = road.find('elevationProfile').findall('elevation')
    elevaNum = len(elevations)
    length = getData(road, 'length')

    slope = 0
    if move == defs.MOVE_TAIL:
      slope = value/length*-1
    elif move == defs.MOVE_HEAD:
      slope = value/length
      
    for i in range(elevaNum):
      e = elevations[i]
      s0 = getData(e, 's')
      s1 = getData(road, "length") if i == elevaNum-1 else getData(elevations[i+1], "s")

      setData(e, 'b', getData(e, 'b')+slope)
      if move == defs.MOVE_BOTH:
        setData(e, 'a', getData(e, 'a')+value)
      elif move == defs.MOVE_TAIL:
        setData(e, 'a', getData(e, 'a')+slope*(s0-length))
      elif move == defs.MOVE_HEAD:
        setData(e, 'a', getData(e, 'a')+slope*s0)

      # rectify the cars' position:
      for infos in JParser.carPosition[-1][id].values():
        for carInfo in infos:
          pos = carInfo["pos"]
          if pos >= s0 and pos < s1:
            de = value
            if move == defs.MOVE_TAIL:
              de = slope*(s0-length)
            elif move == defs.MOVE_HEAD:
              de = slope*s0

            ord = jDataGetter.getOrd(carInfo)
            ord["position"]['y'] += de
            if ord.get("angle") != None:
              ord["angle"]["x"] += hdg2ang(math.atan(slope))
            else:
              ord["rotation"]["x"] += hdg2ang(math.atan(slope))

  def lockChange(self, direction, id):
    for info in XParser.roadConnections[id][direction]:
      if info[1]:
        XParser.roadEdits[info[0]] = defs.HEAD_LOCKED
      else:
        XParser.roadEdits[info[0]] = defs.TAIL_LOCKED

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
          case defs.NOT_EDITED | defs.TAIL_EDITED | defs.HEAD_EDITED:
            XParser.roadEdits[id] = defs.BOTH_EDITED
            for info in XParser.roadConnections[id][0]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
            for info in XParser.roadConnections[id][1]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case defs.TAIL_LOCKED:
            XParser.roadEdits[id] = defs.HEAD_EDITED2
            for info in XParser.roadConnections[id][defs.HEAD]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case defs.HEAD_LOCKED:
            XParser.roadEdits[id] = defs.TAIL_EDITED2
            for info in XParser.roadConnections[id][defs.TAIL]:
              queue.append({"id": info[0], "di": info[1], "step": step+1})
          case _:
            continue
      
      elif step == maxStep and di == defs.TAIL:
        match XParser.roadEdits[id]:
          case defs.NOT_EDITED:
            XParser.roadEdits[id] = defs.TAIL_EDITED
          case defs.HEAD_LOCKED:
            XParser.roadEdits[id] = defs.TAIL_EDITED2
          case defs.HEAD_EDITED:
            XParser.roadEdits[id] = defs.BOTH_EDITED
          case _:
            continue
        for info in XParser.roadConnections[id][defs.TAIL]:
          queue.append({"id": info[0], "di": info[1], "step": step})
      elif step == maxStep and di == defs.HEAD:
        match XParser.roadEdits[id]:
          case defs.NOT_EDITED:
            XParser.roadEdits[id] = defs.HEAD_EDITED
          case defs.TAIL_LOCKED:
            XParser.roadEdits[id] = defs.HEAD_EDITED2
          case defs.TAIL_EDITED:
            XParser.roadEdits[id] = defs.BOTH_EDITED
          case _:
            continue
        for info in XParser.roadConnections[id][defs.HEAD]:
          queue.append({"id": info[0], "di": info[1], "step": step})