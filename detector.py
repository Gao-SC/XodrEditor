from scipy.optimize import root_scalar
from collections import defaultdict
import numpy as np
import math
import json
import heapq
import random

import odrparser as odr
from constants import *

carInfos = defaultdict(dict)
egoT, egoD = None, None
data = None

def readJson(name):
  print("FINDING THE TARGET ROADS...")
  try:
    with open(PATH+'selected_map\\'+name+".json", 'r') as file:
      # 初始化
      global data
      data = json.load(file)
      carInfos.clear()
      for id, road in odr.roads.items():
        carInfos[id] = defaultdict(dict)
        lanes = road.find("lanes").findall(".//lane")
        for lane in lanes:
          carInfos[id][lane.get('id')] = []
          
      agents = data["agents"]
      tPos0 = agents[0]["transform"]["position"]
      tRot0 = agents[0]["transform"]["rotation"]
      dPos0 = agents[0]["destinationPoint"]["position"]
      dRot0 = agents[0]["destinationPoint"]["rotation"]

      global egoT
      global egoD
      egoT, egoD = findRoad(tPos0, tRot0), findRoad(dPos0, dRot0)
      carInfos[egoT[0]][egoT[1]].append({"carId": 0, "ordId": 0, "pos": egoT[2]})
      carInfos[egoD[0]][egoD[1]].append({"carId": 0, "ordId": 1, "pos": egoD[2]})
      
      npcCars = agents[1:]
      for i in range(len(npcCars)):
        tPos = npcCars[i]["transform"]["position"]
        tRot = npcCars[i]["transform"]["rotation"]
        tNpc = findRoad(tPos, tRot)
        carInfos[tNpc[0]][tNpc[1]].append({"carId": i, "ordId": 0, "pos": tNpc[2]})

        wayPoints = npcCars[i]["waypoints"]
        for j in range(len(wayPoints)):
          pos = wayPoints[j]["position"]
          rot = wayPoints[j]["angle"]
          npc = findRoad(pos, rot)
          print(npc)
          carInfos[npc[0]][npc[1]].append({"carId": i, "ordId": j+1, "pos": npc[2]})
      for i in carInfos.values():
        print(i)
  
  except FileNotFoundError:
    print("Error: File not found!")
  except json.JSONDecodeError:
    print("Error: Invalid JSON format!")
  print("Success!")

def testModify():
  graph = buildGRAPH()
  rectifyGraph(graph)

  # 运行Dijkstra
  paths = dijkstra(graph, 'start', 'end')
  candidateRoads = []
  candidateLanes = []
  egoT, egoD = carInfos[0][0], carInfos[0][1]
  for cost, path in paths:
    for node in path:
      id, lid = "", ""
      if node == "start":
        id, lid = egoT[0], egoT[1]
      elif node == "end":
        id, lid = egoD[0], egoD[1]
      else:
        data = node.split('_')
        id, lid = data[1], data[3]
      if id not in candidateRoads:
        candidateRoads.append(id)
      if [id, lid] not in candidateLanes:
        candidateLanes.append([id, lid])

  method = random.randint(0, 2)
  command = ""
  list1 = [-1, 1]
  match method:
    case 0: # width
      target = random.randint(0, len(candidateLanes)-1)
      id = candidateLanes[target][0]
      li = candidateLanes[target][1]
      v = (1+1*random.random())*random.choice(list1)    
      command = f"width id={id} li={li} v={v} s=1 sh=1 ms={1<<30}".split()
    case 1: # slope
      target = random.randint(0, len(candidateRoads)-1)
      id = candidateRoads[target]
      v = (1+1*random.random())*random.choice(list1)
      mv = random.randint(0, 2)
      command = f"slope id={id} v={v} mv={mv} sh=1 ms={1<<30}".split()
    case 2: # curve
      target = random.randint(0, len(candidateRoads)-1)
      id = candidateRoads[target]
      v0 = (0.2+0.2*random.random())*random.choice(list1)
      v1 = (0.2+0.2*random.random())*random.choice(list1)
      command = f"curve id={id} v0={v0} v1={v1}".split()
  
  print(command)
  return command


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
          candidateRoads.append([id, str(i+1),  ansL, abs(ans)])
          break
    else:
      for i in range(len(rws)):
        if ans < rws[i]:
          candidateRoads.append([id, str(-i-1), ansL, abs(ans)])
          break
  if candidateRoads:
    candidateRoads.sort(key=lambda x: x[3])
    return candidateRoads[0][:3]
  else:
    return None

## PRIVATE METHOD

