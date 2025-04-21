import xml.etree.ElementTree as ET
import math
import odrparser as odr
from constants import *

def editRoadPosition(id, move, u, v):
  road = odr.roads[id]
  planView = road.find('planView')
  gs = planView.findall('geometry')
  x, y = 0, 0
  if move == cons.TAIL:
    x, y = getData(gs[0] , 'x'), getData(gs[0] , 'y')
    # TODO：用三次曲线拟合一段新的道路
  else:
    x, y = getData(gs[-1], 'x'), getData(gs[-1], 'y')
    h = getData(gs[-1], 'hdg')%(2*math.pi)
    line = gs[-1].find('line')
    if line != None:
      x += getData(gs[-1], 'length')*math.cos(h)
      y += getData(gs[-1], 'length')*math.sin(h)
    poly = gs[-1].find('paramPoly3')
    if poly != None:
      bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
      bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
      x_, y_ = bU+cU+dU, bV+cV+dV
      h = (h+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*math.pi)
      x += x_*math.cos(h)-y_*math.sin(h)
      y += x_*math.sin(h)+y_*math.cos(h)