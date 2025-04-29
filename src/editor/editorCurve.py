import xml.etree.ElementTree as ET

import Xodr.xodrParser as Xparser
import Json.jsonParser as JParser
import Json.vehicleDetector as detector
from utils.constants import *
from utils.calculator import bezierToPoly3
from utils.pltShow import showCurve

class editorCurve:
  def __init__(self):
    pass

  ## 拟合圆弧时，v0=v1=cos(theta/2)/(3*cos^2(theta/4))
  def edit(self, id, x0, y0, v0, h0, x1, y1, v1, h1, gi):
    if id == "random":
      detector.setCandidates()
      id = detector.getRandomId1()
      print(id)

    road = Xparser.roads[id]
    planView = road.find('planView')
    gs = planView.findall('geometry')
    if gi >= len(gs):
      print("ERROR, out of range!")
      return
    
    params = []
    ## 计算道路方程
    lengthNew = 0
    edit0 = x0 != 0 or y0 != 0 or h0 != 0
    edit1 = x1 != 0 or y1 != 0 or h1 != 0
    B = self.getGBezier(gs[gi])
    euc_dis = math.sqrt(B[0]**2+B[1]**2)
    for i in range(len(gs)):
      bezier = self.getGBezier(gs[i])
      judge = i == gi-1 and edit0 or i == gi or i == gi+1 and edit1
      deltaX, deltaY = 0, 0
      if judge:
        if i == gi-1 and edit0:
          bezier[0] += x0*euc_dis
          bezier[1] += y0*euc_dis
          bezier[5] += h0
        elif i == gi:
          deltaX, deltaY = x0*euc_dis, y0*euc_dis
          bezier[0] += (x1-x0)*euc_dis
          bezier[1] += (y1-y0)*euc_dis
          bezier[2] += v0*euc_dis
          bezier[3] += v1*euc_dis
          bezier[4] += h0
          bezier[5] += h1
        else:
          deltaX, deltaY = x1*euc_dis, y1*euc_dis
          bezier[0] -= x1*euc_dis
          bezier[1] -= y1*euc_dis
          bezier[4] += h1

      x = getData(gs[i], 'x')+deltaX
      y = getData(gs[i], 'y')+deltaY
      param = bezierToPoly3(bezier)
      l = Xparser.getLength(param, 1)
      param.append(x-getData(gs[0], 'x'))
      param.append(y-getData(gs[0], 'y'))
      params.append(param)
      
      if judge:
        gs[i].clear()
        setData(gs[i], 's', lengthNew)
        setData(gs[i], 'x', x)
        setData(gs[i], 'y', y)
        setData(gs[i], 'hdg', 0)
        setData(gs[i], 'length', l)
        poly = ET.Element('paramPoly3')
        setData(poly, 'aU', 0)
        setData(poly, 'bU', param[0])
        setData(poly, 'cU', param[1])
        setData(poly, 'dU', param[2])
        setData(poly, 'aV', 0)
        setData(poly, 'bV', param[3])
        setData(poly, 'cV', param[4])
        setData(poly, 'dV', param[5])
        gs[i].append(poly)
      elif i >= gi+1:
        setData(gs[i], 's', lengthNew)
      lengthNew += l

    showCurve(params)
    self.rectifyRoadData(road, lengthNew)

  ## PRIVATE METHODS

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
    for infos in JParser.carData[-1][id].values():
      for carInfo in infos:
        carInfo["pos"] *= k_l
        for i in range(len(gs)):
          s0 = getData(gs[i], "s")
          s1 = getData(road, "length") if i == len(gs)-1 else getData(gs[i+1], "s")
          
          if carInfo["pos"] >= s0 and carInfo["pos"] < s1:
            hdg  = getData(gs[i], 'hdg')
            x, y = getData(gs[i], 'x'), getData(gs[i], 'y')
            poly = gs[i].find('paramPoly3')
            bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
            bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
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

  def getGBezier(self, g):
    x, y, l0, l1 = 0, 0, 1, 1
    h0, h1 = getData(g, 'hdg'), getData(g, 'hdg')
    line = g.find('line')
    if line != None:
      x = getData(g, 'length')*math.cos(h0)
      y = getData(g, 'length')*math.sin(h0)
    poly = g.find('paramPoly3')
    if poly != None:
      bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
      bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
      x_, y_ = bU+cU+dU, bV+cV+dV
      x = x_*math.cos(h0)-y_*math.sin(h0)
      y = x_*math.sin(h0)+y_*math.cos(h0)
      h0 = (h0+math.atan2(bV          , bU          ))%(2*math.pi)
      h1 = (h1+math.atan2(bV+2*cV+3*dV, bU+2*cU+3*dU))%(2*math.pi)
      l0 = math.sqrt((bU/3          )**2+(bV/3)          **2)
      l1 = math.sqrt((bU/3+cU/3*2+dU)**2+(bV/3+cV/3*2+dV)**2)
    return [x, y, l0, l1, h0, h1]