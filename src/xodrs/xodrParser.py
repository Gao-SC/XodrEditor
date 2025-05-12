import xml.etree.ElementTree as ET
import copy
import math
import numpy

from collections import deque, defaultdict
from utils.definitions import *
from utils.lambdas import *
import utils.path as path

class xodrParser:
  def __init__(self):
    self.data = deque()
    self.root = None
    self.roads = defaultdict(dict)
    self.roadConnections = defaultdict(dict)
    self.laneConnections = defaultdict(dict)
    self.roadEdits = defaultdict(dict)
    self.laneEdits = defaultdict(dict)
    self.roadBackup = defaultdict(dict)
    self.laneBackup = defaultdict(dict)
    self.hdgs = defaultdict(dict)

  def addData(self, new_val):
    self.data.append(copy.deepcopy(new_val))
    if len(self.data) > 256:
      self.data.popleft()
    self.root = self.data[-1].getroot()
  def undo(self):
    if len(self.data) > 1:
      self.data.pop()

  def writeXodr(self):
    self.data[-1].write(path.savePath+path.saveName+"_test.xodr", encoding="utf-8", xml_declaration=True)
    print('Already saved.')

  def openXodr(self, name):
    try:
      data = ET.parse(path.readPath+name+".xodr")
    except FileNotFoundError:
      print("Error: File not found!")
      return False
    except ET.ParseError:
      print("Error: Invalid XODR format!")
      return False
    self.clearAll()
    self.addData(data)
    self.updateData()
    return True

  def updateData(self):
    tmpJSets = {}
    for road in self.root.iter('road'):
      id = road.get('id')
      self.roads[id] = road
      self.hdgUpdate(road.findall('.//geometry'), id)

      self.roadConnections[id] = [[], []]
      self.roadBackup[id] = defs.NOT_EDITED
      self.laneConnections[id] = {}
      self.laneBackup[id] = {}
      tmpJSets[id] = [-1, -1]
      for lane in road.findall('.//lane'):
        lid = lane.get('id')
        if lid != '0':
          self.laneBackup[id][lid] = defs.NOT_EDITED
          self.laneConnections[id][lid] = [[], []]

    for road in self.root.iter('road'):
      id = road.get('id')
      link = road.find('link')
      lanes = road.findall('.//lane')
      self.roadUpdate(id, link, lanes, tmpJSets, defs.TAIL)
      self.roadUpdate(id, link, lanes, tmpJSets, defs.HEAD)
        
    for junction in self.root.iter('junction'):
      id = junction.get('id')
      connections = junction.findall('connection')
      self.junctionUpdate(id, connections, tmpJSets)

  def pushNewData(self):
    self.roads.clear()
    self.addData(self.data[-1])
    for road in self.root.iter('road'):
      id = road.get('id')
      self.roads[id] = road

  # PRIVATE FUNCTION

  def clearAll(self):
    self.data.clear()
    self.roads.clear()
    self.roadConnections.clear()
    self.laneConnections.clear()
    self.roadBackup.clear()
    self.laneBackup.clear()
    self.hdgs.clear()

  def hdgUpdate(self, gs, id):
    h0 = getData(gs[0],  'hdg')
    h1 = getData(gs[-1], 'hdg')
    poly1 = gs[-1].find('paramPoly3')
    if poly1 != None:
      bU, cU, dU = getData(poly1, 'bU'), getData(poly1, 'cU'), getData(poly1, 'dU')
      bV, cV, dV = getData(poly1, 'bV'), getData(poly1, 'cV'), getData(poly1, 'dV')
      h1 = (h1+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)
    self.hdgs[id] = []
    self.hdgs[id].append(h0)
    self.hdgs[id].append(h1)

  def roadUpdate(self, id, link, lanes, tmpJSets, dir):
    p_s = link.find('predecessor')
    if dir == defs.HEAD:
      p_s = link.find('successor')
    
    if p_s != None:
      direction = int(p_s.get("contactPoint") == "end")
      p_sId = p_s.get("elementId")
      if p_s.get("elementType") == "road":
        if [p_sId, direction] not in self.roadConnections[id][dir]:
          self.roadConnections[id][dir].append([p_sId, direction])
        if [id, dir] not in self.roadConnections[p_sId][direction]:
          self.roadConnections[p_sId][direction].append([id, dir])
        for lane in lanes:
          lid = lane.get('id')
          llink = lane.find('link')
          lp_s = llink.find('predecessor')
          if dir == defs.HEAD:
            lp_s = llink.find('successor')

          if lp_s != None:
            p_sLid = lp_s.get('id')
            if [p_sId, p_sLid, direction] not in self.laneConnections[id][lid][dir]:
              self.laneConnections[id][lid][dir].append([p_sId, p_sLid, direction])
            if [id, lid, dir] not in self.laneConnections[p_sId][p_sLid][direction]:    
              self.laneConnections[p_sId][p_sLid][direction].append([id, lid, dir])
      else:
        tmpJSets[id][dir] = p_s.get("elementId")

  def junctionUpdate(self, id, connections, tmpJSets):
    for connection in connections:
      direction = int(connection.get("contactPoint") == "end")
      incId = connection.get('incomingRoad'  )
      conId = connection.get('connectingRoad')
      point = int(tmpJSets[incId][1] == id)
      incLid = connection.find('laneLink').get('from')
      conLid = connection.find('laneLink').get('to'  )
      if [conId, conLid, direction] not in self.laneConnections[incId][incLid][point]:
        self.laneConnections[incId][incLid][point].append([conId, conLid, direction])
      if [conId, direction] not in self.roadConnections[incId][point]:
        self.roadConnections[incId][point].append([conId, direction])

XParser = xodrParser()