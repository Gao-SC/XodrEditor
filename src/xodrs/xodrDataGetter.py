from scipy.optimize import root_scalar
from scipy.integrate import quad
import math
import numpy

from utils.lambdas import *

class xodrDataGetter:
  def __init__(self):
    pass

  def getPoly3Params(self, poly):
    bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
    bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
    return bU, cU, dU, bV, cV, dV

  def bezierToPoly3(self, param):
    x3, y3, l0, l1, h0, h1 = param
    x1, y1 =    l0*math.cos(h0),    l0*math.sin(h0)
    x2, y2 = x3-l1*math.cos(h1), y3-l1*math.sin(h1)
    bU, cU, dU = 3*x1, -6*x1+3*x2, 3*x1-3*x2+x3
    bV, cV, dV = 3*y1, -6*y1+3*y2, 3*y1-3*y2+y3
    return [bU, cU, dU, bV, cV, dV]

  def poly3ToLength(self, param, t):
    bU, cU, dU, bV, cV, dV = param
    def integrand(p):
      du = bU+2*cU*p+3*dU*p**2
      dv = bV+2*cV*p+3*dV*p**2
      return numpy.sqrt(du**2+dv**2)
    length, _ = quad(integrand, 0, t)
    return length

  def getPosWidths(self, road, pos):
    l = getData(road, "length")
    if pos < 0: pos = 0
    if pos > l: pos = l
    
    lanes = road.find('lanes').findall('.//lane')
    lws, rws = [], []

    for lane in lanes:
      id = getData(lane, 'id')
      if id == 0:
        continue

      widths = lane.findall('width')
      for i in range(len(widths)):
        s0 = getData(widths[i], 'sOffset')
        s1 = getData(road, 'length') if i == len(widths)-1 else getData(widths[i+1], 'sOffset')

        if s0 <= pos < s1:
          w = widths[i]
          pos -= getData(w, 'sOffset')
          a, b = getData(w, 'a'), getData(w, 'b')
          c, d = getData(w, 'c'), getData(w, 'd')
          num = a+b*pos+c*pos**2+d*pos**3
          # 此处默认车道序号降序排列
          if id < 0:
            rws.append(num)
          else:
            lws.insert(0, -num)
          break

    for i in range(1, len(lws)):
      lws[i] += lws[i-1]
    for i in range(1, len(rws)):
      rws[i] += rws[i-1]
    return lws, rws
  
  def getPosHdg(self, road, pos):
    l = getData(road, "length")
    if pos < 0: pos = 0
    if pos > l: pos = l

    gs = road.find('planView').findall('geometry')
    for i in range(len(gs)):
      s0 = getData(gs[i], 's')
      s1 = getData(road, 'length') if i == len(gs)-1 else getData(gs[i+1], 's')

      if s0 <= pos < s1:
        h0 = getData(gs[i], 'hdg')
        if gs[i].find('line') != None:
          return h0%(2*math.pi)
        
        poly = gs[i].find('paramPoly3')
        if poly != None:
          x, y, h = self.getPolyPosXYH(poly, pos-s0)
          return (h+h0)%(2*math.pi)
    return 0
  
  def getPolyPosXYH(self, poly, pos, tol=1e-8):
    bU, cU, dU, bV, cV, dV = self.getPoly3Params(poly)
    def integrand(t):
      du = bU+2*cU*t+3*dU*t**2
      dv = bV+2*cV*t+3*dV*t**2
      return math.sqrt(du**2+dv**2)
    def objective(t):
      currentLength, _ = quad(integrand, 0, t, epsabs=tol, epsrel=tol)
      return currentLength-pos
    sol = root_scalar(objective, bracket=[0.0, 1.0], method='bisect', xtol=tol)
    t = sol.root
    x = bU*t+cU*t**2+dU*t**3
    y = bV*t+cV*t**2+dV*t**3
    h = math.atan2(bV+2*cV*t+3*dV*t**2, bU+2*cU*t+3*dU*t**2)
    return x, y, h

dataGetter = xodrDataGetter()