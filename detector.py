from scipy.optimize import root_scalar
import numpy as np
import math

import odrparser as odr
from constants import *

def findRoad(x, y):
  candidateRoads = []
  for road in odr.root.findall('road'):
    id = road.get('id')

    ans, ansL = projectPoint(road, x, y)
    lftW, rgtW = getWidth(road, ansL)
    if -lftW <= ans <= rgtW:
      candidateRoads.append(id)

  print(candidateRoads)
  return candidateRoads

"""  if candidateRoads:
    candidateRoads.sort(key=lambda x: x[1])
    selected_road = candidateRoads[0][0]
    return selected_road
  else:
    return None"""

## PRIVATE METHOD

def projectPoint(road, tarX, tarY):
  gs = road.find('planView').findall('geometry')
  ans, ansL = float('inf'), 0
  length = 0

  for g in gs:
    h    = get(g, 'hdg')
    x, y = get(g, 'x'), get(g, 'y')
    l    = get(g, 'length')
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
      bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
      bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
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
      pos = getLength([bU, cU, dU, bV, cV, dV], T)

    if abs(ans) > abs(dis):
      ans = dis
      ansL = pos+length
    length += l

  return ans, ansL

def getWidth(road, pos):
  lftW, rgtW = 0, 0
  lanes = road.find('lanes').findall('.//lane')
  for lane in lanes:
    id = get(lane, 'id')
    if id == 0:
      continue
    
    widths = lane.findall('width')
    for i in range(1, len(widths)):
      sOffset = get(widths[i], 'sOffset')
      if sOffset > pos:
        w = widths[i-1]
        pos -= get(w, 'sOffset')
        a, b = get(w, 'a'), get(w, 'b')
        c, d = get(w, 'c'), get(w, 'd')
        num = a+b*pos+c*pos**2+d*pos**3
        if id < 0:
          rgtW += num
        else:
          lftW += num
        break
  return lftW, rgtW

