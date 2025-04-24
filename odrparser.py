import xml.etree.ElementTree as ET
import copy
from collections import deque, defaultdict
from constants import *

saveName = 'test'

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

def write():
  trees[-1].write(PATH+saveName+"_test.xodr", encoding="utf-8", xml_declaration=True)
  print('Already saved.')

def openXodr(name):
  tree = None 
  try:
    tree = ET.parse(PATH+'selected_map\\'+name+".xodr")
  except Exception:
    print("File not found!")
    return False
  global saveName
  saveName = name
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