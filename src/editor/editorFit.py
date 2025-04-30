import xml.etree.ElementTree as ET
from scipy.optimize import least_squares
from editor.editor import editor

from Xodr.xodrParser import XParser
from Xodr.xodrDataGetter import dataGetter
from Json.jsonParser import JParser
from Json.carDetector import detector

from utils.constants import *
from utils.calculator import bezierToPoly3, poly3ToXYH
from utils.pltShow import showCurve

class editorFit(editor):
  def __init__(self):
    pass
  
  def edit(self, id, md, st):
    if id == "random":
      detector.setCandidates()
      id = detector.getRandomId1()

    road = XParser.roads[id]
    planView = road.find('planView')
    gs = planView.findall('geometry')
    beziers = self.solveInitialCurve(gs, md, st)
    ## 计算道路方程
    planView.clear()
    length = 0
    x, y = getData(gs[0], 'x'), getData(gs[0], 'y')
    params = []
    for bezier in beziers:
      param = bezierToPoly3(bezier)
      l = XParser.getLength(param, 1)
      param.append(x-getData(gs[0], 'x'))
      param.append(y-getData(gs[0], 'y'))
      params.append(param)

      g = ET.Element('geometry')
      setData(g, 's', length)
      setData(g, 'x', x)
      setData(g, 'y', y)
      setData(g, 'hdg', 0)
      setData(g, 'length', l)
      poly = ET.Element('paramPoly3')
      setData(poly, 'aU', 0)
      setData(poly, 'bU', param[0])
      setData(poly, 'cU', param[1])
      setData(poly, 'dU', param[2])
      setData(poly, 'aV', 0)
      setData(poly, 'bV', param[3])
      setData(poly, 'cV', param[4])
      setData(poly, 'dV', param[5])
      length += l
      x += bezier[0]
      y += bezier[1]
      g.append(poly)
      planView.append(g)

    showCurve(params)
    self.rectifyRoadData(road, length)
    return id, len(beziers)
  
  def fitConstraindCurve(self, x_data, y_data, h_data, params, MAX_DEVIATION):
    x1, y1, dx0, dy0, dx1, dy1, euc_dis = params
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
    lower = [0        ,         0]+[0]*n_points
    upper = [numpy.inf, numpy.inf]+[1]*n_points
    result = least_squares(fun=residuals, x0=initial_guess, bounds=(lower, upper), max_nfev=1e3)
    ## 计算结果
    ans = []
    size = int(len(result.fun)/2)
    index, max = -1, MAX_DEVIATION
    for i in range(2, size-2):
      delta = math.sqrt(result.fun[i]**2+result.fun[i+size]**2)/euc_dis
      if max < delta:
        max = delta
        index = i
    if index < 0:
      # print("good")
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
      # print("bad", index, max, size)
      x_data0, x_data1 = x_data[:index], x_data[index+1:]-x_data[index]
      y_data0, y_data1 = y_data[:index], y_data[index+1:]-y_data[index]
      h_data0, h_data1 = h_data[:index], h_data[index+1:]
      x10, x11 = x_data[index], x1-x_data[index]
      y10, y11 = y_data[index], y1-y_data[index]
      dx2, dy2 = math.cos(h_data[index]), math.sin(h_data[index])
      params0 = [x10, y10, dx0, dy0, dx2, dy2, euc_dis]
      params1 = [x11, y11, dx2, dy2, dx1, dy1, euc_dis]
      ans.extend(self.fitConstraindCurve(x_data0, y_data0, h_data0, params0, MAX_DEVIATION))
      ans.extend(self.fitConstraindCurve(x_data1, y_data1, h_data1, params1, MAX_DEVIATION))
    
    return ans

  def solveInitialCurve(self, gs, maxDeviation, step):
    g0, g1 = gs[0], gs[-1]
    h0, h1 = getData(g0, 'hdg'),   getData(g1, 'hdg')
    x0, y0 = getData(g0, 'x')   ,  getData(g0, 'y')
    x1, y1 = getData(g1, 'x')-x0,  getData(g1, 'y')-y0

    poly = g0.find('paramPoly3')
    if poly != None:
      bU, bV = getData(poly, 'bU'), getData(poly, 'bV')
      h0 = (h0+math.atan2(bV, bU))%(2*math.pi)
    line = g1.find('line')
    if line != None:
      x1 += getData(g1, 'length')*math.cos(h1)
      y1 += getData(g1, 'length')*math.sin(h1)
    poly = g1.find('paramPoly3')
    if poly != None:
      bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
      bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
      x_, y_ = bU+cU+dU, bV+cV+dV
      x1 += x_*math.cos(h1)-y_*math.sin(h1)
      y1 += x_*math.sin(h1)+y_*math.cos(h1)
      h1 = (h1+math.atan2(bV+2*cV+3*dV, bU+2*cU+3*dU))%(2*math.pi)

    dx0, dy0 = math.cos(h0), math.sin(h0)
    dx1, dy1 = math.cos(h1), math.sin(h1)
    x_data, y_data, h_data = self.getMidData(gs, x0, y0, step)

    params = [x1, y1, dx0, dy0, dx1, dy1, math.sqrt(x1**2+y1**2)]
    ans = self.fitConstraindCurve(x_data, y_data, h_data, params, maxDeviation)
    return ans
  
  def rectifyRoadData(self, road, length_new):
    length = getData(road, "length")
    setData(road, 'length', length_new)
    sections = road.find('lanes').findall('laneSection')
    elevas = road.find('elevationProfile').findall('elevation')
    widths = road.find('lanes').findall('.//width')
    k_l = length_new/length
    for section in sections:
      setData(section, 's', getData(section, 's')*k_l)
    for eleva in elevas:
      setData(eleva, 's', getData(eleva, 's')*k_l)
      setData(eleva, 'b', getData(eleva, 'b')/k_l)
      setData(eleva, 'c', getData(eleva, 'c')/(k_l**2))
      setData(eleva, 'd', getData(eleva, 'd')/(k_l**3))
    for width in widths:
      setData(width, 'sOffset', getData(width, 'sOffset')*k_l)
      setData(width, 'b', getData(width, 'b')/k_l)
      setData(width, 'c', getData(width, 'c')/(k_l**2))
      setData(width, 'd', getData(width, 'd')/(k_l**3))

    gs = road.find('planView').findall('geometry')
    for infos in JParser.carPosition[-1][id].values():
      for carInfo in infos:
        carInfo["pos"] *= k_l
        for i in range(len(gs)):
          s0 = getData(gs[i], "s")
          s1 = getData(road, "length") if i == len(gs)-1 else getData(gs[i+1], "s")
          
          if carInfo["pos"] >= s0 and carInfo["pos"] < s1:
            hdg  = getData(gs[i], 'hdg')
            x, y = getData(gs[i], 'x'), getData(gs[i], 'y')
            poly = gs[i].find('paramPoly3')
            bU, cU, dU, bV, cV, dV = dataGetter.getPoly3Params(poly)
            t = carInfo["pos"]-s0
            u = bU*t+cU*t**2+dU*t**3
            v = bV*t+cV*t**2+dV*t**3
            x += u*math.cos(hdg)-v*math.sin(hdg)
            y += u*math.sin(hdg)+v*math.cos(hdg)
            hdg += math.atan2(bV+2*cV*t+3*dV*t**2, bU+2*cU*t+3*dU*t**2)

            x += carInfo["dis"]*math.sin(hdg)
            y -= carInfo["dis"]*math.cos(hdg)
            ord = JParser.getOrd(carInfo)
            ord["position"]['x'] = x
            ord["position"]['z'] = y
            if ord.get("angle") != None:
              if carInfo["dis"] > 0:
                ord["angle"]["y"] =  hdg*180/math.pi
              else:
                ord["angle"]["y"] = -hdg*180/math.pi
            else:
              if carInfo["dis"] > 0:
                ord["rotation"]["y"] =  hdg*180/math.pi
              else:
                ord["rotation"]["y"] = -hdg*180/math.pi
            break

  def getMidData(self, gs, x0, y0, step):
    xs, ys, hs = [], [], []
    position = step

    for g in gs:
      length = getData(g, 'length')
      x = getData(g, 'x')-x0
      y = getData(g, 'y')-y0
      h = getData(g, 'hdg')

      poly = g.find('paramPoly3')
      if poly != None:
        while length > position:
          bU, cU, dU, bV, cV, dV = dataGetter.getPoly3Params(poly)
          dx, dy, dh = poly3ToXYH(bU, cU, dU, bV, cV, dV, position)
          xs.append(x+dx*math.cos(h)-dy*math.sin(h))
          ys.append(y+dx*math.sin(h)+dy*math.cos(h))
          hs.append((h+dh)%(2*math.pi))
          position += step
      else:
        while length > position:
          dx = position*math.cos(h)
          dy = position*math.sin(h)
          xs.append(x+dx)
          ys.append(y+dy)
          hs.append(h%(2*math.pi))
          position += step
      position -= length
    return numpy.array(xs), numpy.array(ys), numpy.array(hs)