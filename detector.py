from scipy.optimize import root_scalar
from collections import defaultdict
import numpy as np
import math
import json
import heapq

import path
import odrparser as odr
from constants import *

carInfos = defaultdict(dict)
egoTs, egoDs = [], []
data = None

def readJson(name):
  print("FINDING THE TARGET ROADS...")
  try:
    with open(path.PATH+name+".json", 'r') as file:
      # 初始化
      global data
      data = json.load(file)
      carInfos.clear()
      egoTs.clear()
      egoDs.clear()
      for id, road in odr.roads.items():
        carInfos[id] = defaultdict(dict)
        lanes = road.find("lanes").findall(".//lane")
        for lane in lanes:
          carInfos[id][lane.get('id')] = []
          
      agents = data["agents"]
      for i in range(len(agents)):
        tPos = agents[i]["transform"]["position"]
        tRot = agents[i]["transform"]["rotation"]
        carT = findRoad(tPos, tRot)
        if carT != None:
          carInfos[carT[0]][carT[1]].append({"carId": i, "ordId": 0, "pos": carT[2], "dis": carT[3]})
        else:
          print("Not found: ", i, " ", 0)

        if agents[i]["uid"] != "":
          dPos = agents[i]["destinationPoint"]["position"]
          dRot = agents[i]["destinationPoint"]["rotation"]
          carD = findRoad(dPos, dRot)
          egoTs.append(carT)
          egoDs.append(carD)
          if carD != None:
            carInfos[carD[0]][carD[1]].append({"carId": i, "ordId": 1, "pos": carD[2], "dis": carD[3]})
          else:
            print("Not found: ", i, " ", 1)
          
        else:
          wayPoints = agents[i]["waypoints"]
          for j in range(len(wayPoints)):
            pos = wayPoints[j]["position"]
            rot = wayPoints[j]["angle"]
            point = findRoad(pos, rot)
            if point != None:
              carInfos[point[0]][point[1]].append({"carId": i, "ordId": j+1, "pos": point[2], "dis": point[3]})
            else:
              print("Not found: ", i, " ", j+1)
        print("Done: ", i)
      return True
  
  except FileNotFoundError:
    print("Error: File not found!")
    return False
  except json.JSONDecodeError:
    print("Error: Invalid JSON format!")
    return False

def writeJson():
  with open(path.PATH+path.saveName+"_test.json", 'w') as file:
    json.dump(data, file, indent=4)
    file.write('\n')

def getOrd(carInfo):
  carId = carInfo["carId"]
  ordId = carInfo["ordId"]
  car = data["agents"][carId]
  if car['uid'] != "":
    if ordId == 0:
      return car['transform']
    else:
      return car['destinationPoint']
  else:
    if ordId == 0:
      return car['transform']
    else:
      return car['waypoints'][ordId-1]

## PRIVATE METHOD

def findRoad(pos, rot):
  candidateRoads = []
  for id, road in odr.roads.items():
    ans, ansL = projectPoint(road, pos['x'], pos['z'])
    if ans == float('inf'):
      continue
    lws, rws = getLanesWidth(road, ansL)
  
    if ans <= 0: #道路左侧
      for i in range(len(lws)):
        if ans > lws[i]:
          candidateRoads.append([id, str(i+1),  ansL, ans])
          break
    else:
      for i in range(len(rws)):
        if ans < rws[i]:
          candidateRoads.append([id, str(-i-1), ansL, ans])
          break
  if candidateRoads:
    candidateRoads.sort(key=lambda x: abs(x[3]))
    return candidateRoads[0]
  else:
    return None

def buildGRAPH():
  graph = defaultdict(dict)
  for id, road in odr.roads.items():
    length = getData(road, 'length')
    section = road.find('lanes').find('laneSection')
    
    lws0, rws0 = getLanesWidth(road, 0)
    lws1, rws1 = getLanesWidth(road, length)

    for lane in section.findall('.//lane'):
      lid = lane.get('id')
      if lid == "0":
        continue
      tailNode = f"road_{id}_lane_{lid}_0"
      headNode = f"road_{id}_lane_{lid}_1"
      if int(lid) < 0: # 右侧车道
        graph[tailNode][headNode] = length
      else:
        graph[headNode][tailNode] = length
      ## 变道
      for otherLane in section.findall('.//lane'):
        otherLid = lane.get('id')
        if otherLid == "0" or otherLid == lid or int(otherLid)*int(lid) < 0:
          continue
        otherTailNode = f"road_{id}_lane_{otherLid}_0"
        otherHeadNode = f"road_{id}_lane_{otherLid}_1"
        if int(lid) < 0: # 右侧车道
          graph[tailNode][otherTailNode] = abs(rws0[-int(lid)]-rws0[-int(otherLid)])
          graph[headNode][otherHeadNode] = abs(rws1[-int(lid)]-rws1[-int(otherLid)])
        else:
          graph[tailNode][otherTailNode] = abs(lws0[ int(lid)]-lws0[ int(otherLid)])
          graph[headNode][otherHeadNode] = abs(lws1[ int(lid)]-lws1[ int(otherLid)])
    
      
  for id, item in odr.laneConnections.items():
    for lid, item_ in item.items():
      if int(lid) < 0: #右侧车道
        node = f"road_{id}_lane_{lid}_1"
        for target in item_[1]:
          targetNode = f"road_{target[0]}_lane_{target[1]}_{target[2]}"
          graph[node][targetNode] = 0
      else:
        node = f"road_{id}_lane_{lid}_0"
        for target in item_[0]:
          targetNode = f"road_{target[0]}_lane_{target[1]}_{target[2]}"
          graph[node][targetNode] = 0
  
  return graph

