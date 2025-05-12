import xml.etree.ElementTree as ET
import math

from editor.editor import editor
from xodrs.xodrParser import XParser
from xodrs.xodrDataGetter import xDataGetter

from utils.lambdas import *
from utils.pltShow import showCurve

class editorCurve(editor):
  def __init__(self):
    editor.__init__(self)

  ## 拟合圆弧时, v0=v1=cos(theta/2)/(3*cos^2(theta/4))
  ## 参数含义见 readme
  def edit(self, id, x0, y0, v0, h0, x1, y1, v1, h1, gi):
    road = XParser.roads[id]
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
      param = xDataGetter.bezierToPoly3(bezier)
      l = xDataGetter.poly3ToLength(param, 1)
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

        if i == 0:
          XParser.hdgs[id][0] = bezier[4]
        elif i == len(gs)-1:
          XParser.hdgs[id][1] = bezier[5]

      elif i >= gi+1:
        setData(gs[i], 's', lengthNew)
      lengthNew += l

    showCurve(params)
    self.rectifyRoadData(road, lengthNew)

  def getGBezier(self, g):
    x, y, l0, l1 = 0, 0, 1, 1
    h0, h1 = getData(g, 'hdg'), getData(g, 'hdg')
    line = g.find('line')
    if line != None:
      x = getData(g, 'length')*math.cos(h0)
      y = getData(g, 'length')*math.sin(h0)
    poly = g.find('paramPoly3')
    if poly != None:
      bU, cU, dU, bV, cV, dV = xDataGetter.getPoly3Params(poly)
      x_, y_ = bU+cU+dU, bV+cV+dV
      x = x_*math.cos(h0)-y_*math.sin(h0)
      y = x_*math.sin(h0)+y_*math.cos(h0)
      h0 = (h0+math.atan2(bV          , bU          ))%(2*math.pi)
      h1 = (h1+math.atan2(bV+2*cV+3*dV, bU+2*cU+3*dU))%(2*math.pi)
      l0 = math.sqrt((bU/3          )**2+(bV/3)          **2)
      l1 = math.sqrt((bU/3+cU/3*2+dU)**2+(bV/3+cV/3*2+dV)**2)
    return [x, y, l0, l1, h0, h1]