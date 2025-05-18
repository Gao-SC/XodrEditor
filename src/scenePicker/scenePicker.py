import heapq
from collections import defaultdict

from xodrs.xodrParser import XParser
from xodrs.xodrDataGetter import xDataGetter
from jsons.jsonParser import JParser

from utils.lambdas import *

import random
class scenePicker:
  def __init__(self):
    self.candidateRoads = []
    self.candidateLanes = []

  def setCandidates(self, ego, npc):
    self.candidateRoads.clear()
    self.candidateLanes.clear()

    if ego > 0: # 考虑ego车的途径点
      graph = self.buildGRAPH()
      self.rectifyGraph(graph)

      # 寻找潜在的ego路径
      paths = []
      for i in range(len(JParser.egoTs)):
        x = self.dijkstra(graph, f"start_{i}", f"end_{i}", k=ego)
        paths.extend(x)

      for cost, path in paths:
        for node in path:
          data = node.split('_')
          if data[0] == "start":
            egoT = JParser.egoTs[int(data[1])]
            id, lid = egoT[0], egoT[1]
          elif data[0] == "end":
            egoD = JParser.egoDs[int(data[1])]
            id, lid = egoD[0], egoD[1]
          else:
            id, lid = data[1], data[3]
          if id not in self.candidateRoads:
            self.candidateRoads.append(id)
          if [id, lid] not in self.candidateLanes:
            self.candidateLanes.append([id, lid])

    if npc > 0: # 考虑npc车的途径点
      for id, roadInfo in JParser.carPosition[-1].items():
        if roadInfo and id not in self.candidateRoads:
          self.candidateRoads.append(id)
        for lid, laneInfo in roadInfo.items():
          if laneInfo and [id, lid] not in self.candidateLanes:
            self.candidateLanes.append([id, lid])

  def buildGRAPH(self):
    graph = defaultdict(dict)
    for id, road in XParser.roads.items():
      length = getData(road, 'length')
      section = road.find('lanes').find('laneSection')
      LHT = road.find('rule') == "LHT"
      
      lws0, rws0 = xDataGetter.getPosWidths(road, 0)
      lws1, rws1 = xDataGetter.getPosWidths(road, length)

      for lane in section.findall('.//lane'):
        lid = lane.get('id')
        if lid == "0":
          continue
        tailNode = f"road_{id}_lane_{lid}_0"
        headNode = f"road_{id}_lane_{lid}_1"
        ## 道路上行驶
        if int(lid) < 0 ^ LHT: # 右侧车道向前行驶
          graph[tailNode][headNode] = length
        else:
          graph[headNode][tailNode] = length
        ## 变道
        for otherLane in section.findall('.//lane'):
          otherLid = otherLane.get('id')
          if otherLid == "0" or otherLid == lid or int(otherLid)*int(lid) < 0:
            continue
          otherTailNode = f"road_{id}_lane_{otherLid}_0"
          otherHeadNode = f"road_{id}_lane_{otherLid}_1"
          if int(lid) < 0: # 右侧车道
            graph[tailNode][otherTailNode] = abs(rws0[-int(lid)-1]-rws0[-int(otherLid)-1])
            graph[headNode][otherHeadNode] = abs(rws1[-int(lid)-1]-rws1[-int(otherLid)-1])
          else:
            graph[tailNode][otherTailNode] = abs(lws0[ int(lid)-1]-lws0[ int(otherLid)-1])
            graph[headNode][otherHeadNode] = abs(lws1[ int(lid)-1]-lws1[ int(otherLid)-1])
      
    ## 道路连接
    for id, item in XParser.laneConnections.items():
      for lid, item_ in item.items():
        if int(lid) < 0 ^ LHT: # 右侧车道向前行驶
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

  def rectifyGraph(self, graph):
    for i in range(len(JParser.egoTs)):
      egoT, egoD = JParser.egoTs[i], JParser.egoDs[i]
      if egoT == None or egoD == None:
        continue

      road0 = XParser.roads[egoT[0]]
      length0 = getData(road0, 'length')
      if int(egoT[1]) < 0: # 道路右侧
        graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_1"] = length0-egoT[2]
        graph[f"road_{egoT[0]}_lane_{egoT[1]}_0"][f"start_{i}"] = egoT[2]
      else:
        graph[f"start_{i}"][f"road_{egoT[0]}_lane_{egoT[1]}_0"] = egoT[2]
        graph[f"road_{egoT[0]}_lane_{egoT[1]}_1"][f"start_{i}"] = length0-egoT[2]

      road1 = XParser.roads[egoD[0]]
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

  def dijkstra(self, graph, start, end, k):
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
      
      if visited[current_node] > k:
        continue
      visited[current_node] += 1
      
      for neighbor, weight in graph[current_node].items():
        if neighbor not in path:
          new_path = list(path)
          new_path.append(neighbor)
          heapq.heappush(heap, (cost+weight, new_path))
    
    if paths == []:
      return [(0, [start, end])]
    return paths[:k]

  def getRandomId1(self):
    id = random.choice(self.candidateRoads)
    print("Randomly select: ", id)
    return id

  def getRandomId2(self):
    id, laneId = random.choice(self.candidateLanes)
    print("Randomly select: ", id, laneId)
    return id, laneId

sPicker = scenePicker()