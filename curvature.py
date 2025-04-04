import xml.etree.ElementTree as ET
import math
import numpy
from scipy.integrate import quad
from scipy.optimize import least_squares
import variables as vars
from constants import *
 
def fit_constrained_curve(x_data, y_data, h_data, params):
  x1, y1, dx0, dy0, dx1, dy1, euc_dis = params
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
  ans = []
  size = int(len(result.fun)/2)
  index, max = -1, MAX_DEVIATION
  for i in range(1, size-1):
    delta = math.sqrt(result.fun[i]**2+result.fun[i+size]**2)/euc_dis
    if max < delta:
      max = delta
      index = i
  if index < 0:
    print("good")
    k1_opt, k2_opt = result.x[0], result.x[1]
    bX =    k1_opt*dx0
    bY =    k1_opt*dy0
    cX = -2*k1_opt*dx0 + 3*x1 - k2_opt*dx1
    dX =    k1_opt*dx0 - 2*x1 + k2_opt*dx1
    cY = -2*k1_opt*dy0 + 3*y1 - k2_opt*dy1
    dY =    k1_opt*dy0 - 2*y1 + k2_opt*dy1
    l0 = math.sqrt((bX/3          )**2+(bY/3)          **2)
    l1 = math.sqrt((bX/3+cX/3*2+dX)**2+(bY/3+cY/3*2+dY)**2)
    ans.append([x1, y1, math.atan2(dy0, dx0), math.atan2(dy1, dx1), l0, l1])
  else:
    print("bad", index, max)
    x_data0, x_data1 = x_data[:index], x_data[index+1:]-x_data[index]
    y_data0, y_data1 = y_data[:index], y_data[index+1:]-y_data[index]
    h_data0, h_data1 = h_data[:index], h_data[index+1:]
    x10, x11 = x_data[index], x1-x_data[index]
    y10, y11 = y_data[index], y1-y_data[index]
    dx2, dy2 = hdgToDxDy(h_data[index])
    params0 = [x10, y10, dx0, dy0, dx2, dy2, euc_dis]
    params1 = [x11, y11, dx2, dy2, dx1, dy1, euc_dis]
    print("params0", params0)
    print("params1", params1)
    ans.extend(fit_constrained_curve(x_data0, y_data0, h_data0, params0))
    ans.extend(fit_constrained_curve(x_data1, y_data1, h_data1, params1))
  
  return ans

def solveInitialCurve(gs):
  g0, g1 = gs[0], gs[-1]
  h0, h1 = getHdg(g0, 0)  ,  getHdg(g1, 1)
  x0, y0 = get(g0, 'x')   ,  get(g0, 'y')
  x1, y1 = get(g1, 'x')-x0,  get(g1, 'y')-y0

  line = g1.find('line')
  if line != None:
    x1 += get(g1, 'length')*math.cos(h1)
    y1 += get(g1, 'length')*math.sin(h1)
  poly = g1.find('paramPoly3')
  if poly != None:
    bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
    bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
    x_, y_ = bU+cU+dU, bV+cV+dV
    x1 += x_*math.cos(h1)-y_*math.sin(h1)
    y1 += x_*math.sin(h1)+y_*math.cos(h1)

  dx0, dy0 = hdgToDxDy(h0)
  dx1, dy1 = hdgToDxDy(h1)
  x_data, y_data, hdg_data = getMidData(gs, poly, x0, y0, x1, y1)
  params = [x1, y1, dx0, dy0, dx1, dy1, math.sqrt(x1**2+y1**2)]
  ans = fit_constrained_curve(x_data, y_data, hdg_data, params)

  return ans, math.sqrt(x1**2+y1**2)

def getHdg(g, num):
  h = get(g, 'hdg')%(2*numpy.pi)
  poly = g.find('paramPoly3')
  if poly != None:
    bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
    bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
    if num == 0:
      h = (h+math.atan(bV/bU))%(2*numpy.pi)
    else:
      h = (h+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)
  return h

def hdgToDxDy(h):
  dx, dy = 0, 0
  match h:
    case h if h == 0:        dx, dy =  1, 0
    case h if h == numpy.pi: dx, dy = -1, 0
    case h if h >  numpy.pi: dx, dy = -1/math.tan(h), -1
    case h if h <  numpy.pi: dx, dy =  1/math.tan(h), 1
  return dx, dy

def getMidData(gs, poly, x0, y0, x1, y1):
  xs, ys, hdgs = [], [], []
  for g in gs:
    if get(g, 's') == 0:
      continue
    xs.append(get(g, 'x')-x0)
    ys.append(get(g, 'y')-y0)
    hdgs.append(getHdg(g, 0))
  if xs == [] or ys == []:
    if poly != None:
      bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
      bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
      x_1, y_1 = bU/3*2+cU/9*4+dU/27*8, bV/3*2+cV/9*4+dV/27*8
      x_2, y_2 = bU/3+cU/9+dU/27      , bV/3+cV/9+dV/27
      xs.extend([x_1, x_2])
      ys.extend([y_1, y_2])
      hdgs.extend([]) # THIS WON'T BE USED
    else:
      xs.append(x1/2)
      ys.append(y1/2)
  return numpy.array(xs), numpy.array(ys), numpy.array(hdgs)

def solvePoly3(param):
  x3, y3, h0, h1, l0, l1 = param
  x1, y1 =    l0*math.cos(h0),    l0*math.sin(h0)
  x2, y2 = x3-l1*math.cos(h1), y3-l1*math.sin(h1)
  bU, cU, dU = 3*x1, -6*x1+3*x2, 3*x1-3*x2+x3
  bV, cV, dV = 3*y1, -6*y1+3*y2, 3*y1-3*y2+y3
  return bU, cU, dU, bV, cV, dV

def getLength(param):
  bX, cX, dX, bY, cY, dY = param
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
      params, euc_dis = solveInitialCurve(gs)
      params[ 0][2] = (params[ 0][2]+h0)%(2*numpy.pi)
      params[-1][3] = (params[-1][3]+h1)%(2*numpy.pi)
      params[ 0][4] += euc_dis*v0
      params[-1][5] += euc_dis*v1

      ## 计算道路方程
      planView.clear()
      length_new = 0
      x, y = get(gs[0], 'x'), get(gs[0], 'y')
      for param in params:
        print(param)
        ans = solvePoly3(param)
        l = getLength(ans)
        g = ET.Element('geometry')
        set(g, 's', length_new)
        set(g, 'x', x)
        set(g, 'y', y)
        set(g, 'hdg', 0)
        set(g, 'length', l)
        poly = ET.Element('paramPoly3')
        set(poly, 'bU', ans[0])
        set(poly, 'cU', ans[1])
        set(poly, 'dU', ans[2])
        set(poly, 'bV', ans[3])
        set(poly, 'cV', ans[4])
        set(poly, 'dV', ans[5])
        length_new += l
        x += param[0]
        y += param[1]
        g.append(poly)
        planView.append(g)

      # 修正道路数据
      set(road, 'length', length_new)
      sections = road.find('lanes').findall('laneSection')
      elevas = road.find('elevationProfile').findall('elevation')
      widths = road.find('lanes').findall('.//width')
      k_l = length_new/length
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