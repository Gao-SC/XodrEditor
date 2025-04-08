import xml.etree.ElementTree as ET
import math
import numpy
from scipy.integrate import quad
from scipy.optimize import least_squares
from scipy.optimize import root_scalar
import variables as vars
from constants import *

def fit_constrained_curve(gs, params, MAX_DEVIATION):
  x0, y0, x1, y1, dx0, dy0, dx1, dy1, euc_dis = params
  x_data, y_data, h_data = getMidData(gs, x0, y0, x1, y1)
  print(len(x_data), len(y_data), len(h_data), len(gs))

  ## 初始化
  def compute_initial_t(x, y):
    dx = numpy.diff(x)
    dy = numpy.diff(y)
    dist = numpy.sqrt(dx**2 + dy**2)
    cum_dist = numpy.insert(numpy.cumsum(dist), 0, 0)
    return cum_dist/cum_dist[-1] if cum_dist[-1] != 0 else numpy.linspace(0, 1, len(x))
  
  t_initial = compute_initial_t(x_data, y_data)
  k1_initial, k2_initial  = 1.0, 1.0
  initial_guess = numpy.concatenate([[k1_initial, k2_initial], t_initial])
  ## 拟合
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
  ## 计算结果
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
    ans.append([x1, y1, l0, l1, math.atan2(dy0, dx0), math.atan2(dy1, dx1)])
  else:
    print("bad", index, max, size, len(gs))
    gs0, gs1 = gs[:index+1], gs[index+1:]
    x00, x01 = x0,            x0+x_data[index]
    x10, x11 = x_data[index], x1-x_data[index]
    y00, y01 = y0,            y0+y_data[index]
    y10, y11 = y_data[index], y1-y_data[index]
    dx2, dy2 = hdgToDxDy(h_data[index])
    params0 = [x00, y00, x10, y10, dx0, dy0, dx2, dy2, euc_dis]
    params1 = [x01, y01, x11, y11, dx2, dy2, dx1, dy1, euc_dis]
    ans.extend(fit_constrained_curve(gs0, params0, MAX_DEVIATION))
    ans.extend(fit_constrained_curve(gs1, params1, MAX_DEVIATION))
  
  return ans

def solveInitialCurve(gs, MAX_DEVIATION):
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
  params = [x0, y0, x1, y1, dx0, dy0, dx1, dy1, math.sqrt(x1**2+y1**2)]
  ans = fit_constrained_curve(gs, params, MAX_DEVIATION)
  return ans

# TODO
def getMidData(gs, x0, y0, x1, y1):
  xs, ys, hdgs = [], [], []
  for i in range(len(gs)):
    if i == 0:
      continue
    xs.append(get(gs[i], 'x')-x0)
    ys.append(get(gs[i], 'y')-y0)
    hdgs.append(getHdg(gs[i], 0))
  if xs == []:
    poly = gs[0].find('paramPoly3')
    if poly != None:
      bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
      bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
      x_1, y_1 = bU/4+cU/16+dU/64,        bV/4+cV/16+dV/64
      x_2, y_2 = bU/2+cU/4+dU/8          ,bV/2+cV/4+dV/8
      x_3, y_3 = bU/4*3+cU/16*9+dU/64*27 ,bV/4*3+cV/16*9+dV/64*27
      xs.extend([x_1, x_2, x_3])
      ys.extend([y_1, y_2, y_3])
      hdgs.extend([]) # THIS WON'T BE USED
    else:
      xs.append(x1/2)
      ys.append(y1/2)
  return numpy.array(xs), numpy.array(ys), numpy.array(hdgs)



def find_t(param, l, tol=1e-8):
  bU, cU, dU, bV, cV, dV = param
  def integrand(t):
    du = bU+2*cU*t+3*dU*t**2
    dv = bV+2*cV*t+3*dV*t**2
    return math.sqrt(du**2+dv**2)
  def objective(t):
      current_length, _ = quad(integrand, 0, t, epsabs=tol, epsrel=tol)
      return current_length-l
  sol = root_scalar(objective, bracket=[0.0, 1.0], method='bisect', xtol=tol)
  return sol.root

