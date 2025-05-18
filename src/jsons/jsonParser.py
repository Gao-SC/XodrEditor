from scipy.optimize import root_scalar
from collections import deque, defaultdict
import numpy as np
import copy
import math
import json

from xodrs.xodrParser import XParser
from xodrs.xodrDataGetter import xDataGetter

import utils.path as path
from utils.lambdas import *

class jsonParser:
  def __init__(self):
    self.data = deque()
    self.carPosition = deque()
    self.egoTs = []
    self.egoDs = []

  def addData(self, new_val):
    self.data.append(copy.deepcopy(new_val))
    if len(self.data) > 256:
      self.data.popleft()
      
  def addCarData(self, new_val):
    self.carPosition.append(copy.deepcopy(new_val))
    if len(self.carPosition) > 256:
      self.carPosition.popleft()

  def undo(self):
    if len(self.data) > 1:
      self.data.pop()
      self.carPosition.pop()

  def clearAll(self):
    self.data.clear()
    self.carPosition.clear()
    self.egoTs.clear()
    self.egoDs.clear()

  def pushNewData(self):
    self.addData(self.data[-1])
    self.addCarData(self.carPosition[-1])

  def readJson(self, name):
    print("FINDING THE POSITION OF CARS...")
    try:
      with open(path.jsonPath+name+".json", 'r') as file:
        jsonData = json.load(file)
    except FileNotFoundError:
      print(f"Error: File not found: {path.jsonPath+name}.xodr")
      return False
    except json.JSONDecodeError:
      print("Error: Invalid JSON format!")
      return False
    self.clearAll()
    self.addData(jsonData)
    # self.rectifyJsonData()
    self.updateCarData()
    return True

  def updateCarData(self):
    carInfos = defaultdict(dict)
    for id, road in XParser.roads.items():
      carInfos[id] = defaultdict(dict)
      lanes = road.find("lanes").findall(".//lane")
      for lane in lanes:
        carInfos[id][lane.get('id')] = []
        
    agents = self.data[-1]["agents"]
    for i in range(len(agents)):
      tPos = agents[i]["transform"]["position"]
      tRot = agents[i]["transform"]["rotation"]
      carT = self.findRoad(tPos, tRot)

      if agents[i]["uid"] != "":
        dPos = agents[i]["destinationPoint"]["position"]
        dRot = agents[i]["destinationPoint"]["rotation"]
        carD = self.findRoad(dPos, dRot)
        if carT != None and carD != None:
          self.egoTs.append([carT[0], carT[1], len(carInfos[carT[0]][carT[1]])])
          self.egoDs.append([carD[0], carD[1], len(carInfos[carD[0]][carD[1]])])
          carInfos[carT[0]][carT[1]].append({"carId": i, "ordId": 0, "pos": carT[2], "dis": carT[3]})
          carInfos[carD[0]][carD[1]].append({"carId": i, "ordId": 1, "pos": carD[2], "dis": carD[3]})
        else:
          print("Ego not found: ", i)

      else:
        if carT != None:
          carInfos[carT[0]][carT[1]].append({"carId": i, "ordId": 0, "pos": carT[2], "dis": carT[3]})
        else:
          print("Not found: ", i, " ", 0) 
        if "waypoints" in agents[i]:
          wayPoints = agents[i]["waypoints"]
          for j in range(len(wayPoints)):
            pos = wayPoints[j]["position"]
            rot = wayPoints[j]["angle"]
            point = self.findRoad(pos, rot)
            if point != None:
              carInfos[point[0]][point[1]].append({"carId": i, "ordId": j+1, "pos": point[2], "dis": point[3]})
            else:
              print("Not found: ", i, " ", j+1)

    print("FINDING ENDED.")
    self.addCarData(carInfos)

  def writeJson(self):
    with open(path.savePath+path.saveName+"_test.json", 'w') as file:
      json.dump(self.data[-1], file, indent=4)
      file.write('\n')

  def rectifyJsonData(self):
    agents = self.data[-1]["agents"]
    index, length = 0, len(agents)
    for i in range(length):
      index = i
      if agents[i]["uid"] != "":
        agents[i]["initial_speed"] = 0
      else:
        break
    for i in range(index, length):
      agents.pop()

  def editSaveName(self, saveName):
    map = self.data[-1]["map"]
    map["name"] = saveName
    
  ## PRIVATE METHOD
  def findRoad(self, pos, rot):
    candidateRoads = []
    for id, road in XParser.roads.items():
      ans, ansL = self.projectPoint(road, pos['x'], pos['z'])
      if ans == float('inf'):
        continue

      lws, rws = xDataGetter.getPosWidths(road, ansL)
      hdg = xDataGetter.getPosHdg(road, ansL)
      LHT = road.find('rule') == "LHT"
      if ans < 0 ^ LHT: hdg = (hdg+math.pi)%(2*math.pi)
      if 'y' in rot:
        carHdg = ang2hdg(rot['y'])
        deltaHdg = min(2*math.pi-abs(hdg-carHdg), abs(hdg-carHdg))
      else:
        deltaHdg = 0
    
      if ans <= 0: #道路左侧
        for i in range(len(lws)):
          if ans > lws[i]:
            candidateRoads.append([id, str(i+1),  ansL, ans, deltaHdg])
            break
      else:
        for i in range(len(rws)):
          if ans < rws[i]:
            candidateRoads.append([id, str(-i-1), ansL, ans, deltaHdg])
            break

    if candidateRoads:
      candidateRoads.sort(key=lambda x: abs(x[3])+x[4])
      return candidateRoads[0]
    else:
      return None

  def projectPoint(self, road, tarX, tarY):
    gs = road.find('planView').findall('geometry')
    ans, ansL = float('inf'), 0
    maxWidth = XParser.maxWidths[road.get('id')]
    
    for g in gs:
      h    = getData(g, 'hdg')
      x, y = getData(g, 'x'), getData(g, 'y')
      l    = getData(g, 'length')
      dis, pos = 0, 0

      if math.hypot(x-tarX, y-tarY) > l+maxWidth:
        continue

      if g.find('line') != None:
        a = math.cos(h)
        b = math.sin(h)
        dis = b*(tarX-x)-a*(tarY-y)
        pos = a*(tarX-x)+b*(tarY-y)

        epsilon = 1e-2
        if  -epsilon < pos < 0:
          pos = 0
        if l < pos < l+epsilon:
          pos = l
        if pos < 0 or pos > l:
          continue

      else:
        poly = g.find('paramPoly3')
        bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
        bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
        length = getData(g, 'length')
        cosH, sinH = math.cos(h), math.sin(h)

        def compute_uv(t):
          u = bU*t + cU*t**2 + dU*t**3
          v = bV*t + cV*t**2 + dV*t**3
          du_dt = bU + 2*cU*t + 3*dU*t**2
          dv_dt = bV + 2*cV*t + 3*dV*t**2
          return u, v, du_dt, dv_dt
        def F(t):
          u, v, du_dt, dv_dt = compute_uv(t)
          x_t = x + u*cosH - v*sinH
          y_t = y + u*sinH + v*cosH
          dx_dt = du_dt*cosH - dv_dt*sinH
          dy_dt = du_dt*sinH + dv_dt*cosH
          return (x_t-tarX)*dx_dt + (y_t-tarY)*dy_dt
        
        epsilon, N = 1e-4, math.ceil(length*20)
        roots = []
        t_values = np.linspace(0, 1, N+1)
        f_values = [F(t) for t in t_values]
        for i in range(len(t_values)):
          t = t_values[i]
          if abs(f_values[i]) < epsilon:
            roots.append(t)

        sign_changes = []
        for i in range(N):
          t0, t1 = t_values[i], t_values[i+1]
          f0, f1 = f_values[i], f_values[i+1]
          if f0 * f1 < 0:
            sign_changes.append([t0, t1])

        for interval in sign_changes:
          try:
            result = root_scalar(F, method='brentq', bracket=interval)
            if result.converged:
              roots.append(result.root)
          except:
            continue
        
        roots = np.unique(np.round(roots, 5))
        roots = np.clip(roots, 0, 1)
        roots = np.unique(roots)

        dis, T = float('inf'), 0
        for tRoot in roots:
          u, v, du_dt, dv_dt = compute_uv(tRoot)
          x_t = x + u*cosH - v*sinH
          y_t = y + u*sinH + v*cosH
          dx_dt = du_dt*cosH - dv_dt*sinH
          dy_dt = du_dt*sinH + dv_dt*cosH
          if abs(dis) > math.hypot(x_t-tarX, y_t-tarY):
            T = tRoot
            dis = math.hypot(x_t-tarX, y_t-tarY)
            if dx_dt*(tarY-y_t) > dy_dt*(tarX-x_t):
              dis *= -1
        pos = xDataGetter.poly3ToLength([bU, cU, dU, bV, cV, dV], T)

      if abs(ans) > abs(dis):
        ans = dis
        ansL = pos+getData(g, "s")
    return ans, ansL
  
JParser = jsonParser()