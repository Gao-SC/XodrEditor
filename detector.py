import odrparser as odr

def findRoad(x, y):
  candidate_roads = []
  for road in odr.roads:
    # 将点投影到道路参考线，获取s和t
    s, t = project_point(road, x, y)
    if s is None:
        continue  # 投影失败或不在范围内
    
    lftW, rgtW = getWidth(road, s)
    if -lftW <= t <= rgtW:
      candidate_roads.append((road, abs(t)))

  # 选择t最小的道路
  if candidate_roads:
    candidate_roads.sort(key=lambda x: x[1])
    selected_road = candidate_roads[0][0]
    return selected_road
  else:
    return None