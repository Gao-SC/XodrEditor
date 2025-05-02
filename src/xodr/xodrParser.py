import xml.etree.ElementTree as ET
import copy
import math
import numpy

from scipy.optimize import root_scalar
from scipy.integrate import quad
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
  def redoData(self):
    if len(self.data) > 1:
      self.data.pop()
  def clearData(self):
    self.data.clear()

  def updateRoot(self, new_val):
    self.root = new_val

  def writeXodr(self):
    self.data[-1].write(path.openPath+path.saveName+"_test.xodr", encoding="utf-8", xml_declaration=True)
    print('Already saved.')

  def openXodr(self, name):
    tree = None 
    try:
      tree = ET.parse(path.openPath+name+".xodr")
    except Exception:
      print("File not found!")
      return False
    self.clearData()
    self.addData(tree)
    self.updateRoot(self.data[-1].getroot())
    self.updateData()
    return True

  def updateData(self):
    self.clearAll()
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
    self.updateRoot(self.data[-1].getroot())
    for road in self.root.iter('road'):
      id = road.get('id')
      self.roads[id] = road

  def getLength(self, param, t):
    bU, cU, dU, bV, cV, dV = param
    def integrand(p):
      du = bU+2*cU*p+3*dU*p**2
      dv = bV+2*cV*p+3*dV*p**2
      return numpy.sqrt(du**2+dv**2)
    length, _ = quad(integrand, 0, t)
    return length

  def getT(self, param, length):
    def objective(t):
      return self.getLength(param, t)-length
    if length == 0:
      return 0
    sol = root_scalar(objective, bracket=[0, 1], method='brentq')
    return sol.root

  def findHdg(self, id, pos):
    road = self.roads[id]
    gs = road.find('planView').findall('geometry')
    for i in range(len(gs)):
      s0 = getData(gs[i], 's')
      s1 = getData(road, 'length') if i == len(gs)-1 else getData(gs[i+1], 's')
      if s0 <= pos < s1:
        if gs[i].find('line') != None:
          return getData(gs[i], 'hdg')
        poly = gs[i].find('paramPoly3')
        bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
        bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
        t = self.getT([bU, cU, dU, bV, cV, dV], pos-s0)
        du_dt = bU+2*cU*t+3*dU*t**2
        dv_dt = bV+2*cV*t+3*dV*t**2
        deltaH = math.atan2(dv_dt, du_dt)
        return (deltaH+getData(gs[i], 'hdg'))%(2*math.pi)
    return 0

  # PRIVATE FUNCTION

  def clearAll(self):
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