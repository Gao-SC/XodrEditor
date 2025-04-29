import heapq
from collections import defaultdict

import Xodr.xodrParser as Xparser
import Json.jsonParser as JParser
from utils.constants import *

candidateRoads = []
candidateLanes = []

def setCandidates():
  graph = buildGRAPH()
  rectifyGraph(graph)

  # 运行Dijkstra
  paths = []
  for i in range(len(JParser.egoTs)):
    x = dijkstra(graph, f"start_{i}", f"end_{i}")
    paths.extend(x)

  candidateRoads.clear()
  candidateLanes.clear()
  
  for cost, path in paths:
    for node in path:
      id, lid = "", ""
      data = node.split('_')
      if data[0] == "start":
        egoT = JParser.egoTs[int(data[1])]
        id, lid = egoT[0], egoT[1]
      elif data[0] == "end":
        egoD = JParser.egoDs[int(data[1])]
        id, lid = egoD[0], egoD[1]
      else:
        id, lid = data[1], data[3]
      if id not in candidateRoads:
        candidateRoads.append(id)
      if [id, lid] not in candidateLanes:
        candidateLanes.append([id, lid])

  """method = random.randint(0, 2)
  command = ""
  match method:
    case 0: # width
      target = random.randint(0, len(candidateLanes)-1)
      id = candidateLanes[target][0]
      li = candidateLanes[target][1]
      v = (1+1*random.random())*random.choice([-1, 1])    
      command = f"width id={id} li={li} v={v} s=1 sh=1 ms={1<<30}".split()
    case 1: # slope
      target = random.randint(0, len(candidateRoads)-1)
      id = candidateRoads[target]
      v = (1+1*random.random())*random.choice([-1, 1])
      mv = random.randint(0, 2)
      command = f"slope id={id} v={v} mv={mv} sh=1 ms={1<<30}".split()
    case 2: # curve
      target = random.randint(0, len(candidateRoads)-1)
      id = candidateRoads[target]
      v0 = (0.2+0.2*random.random())*random.choice([-1, 1])
      v1 = (0.2+0.2*random.random())*random.choice([-1, 1])
      command = f"curve id={id} v0={v0} v1={v1}".split()
  
  print(command)
  return command"""

def buildGRAPH():
  graph = defaultdict(dict)
  for id, road in Xparser.roads.items():
    length = getData(road, 'length')
    section = road.find('lanes').find('laneSection')
    
    lws0, rws0 = JParser.getLanesWidth(road, 0)
    lws1, rws1 = JParser.getLanesWidth(road, length)

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
    
      
  for id, item in Xparser.laneConnections.items():
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
  for i in range(len(JParser.egoTs)):
    egoT, egoD = JParser.egoTs[i], JParser.egoDs[i]
    if egoT == None or egoD == None:
      continue

    road0 = Xparser.roads[egoT[0]]
    length0 = getData(road0, 'length')
    if int(egoT[1]) < 0: # 道路右侧
      graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_1"] = length0-egoT[2]
      graph[f"road_{egoT[0]}_lane_{egoT[1]}_0"][f"start_{i}"] = egoT[2]
    else:
      graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_0"] = egoT[2]
      graph[f"road_{egoT[0]}_lane_{egoT[1]}_1"][f"start_{i}"] = length0-egoT[2]

    road1 = Xparser.roads[egoD[0]]
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
  
  # print(paths)
  if paths == []:
    return [(0, [start, end])]
  
  for i in range(len(paths)):
    if i >= k or paths[i][0] > paths[0][0]*k:
      return paths[:i]
  return paths