def rectifyGraph(graph):
  for i in range(len(egoTs)):
    egoT, egoD = egoTs[i], egoDs[i]
    if egoT == None or egoD == None:
      continue

    road0 = odr.roads[egoT[0]]
    length0 = getData(road0, 'length')
    if int(egoT[1]) < 0: # 道路右侧
      graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_1"] = length0-egoT[2]
      graph[f"road_{egoT[0]}_lane_{egoT[1]}_0"][f"start_{i}"] = egoT[2]
    else:
      graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_0"] = egoT[2]
      graph[f"road_{egoT[0]}_lane_{egoT[1]}_1"][f"start_{i}"] = length0-egoT[2]

    road1 = odr.roads[egoD[0]]
    length1 = getData(road1, 'length')
    if int(egoD[1]) < 0: # 道路右侧
      graph[f"end_{i}"][f"road_{egoD[0]}_lane_{egoD[1]}_1"] = length1-egoD[2]
      graph[f"road_{egoD[0]}_lane_{egoD[1]}_0"][f"end_{i}"] = egoD[2]
    else:
      graph[f"end_{i}"][f"road_{egoD[0]}_lane_{egoD[1]}_0"] = egoD[2]
      graph[f"road_{egoD[0]}_lane_{egoD[1]}_1"][f"end_{i}"] = length1-egoD[2]
    
    if egoT[0] == egoD[0] and egoT[1] == egoD[1]:
      if (int(egoT[1]) > 0) ^ (egoT[2] < egoD[2]):
        graph[f"start_{i}"][f"end_{i}"] = abs(egoT[2]-egoD[2])
      else:
        graph[f"end_{i}"][f"start_{i}"] = abs(egoT[2]-egoD[2])

def dijkstra(graph, start, end, k=3):
  heap = []
  heapq.heappush(heap, (0, [start]))
  visited = defaultdict(int)
  paths = []
  
  while heap and len(paths) < k:
    cost, path = heapq.heappop(heap)
    current_node = path[-1]
    
    if current_node == end:
      paths.append((cost, path))
      continue
    
    if visited[current_node] > k*2:
      continue
    visited[current_node] += 1
    
    for neighbor, weight in graph[current_node].items():
      if neighbor not in path:
        new_path = list(path)
        new_path.append(neighbor)
        heapq.heappush(heap, (cost+weight, new_path))
  
  print(paths)
  if paths == []:
    return [(0, [start, end])]
  
  for i in range(len(paths)):
    if i >= k or paths[i][0] > paths[0][0]*k:
      return paths[:i]
  return paths

def projectPoint(road, tarX, tarY):
  gs = road.find('planView').findall('geometry')
  x0, y0 = getData(gs[0], 'x'), getData(gs[0], 'y')
  ans, ansL = float('inf'), 0
  if math.hypot(x0-tarX, y0-tarY) > getData(road, 'length')*2:
    return ans, ansL

  for g in gs:
    h    = getData(g, 'hdg')
    x, y = getData(g, 'x'), getData(g, 'y')
    l    = getData(g, 'length')
    dis, pos = 0, 0

    if g.find('line') != None:
      k, k_ = math.tan(h), -1/math.tan(h)
      b, b_ = y-k*x, tarY-k_*tarX
      dis = abs(k*tarX+b-tarY)/math.sqrt(k**2+1)
      x_cross = (b_-b)/(k-k_)
      pos = (x_cross-x)/math.cos(h)

      epsilon = 1e-2
      if  -epsilon < pos < 0:
        pos = 0
      if l < pos < l+epsilon:
        pos = l
      if pos < 0 or pos > l:
        continue
      if math.cos(h)*(tarY-y) > math.sin(h)*(tarX-x):
        dis *= -1
      
    else:
      poly = g.find('paramPoly3')
      bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
      bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
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
      
      epsilon, N = 1e-4, 100
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
      
      validRoots = [t for t in roots if -epsilon <= t <= 1+epsilon]
      validRoots = np.clip(validRoots, 0, 1)
      validRoots = np.unique(validRoots)
      for tRoot in validRoots:
        if t < 0: t = 0
        if t > 1: t = 1

      dis, T = float('inf'), 0
      for tRoot in validRoots:
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
      pos = odr.getLength([bU, cU, dU, bV, cV, dV], T)

    if abs(ans) > abs(dis):
      ans = dis
      ansL = pos+getData(g, "s")
  return ans, ansL

def getLanesWidth(road, pos):
  l = getData(road, "length")
  if pos < 0: pos = 0
  if pos > l: pos = l
  
  lanes = road.find('lanes').findall('.//lane')
  lws, rws = [], []

  for lane in lanes:
    id = getData(lane, 'id')
    if id == 0:
      continue

    widths = lane.findall('width')
    for i in range(1, len(widths)):
      sOffset = getData(widths[i], 'sOffset')
      if sOffset >= pos:
        w = widths[i-1]
        pos -= getData(w, 'sOffset')
        a, b = getData(w, 'a'), getData(w, 'b')
        c, d = getData(w, 'c'), getData(w, 'd')
        num = a+b*pos+c*pos**2+d*pos**3
        # TODO: 此处默认车道序号降序排列
        if id < 0:
          rws.append(num)
        else:
          lws.insert(0, -num)
        break
  for i in range(1, len(lws)):
    lws[i] += lws[i-1]
  for i in range(1, len(rws)):
    rws[i] += rws[i-1]
  return lws, rws