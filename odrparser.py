import xml.etree.ElementTree as ET
import copy
import path
from collections import deque, defaultdict
from constants import *
from scipy.optimize import root_scalar

trees = deque()
def updateTrees(new_val):
  trees.append(copy.deepcopy(new_val))
  if len(trees) > 256:
    trees.popleft()
def redoTrees():
  if len(trees) > 1:
    trees.pop()
def clearTrees():
  trees.clear()

root = None
def updateRoot(new_val):
  global root
  root = new_val

roads = defaultdict(dict)
roadConnections = defaultdict(dict)
laneConnections = defaultdict(dict)
roadEdits = defaultdict(dict)
laneEdits = defaultdict(dict)
roadBackup = defaultdict(dict)
laneBackup = defaultdict(dict)
hdgs = defaultdict(dict)

def writeXodr():
  trees[-1].write(path.PATH+path.saveName+"_test.xodr", encoding="utf-8", xml_declaration=True)
  print('Already saved.')

def openXodr(name):
  tree = None 
  try:
    tree = ET.parse(path.PATH+name+".xodr")
  except Exception:
    print("File not found!")
    return False
  clearTrees()
  updateTrees(tree)
  updateRoot(trees[-1].getroot())
  updateData()
  return True

def updateData():
  clearAll()
  tmpJSets = {}
  for road in root.iter('road'):
    id = road.get('id')
    roads[id] = road
    hdgUpdate(road.findall('.//geometry'), id)

    roadConnections[id] = [[], []]
    roadBackup[id] = cons.NOT_EDITED
    laneConnections[id] = {}
    laneBackup[id] = {}
    tmpJSets[id] = [-1, -1]
    for lane in road.findall('.//lane'):
      lid = lane.get('id')
      if lid != '0':
        laneBackup[id][lid] = cons.NOT_EDITED
        laneConnections[id][lid] = [[], []]

  for road in root.iter('road'):
    id = road.get('id')
    link = road.find('link')
    lanes = road.findall('.//lane')
    roadUpdate(id, link, lanes, tmpJSets, cons.TAIL)
    roadUpdate(id, link, lanes, tmpJSets, cons.HEAD)
      
  for junction in root.iter('junction'):
    id = junction.get('id')
    connections = junction.findall('connection')
    junctionUpdate(id, connections, tmpJSets)

def pushNewTree():
  roads.clear()
  updateTrees(trees[-1])
  updateRoot(trees[-1].getroot())
  for road in root.iter('road'):
    id = road.get('id')
    roads[id] = road

def getLength(param, t):
  bU, cU, dU, bV, cV, dV = param
  def integrand(p):
    du = bU+2*cU*p+3*dU*p**2
    dv = bV+2*cV*p+3*dV*p**2
    return numpy.sqrt(du**2+dv**2)
  length, _ = quad(integrand, 0, t)
  return length

def getT(param, length):
  def objective(t):
    return getLength(param, t)-length
  if length == 0:
    return 0
  sol = root_scalar(objective, bracket=[0, 1], method='brentq')
  return sol.root

def findHdg(id, pos):
  road = roads[id]
  gs = road.find('planView').findall('geometry')
  for i in range(len(gs)):
    s0 = getData(gs[i], 's')
    s1 = getData(road, 'length') if i == len(gs) else getData(gs[i+1], 's')
    if s0 <= pos < s1:
      if gs[i].find('line') != None:
        return getData(gs[i], 'hdg')
      poly = gs[i].find('paramPoly3')
      bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
      bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
      t = getT([bU, cU, dU, bV, cV, dV], pos-s0)
      du_dt = bU+2*cU*t+3*dU*t**2
      dv_dt = bV+2*cV*t+3*dV*t**2
      deltaH = math.atan2(dv_dt, du_dt)
      return (deltaH+getData(gs[i], 'hdg'))%(2*math.pi)
  return 0

# PRIVATE FUNCTION

def clearAll():
  roads.clear()
  roadConnections.clear()
  laneConnections.clear()
  roadBackup.clear()
  laneBackup.clear()
  hdgs.clear()

def hdgUpdate(gs, id):
  h0 = getData(gs[0],  'hdg')
  h1 = getData(gs[-1], 'hdg')
  poly1 = gs[-1].find('paramPoly3')
  if poly1 != None:
    bU, cU, dU = getData(poly1, 'bU'), getData(poly1, 'cU'), getData(poly1, 'dU')
    bV, cV, dV = getData(poly1, 'bV'), getData(poly1, 'cV'), getData(poly1, 'dV')
    h1 = (h1+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)
  hdgs[id] = []
  hdgs[id].append(h0)
  hdgs[id].append(h1)

def roadUpdate(id, link, lanes, tmpJSets, dir):
  p_s = link.find('predecessor')
  if dir == cons.HEAD:
    p_s = link.find('successor')
  
  if p_s != None:
    direction = int(p_s.get("contactPoint") == "end")
    p_sId = p_s.get("elementId")
    if p_s.get("elementType") == "road":
      if [p_sId, direction] not in roadConnections[id][dir]:
        roadConnections[id][dir].append([p_sId, direction])
      if [id, dir] not in roadConnections[p_sId][direction]:
        roadConnections[p_sId][direction].append([id, dir])
      for lane in lanes:
        lid = lane.get('id')
        llink = lane.find('link')
        lp_s = llink.find('predecessor')
        if dir == cons.HEAD:
          lp_s = llink.find('successor')

        if lp_s != None:
          p_sLid = lp_s.get('id')
          if [p_sId, p_sLid, direction] not in laneConnections[id][lid][dir]:
            laneConnections[id][lid][dir].append([p_sId, p_sLid, direction])
          if [id, lid, dir] not in laneConnections[p_sId][p_sLid][direction]:    
            laneConnections[p_sId][p_sLid][direction].append([id, lid, dir])
    else:
      tmpJSets[id][dir] = p_s.get("elementId")

def junctionUpdate(id, connections, tmpJSets):
  for connection in connections:
    direction = int(connection.get("contactPoint") == "end")
    incId = connection.get('incomingRoad'  )
    conId = connection.get('connectingRoad')
    point = int(tmpJSets[incId][1] == id)
    incLid = connection.find('laneLink').get('from')
    conLid = connection.find('laneLink').get('to'  )
    if [conId, conLid, direction] not in laneConnections[incId][incLid][point]:
      laneConnections[incId][incLid][point].append([conId, conLid, direction])
    if [conId, direction] not in roadConnections[incId][point]:
      roadConnections[incId][point].append([conId, direction])