def buildGRAPH():
  graph = defaultdict(dict)
  for id, road in odr.roads.items():
    length = getData(road, 'length')
    section = road.find('lanes').find('laneSection')
    for lane in section.findall('.//lane'):
      lid = lane.get('id')
      if lid == "0":
        continue
      tailNode = f"road_{id}_lane_{lid}_0"
      headNode = f"road_{id}_lane_{lid}_1"
      if int(lid) < 0: #右侧车道
        graph[tailNode][headNode] = length
      else:
        graph[headNode][tailNode] = length
      
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
  egoT, egoD = carInfos[0][0], carInfos[0][1]
  road0 = odr.roads[egoT[0]]
  length0 = getData(road0, 'length')
  if int(egoT[1]) < 0: # 道路右侧
    graph['start'][f"road_{egoT[0]}_lane_{egoT[1]}_1"] = length0-egoT[2]
    graph[f"road_{egoT[0]}_lane_{egoT[1]}_0"]['start'] = egoT[2]
  else:
    graph['start'][f"road_{egoT[0]}_lane_{egoT[1]}_0"] = egoT[2]
    graph[f"road_{egoT[0]}_lane_{egoT[1]}_1"]['start'] = length0-egoT[2]

  road1 = odr.roads[egoD[0]]
  length1 = getData(road1, 'length')
  if int(egoD[1]) < 0: # 道路右侧
    graph['end'][f"road_{egoD[0]}_lane_{egoD[1]}_1"] = length1-egoD[2]
    graph[f"road_{egoD[0]}_lane_{egoD[1]}_0"]['end'] = egoD[2]
  else:
    graph['end'][f"road_{egoD[0]}_lane_{egoD[1]}_0"] = egoD[2]
    graph[f"road_{egoD[0]}_lane_{egoD[1]}_1"]['end'] = length1-egoD[2]
  
  if egoT[0] == egoD[0] and egoT[1] == egoD[1]:
    if (int(egoT[1]) > 0) ^ (egoT[2] < egoD[2]):
      graph['start']['end'] = abs(egoT[2]-egoD[2])
    else:
      graph['end']['start'] = abs(egoT[2]-egoD[2])

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
    
    for i in range(len(paths)):
      if i >= k or paths[i][0] > paths[0][0]*k:
        return paths[:i]

def projectPoint(road, tarX, tarY):
  gs = road.find('planView').findall('geometry')
  x0, y0 = getData(gs[0], 'x'), getData(gs[0], 'y')
  ans, ansL = float('inf'), 0
  if math.hypot(x0-tarX, y0-tarY) > getData(road, 'length')*2:
    return ans, ansL
  length = 0

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
        u = x + bU*t + cU*t**2 + dU*t**3
        v = y + bV*t + cV*t**2 + dV*t**3
        du_dt = bU + 2*cU*t + 3*dU*t**2
        dv_dt = bV + 2*cV*t + 3*dV*t**2
        return u, v, du_dt, dv_dt
      def F(t):
        u, v, du_dt, dv_dt = compute_uv(t)
        x_t = u*cosH - v*sinH
        y_t = u*sinH + v*cosH
        dx_dt = du_dt*cosH - dv_dt*sinH
        dy_dt = du_dt*sinH + dv_dt*cosH
        return (x_t-tarX)*dx_dt + (y_t-tarY)*dy_dt
      
      epsilon, N = 1e-6, 10000
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
      valid_roots = [t for t in roots if 0 <= t <= 1]
      valid_roots = np.clip(valid_roots, 0, 1)
      valid_roots = np.unique(valid_roots)
            
      dis, T = float('inf'), 0
      for t_root in valid_roots:
        u, v, du_dt, dv_dt = compute_uv(t_root)
        x = u*cosH - v*sinH
        y = u*sinH + v*cosH
        dx_dt = du_dt*cosH - dv_dt*sinH
        dy_dt = du_dt*sinH + dv_dt*cosH
        if abs(dis) > math.hypot(x-tarX, y-tarY):
          T = t_root
          dis = math.hypot(x-tarX, y-tarY)
          if dx_dt*(tarY-y) > dy_dt*(tarX-x):
            dis *= -1
      pos = odr.getLength([bU, cU, dU, bV, cV, dV], T)

    if abs(ans) > abs(dis):
      ans = dis
      ansL = pos+length
    length += l

  return ans, ansL

def getLanesWidth(road, pos):
  lanes = road.find('lanes').findall('.//lane')
  lws, rws = [], []

  for lane in lanes:
    id = getData(lane, 'id')
    if id == 0:
      continue

    widths = lane.findall('width')
    for i in range(1, len(widths)):
      sOffset = getData(widths[i], 'sOffset')
      if sOffset > pos:
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