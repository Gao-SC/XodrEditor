import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *
import numpy
from scipy.integrate import quad
from scipy.optimize import least_squares
 
def fit_constrained_curve(x_data, y_data, x1, y1, dx0, dy0, dx1, dy1):
  def compute_initial_t(x, y):
    dx = numpy.diff(x)
    dy = numpy.diff(y)
    dist = numpy.sqrt(dx**2 + dy**2)
    cum_dist = numpy.insert(numpy.cumsum(dist), 0, 0)
    return cum_dist/cum_dist[-1] if cum_dist[-1] != 0 else numpy.linspace(0, 1, len(x))
  
  t_initial = compute_initial_t(x_data, y_data)
  k1_initial, k2_initial  = 1.0, 1.0
  initial_guess = numpy.concatenate([[k1_initial, k2_initial], t_initial])
  
  def residuals(params):
    k1, k2, t_vals = params[0], params[1], params[2:]
    bX =    k1*dx0
    bY =    k1*dy0
    cX = -2*k1*dx0 + 3*x1 - k2*dx1
    cY = -2*k1*dy0 + 3*y1 - k2*dy1
    dX =    k1*dx0 - 2*x1 + k2*dx1
    dY =    k1*dy0 - 2*y1 + k2*dy1
    x_pred = bX*t_vals + cX*t_vals**2 + dX*t_vals**3
    y_pred = bY*t_vals + cY*t_vals**2 + dY*t_vals**3
    return numpy.concatenate([x_data-x_pred, y_data-y_pred])
  
  n_points = len(x_data)
  lower = [-numpy.inf, -numpy.inf]+[0]*n_points
  upper = [ numpy.inf,  numpy.inf]+[1]*n_points
  
  result = least_squares(residuals, initial_guess, bounds=(lower, upper))
  k1_opt, k2_opt = result.x[0], result.x[1]
  bX =    k1_opt*dx0
  bY =    k1_opt*dy0
  cX = -2*k1_opt*dx0 + 3*x1 - k2_opt*dx1
  dX =    k1_opt*dx0 - 2*x1 + k2_opt*dx1
  cY = -2*k1_opt*dy0 + 3*y1 - k2_opt*dy1
  dY =    k1_opt*dy0 - 2*y1 + k2_opt*dy1
  return bX, cX, dX, bY, cY, dY

def solveInitialCurve(gs):
  g0, g1 = gs[0], gs[-1]
  h0, h1 = get(g0 , 'hdg'),  get(g1, 'hdg')
  x0, y0 = get(g0, 'x')   ,  get(g0, 'y')
  x1, y1 = get(g1, 'x')-x0,  get(g1, 'y')-y0
  h0, h1 = h0%(2*numpy.pi),  h1%(2*numpy.pi)

  poly0 = g0.find('paramPoly3')
  if poly0 != None:
    bU, cU, dU = get(poly0, 'bU'), get(poly0, 'cU'), get(poly0, 'dU')
    bV, cV, dV = get(poly0, 'bV'), get(poly0, 'cV'), get(poly0, 'dV')
    h0 = (h0+math.atan(bV/bU))%(2*numpy.pi)

  line1 = g1.find('line')
  if line1 != None:
    x1 += get(g1, 'length')*math.cos(h1)
    y1 += get(g1, 'length')*math.sin(h1)
  poly1 = g1.find('paramPoly3')
  if poly1 != None:
    bU, cU, dU = get(poly1, 'bU'), get(poly1, 'cU'), get(poly1, 'dU')
    bV, cV, dV = get(poly1, 'bV'), get(poly1, 'cV'), get(poly1, 'dV')
    x_, y_ = bU+cU+dU, bV+cV+dV
    x1 += x_*math.cos(h1)-y_*math.sin(h1)
    y1 += x_*math.sin(h1)+y_*math.cos(h1)
    h1 = (h1+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)

  dx0, dy0, dx1, dy1 = 0, 0, 0, 0
  if h0 == 0:
    dx0, dy0 =  1, 0
  elif h0 == numpy.pi:
    dx0, dy0 = -1, 0
  elif h0 >  numpy.pi:
    dx0, dy0 = -1/math.tan(h0), -1
  else:
    dx0, dy0 =  1/math.tan(h0), 1
  if h1 == 0:
    dx1, dy1 =  1, 0
  elif h1 == numpy.pi:
    dx1, dy1 = -1, 0
  elif h1 >  numpy.pi:
    dx1, dy1 = -1/math.tan(h1), -1
  else:
    dx1, dy1 =  1/math.tan(h1), 1

  xs, ys = [], []
  for g in gs:
    if get(g, 's') == 0:
      continue
    xs.append(get(g, 'x')-x0)
    ys.append(get(g, 'y')-y0)
  if xs == [] or ys == []:
    if poly0 != None:
      bU, cU, dU = get(poly0, 'bU'), get(poly0, 'cU'), get(poly0, 'dU')
      bV, cV, dV = get(poly0, 'bV'), get(poly0, 'cV'), get(poly0, 'dV')
      x_1, y_1 = bU/3*2+cU/9*4+dU/27*8, bV/3*2+cV/9*4+dV/27*8
      x_2, y_2 = bU/3+cU/9+dU/27      , bV/3+cV/9+dV/27
      xs.append(x_1)
      xs.append(x_2)
      ys.append(y_1)
      ys.append(y_2)
    else:
      xs.append(x1/2)
      ys.append(y1/2)
  x_data = numpy.array(xs)
  y_data = numpy.array(ys)
  bX, cX, dX, bY, cY, dY = fit_constrained_curve(x_data, y_data, x1, y1, dx0, dy0, dx1, dy1)
  l0 = math.sqrt((bX/3          )**2+(bY/3)          **2)
  l1 = math.sqrt((bX/3+cX/3*2+dX)**2+(bY/3+cY/3*2+dY)**2)
  s = math.sqrt(x1**2+y1**2)
  print(x1, y1, h0, h1, l0, l1)
  return [x1, y1, h0, h1, l0, l1], s

def solvePoly3(params):
  x3, y3 = params[0], params[1]
  h0, h1 = params[2], params[3]
  l0, l1 = params[4], params[5]
  x1, y1 =    l0*math.cos(h0),    l0*math.sin(h0)
  x2, y2 = x3-l1*math.cos(h1), y3-l1*math.sin(h1)
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
      params, s = solveInitialCurve(gs)
      params[2] = (params[2]+h0)%(2*numpy.pi)
      params[3] = (params[3]+h1)%(2*numpy.pi)
      params[4] += s*v0
      params[5] += s*v1

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