def getLength(param):
  bU, cU, dU, bV, cV, dV = param
  def integrand(p):
    du = bU+2*cU*p+3*dU*p**2
    dv = bV+2*cV*p+3*dV*p**2
    return numpy.sqrt(du**2+dv**2)
  length, _ = quad(integrand, 0, 1)
  return length

def rectifyRoadData(road, length_new):
  length = get(road, "length")
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

def initRoadArc(id, md=0.02):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      planView = road.find('planView')
      gs = planView.findall('geometry')
      params = solveInitialCurve(gs, md)
      ## 计算道路方程
      planView.clear()
      length = 0
      x, y = get(gs[0], 'x'), get(gs[0], 'y')
      for param in params:
        print(param)
        ans = bezierToParam(param)
        l = getLength(ans)
        g = ET.Element('geometry')
        set(g, 's', length)
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
        length += l
        x += param[0]
        y += param[1]
        g.append(poly)
        planView.append(g)
      rectifyRoadData(road, length)
      return

def bezierToParam(param):
  x3, y3, l0, l1, h0, h1 = param
  x1, y1 =    l0*math.cos(h0),    l0*math.sin(h0)
  x2, y2 = x3-l1*math.cos(h1), y3-l1*math.sin(h1)
  bU, cU, dU = 3*x1, -6*x1+3*x2, 3*x1-3*x2+x3
  bV, cV, dV = 3*y1, -6*y1+3*y2, 3*y1-3*y2+y3
  return bU, cU, dU, bV, cV, dV

def getGBezier(g):
  x, y, l0, l1 = 0, 0, 1, 1
  h0, h1 = getHdg(g, 0), getHdg(g, 1)
  line = g.find('line')
  if line != None:
    x = get(g, 'length')*math.cos(h0)
    y = get(g, 'length')*math.sin(h0)
  poly = g.find('paramPoly3')
  if poly != None:
    bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
    bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
    x_, y_ = bU+cU+dU, bV+cV+dV
    x = x_*math.cos(h0)-y_*math.sin(h0)
    y = x_*math.sin(h0)+y_*math.cos(h0)
    l0 = math.sqrt((bU/3          )**2+(bV/3)          **2)
    l1 = math.sqrt((bU/3+cU/3*2+dU)**2+(bV/3+cV/3*2+dV)**2)
  return x, y, l0, l1, h0, h1

## 拟合圆弧时，v0=v1=cos(theta/2)/(3*cos^2(theta/4))
def editRoadArc(id, v0, v1, h0, h1, gi):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      planView = road.find('planView')
      gs = planView.findall('geometry')
      if gi >= len(gs):
        print("ERROR, out of range!")
        return

      ## 计算道路方程
      length_new = 0
      for i in range(len(gs)):
        if i < gi-1:
          length_new += get(gs[i], 'length')

        elif i == gi-1 and h0 != 0 or i == gi or i == gi+1 and h1 != 0:
          bezier = getGBezier(gs[i])
          if i == gi-1 and h0 != 0:
            bezier[5] += h0
          elif i == gi:
            euc_dis = math.sqrt(bezier[0]**2+bezier[1]**2)
            bezier[2] += v0*euc_dis
            bezier[3] += v1*euc_dis
            bezier[4] += h0
            bezier[5] += h1
          else:
            bezier[4] += h1

          param = bezierToParam(bezier)
          l = getLength(param)
          set(gs[i], 'hdg', 0)
          set(gs[i], 'length', l)
          gs[i].clear()
          poly = ET.Element('paramPoly3')
          set(poly, 'bU', param[0])
          set(poly, 'cU', param[1])
          set(poly, 'dU', param[2])
          set(poly, 'bV', param[3])
          set(poly, 'cV', param[4])
          set(poly, 'dV', param[5])
          length_new += l
          gs[i].append(poly)
        else:
          length_new += get(gs[i], 'length')

      rectifyRoadData(road, length_new)
      return