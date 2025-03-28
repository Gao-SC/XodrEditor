import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *
import numpy
from scipy.integrate import quad
 
def getParams(gs):
  g0,   g1   = gs[0], gs[-1]
  hdg0, hdg1 = get(g0 , 'hdg'), get(g1, 'hdg')
  x1,   y1   = get(g1, 'x')-get(g0, 'x'), get(g1, 'y')-get(g0, 'y')
  h0,   h1   = hdg0%(2*numpy.pi), hdg1%(2*numpy.pi)

  poly0 = g0.find('paramPoly3')
  if poly0 != None:
    bU, cU, dU = get(poly0, 'bU'), get(poly0, 'cU'), get(poly0, 'dU')
    bV, cV, dV = get(poly0, 'bV'), get(poly0, 'cV'), get(poly0, 'dV')
    h0 = (hdg0+math.atan(bV/bU))%(2*numpy.pi)

  line1 = g1.find('line')
  if line1 != None:
    x1 += get(g1, 'length')*math.cos(hdg1)
    y1 += get(g1, 'length')*math.sin(hdg1)
  poly1 = g1.find('paramPoly3')
  if poly1 != None:
    bU, cU, dU = get(poly1, 'bU'), get(poly1, 'cU'), get(poly1, 'dU')
    bV, cV, dV = get(poly1, 'bV'), get(poly1, 'cV'), get(poly1, 'dV')
    x_, y_ = bU+cU+dU, bV*cV+dV
    x1 += x_*math.cos(hdg1)-y_*math.sin(hdg1)
    y1 += y_*math.sin(hdg1)+y_*math.cos(hdg1)
    h1 = (hdg1+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)
    print(h1)

  return [x1, y1, h0, h1]

def solvePoly3(params):
  x3, y3 = params[0], params[1]
  h0, h1 = params[2], params[3]
  v0, v1 = params[4], params[5]
  s = math.sqrt(x3**2+y3**2)
  x1, y1 =    s*v0*math.cos(h0),    s*v0*math.sin(h0)
  x2, y2 = x3-s*v1*math.cos(h1), y3-s*v1*math.sin(h1)
  bU, cU, dU = 3*x1, -6*x1+3*x2, 3*x1-3*x2+x3
  bV, cV, dV = 3*y1, -6*y1+3*y2, 3*y1-3*y2+y3
  return bU, cU, dU, bV, cV, dV

def getLength(params):
  bX, cX, dX = params[0], params[1], params[2]
  bY, cY, dY = params[3], params[4], params[5]
  def integrand(p, bX, cX, dX, bY, cY, dY):
    dx_dp = bX+2*cX*p+3*dX*p**2
    dy_dp = bY+2*cY*p+3*dY*p**2
    return numpy.sqrt(dx_dp**2+dy_dp**2)
  length, _ = quad(integrand, 0, 1, args=(bX, cX, dX, bY, cY, dY))
  return length

## 拟合圆弧时，v0=v1=cos(theta/2)/(3*cos^2(theta/4))
def changeRoadArc(id, v0, v1, h0, h1):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      planView = road.find('planView')
      gs = planView.findall('geometry')
      length = get(road, 'length')

      ## 获取道路参数
      params = getParams(gs)
      params[2] = (params[2]+h0)%(2*numpy.pi)
      params[3] = (params[3]+h1)%(2*numpy.pi)
      params.append(v0)
      params.append(v1)

      ## 计算道路方程
      ans = solvePoly3(params)
      newL = getLength(ans)
      set(road, 'length', newL)
      s, x, y = get(gs[0], 's'), get(gs[0], 'x'), get(gs[0], 'y')
      planView.clear()
      g = ET.Element('geometry')
      set(g, 's', s)
      set(g, 'x', x)
      set(g, 'y', y)
      set(g, 'hdg', 0)
      set(g, 'length', newL)
      poly = ET.Element('paramPoly3')
      set(poly, 'bU', ans[0])
      set(poly, 'cU', ans[1])
      set(poly, 'dU', ans[2])
      set(poly, 'bV', ans[3])
      set(poly, 'cV', ans[4])
      set(poly, 'dV', ans[5])
      g.append(poly)
      planView.append(g)

      # 修正道路宽度
      sections = road.find('lanes').findall('laneSection')
      elevas = road.find('elevationProfile').findall('elevation')
      widths = road.find('lanes').findall('.//width')
      k_l = newL/length

      for section in sections:
        set(section, 's', get(section, 's')*k_l)
      for eleva in elevas:
        set(eleva, 's', get(eleva, 's')*k_l)
        set(eleva, 'b', get(eleva, 'b')/k_l)
        set(eleva, 'c', get(eleva, 'c')/(k_l**2))
        set(eleva, 'd', get(eleva, 'd')/(k_l**3))
      for width in widths:
        set(width, 'sOffset', get(width, 'sOffset')*k_l)
        set(width, 'b', get(width, 'b')/k_l)
        set(width, 'c', get(width, 'c')/(k_l**2))
        set(width, 'd', get(width, 'd')/(k_l**3))
      break