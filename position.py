import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *

def editRoadPosition(id, move, u, v):
  for road in vars.root.iter('road'):
    if road.get('id') != id:
      continue      
    planView = road.find('planView')
    gs = planView.findall('geometry')
    x, y = 0, 0
    if move == cons.TAIL:
      x, y = get(gs[0] , 'x'), get(gs[0] , 'y')
      # TODO：用三次曲线拟合一段新的道路
    else:
      x, y = get(gs[-1], 'x'), get(gs[-1], 'y')
      h = get(gs[-1], 'hdg')%(2*math.pi)
      line = gs[-1].find('line')
      if line != None:
        x += get(gs[-1], 'length')*math.cos(h)
        y += get(gs[-1], 'length')*math.sin(h)
      poly = gs[-1].find('paramPoly3')
      if poly != None:
        bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
        bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
        x_, y_ = bU+cU+dU, bV+cV+dV
        h = (h+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*math.pi)
        x += x_*math.cos(h)-y_*math.sin(h)
        y += x_*math.sin(h)+y_*math.cos(h)

    return