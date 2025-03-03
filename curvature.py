import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *
import numpy

from scipy.optimize  import root as scipy_root
from scipy.integrate import quad as scipy_quad


def eulerSpiral(Px, Py, Phdg, Qx, Qy, Qhdg):
  def equations(vars):
    k1, L = vars
    delta_theta = Qhdg - Phdg
    k2 = (2*delta_theta/L)-k1
    
    def theta(s):
      return Phdg+k1*s+(k2-k1)*(s**2)/(2*L)
    
    integrand_x = lambda s: numpy.cos(theta(s))
    integrand_y = lambda s: numpy.sin(theta(s))
    
    integral_x, _ = scipy_quad(integrand_x, 0, L)
    integral_y, _ = scipy_quad(integrand_y, 0, L)
    
    target_x = Qx - Px
    target_y = Qy - Py
    return [integral_x-target_x, integral_y-target_y]
  
  initial_L = numpy.sqrt((Qx-Px)**2+(Qy-Py)**2)
  initial_k1 = 0.0
  initial_guess = [initial_k1, initial_L]

  result = scipy_root(equations, initial_guess, method='lm')
  if result.success:
      k1, L = result.x
      delta_theta = Qhdg-Phdg
      k2 = (2*delta_theta/L)-k1
      return k1, k2, L
  else:
      return None
  
def getArcPosition(gs, length, position):
  def f(params, x):
    a = math.pow(params[0]+2*params[1]*x+3*params[2]*x**2, 2)
    b = math.pow(params[3]+2*params[4]*x+3*params[5]*x**2, 2)
    return math.sqrt(a+b)
  def simpson(a, b, f, params):
    mid = (a+b)/2
    return (b-a)*(f(params, a)+4*f(params, mid)+f(params, b))/6
  def work(l, r, f, params):
    mid = (l+r)/2
    if abs(simpson(l, mid, f, params)+simpson(mid, r, f, params)-simpson(l, r, f, params)) < 1e-3:
      return simpson(l, r, f, params)
    return work(l, mid, f, params)+work(mid, r, f, params)

  m = position*length

  g0 = gs[0]
  x0, y0 = get(g0 , 'x'), get(g0 , 'y')
  hdg0 = get(g0 , 'hdg')
  _poly = g0.find('paramPoly3')
  if _poly != None:
    hdg0 += math.atan((get(_poly, 'bV'))/( get(_poly, 'bU')))

  g2 = gs[-1]
  x2, y2 = get(g2, 'x'), get(g2, 'y')
  hdg2 = get(g2, 'hdg')
  line_ = g2.find('line')
  if line_ != None:
    x2 += get(g2, 'length')*math.cos(hdg2)
    y2 += get(g2, 'length')*math.sin(hdg2)
  poly_ = g2.find('paramPoly3')
  if poly_ != None:
    bU = get(poly_, 'bU')
    cU = get(poly_, 'cU')
    dU = get(poly_, 'dU')
    bV = get(poly_, 'bV')
    cV = get(poly_, 'cV')
    dV = get(poly_, 'dV')
    x_ = bU+cU+dU
    y_ = bV*cV+dV
    x2 += x_*math.cos(hdg2)-y_*math.sin(hdg2)
    y2 += y_*math.sin(hdg2)+y_*math.cos(hdg2)
    hdg2 += math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU))

  x1, y1, hdg1 = 0, 0, 0
  for g in gs:
    s = get(g, 's')
    g_length = get(g, 'length')
    if s <= m and s+g_length > m:
      l = m-s
      hdg = get(g, 'hdg')
      x = get(g, 'x')
      y = get(g, 'y')

      line = g.find('line')
      if line != None:
        x1 = x+l*math.cos(hdg)
        y1 = y+l*math.sin(hdg)
        hdg1 = hdg
        break
      
      poly = g.find('paramPoly3')
      if poly != None:
        bU = get(poly, 'bU')
        cU = get(poly, 'cU')
        dU = get(poly, 'dU')
        bV = get(poly, 'bV')
        cV = get(poly, 'cV')
        dV = get(poly, 'dV')
        params = [bU, cU, dU, bV, cV, dV]

        k = l/g_length
        while True:
            res = work(0, k, f, params)-l
            if res < 1e-4:
              break
            k = k-res/f(params, k)

        x_ = bU*k+cU*k**2+dU*k**3
        y_ = bV*k+cV*k**2+dV*k**3
        x1 = x_*math.cos(hdg)-y_*math.sin(hdg)+x
        y1 = y_*math.sin(hdg)+y_*math.cos(hdg)+y
        hdg1 = hdg+math.atan((bV+2*cV*k+3*dV*k**2)/(bU+2*cU*k+3*dU*k**2))
        break

      print('not line or poly.')
      break
  return x0, y0, hdg0, x1, y1, hdg1, x2, y2, hdg2 
  
def changeRoadArc(id, value, position = 0.5):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      planView = road.find('planView')
      gs = planView.findall('geometry')
      length = get(road, 'length')

      x0, y0, hdg0, x1, y1, hdg1, x2, y2, hdg2 = getArcPosition(gs, length, position)
      k00, k01, L0 = eulerSpiral(x0, y0, hdg0, x1, y1, hdg1+value)
      k10, k11, L1 = eulerSpiral(x1, y1, hdg1+value, x2, y2, hdg2)
      print(k00, k01, L0)
      print(k10, k11, L1)
      new_length = L0+L1
      set(road, 'length', new_length)
      planView.clear()

      spiral0 = ET.Element("geometry")
      set(spiral0, 's', 0)
      set(spiral0, 'x', x0)
      set(spiral0, 'y', y0)
      set(spiral0, 'length', L0)
      set(spiral0, 'hdg', hdg0)
      s0 = ET.Element("spiral")
      set(s0, 'curvStart', k00)
      set(s0, 'curvEnd', k01)
      spiral0.append(s0)
      planView.append(spiral0)

      spiral1 = ET.Element("geometry")
      set(spiral1, 's', L0)
      set(spiral1, 'x', x1)
      set(spiral1, 'y', y1)
      set(spiral1, 'length', L1)
      set(spiral1, 'hdg', hdg1)
      s1 = ET.Element("spiral")
      set(s1, 'curvStart', k10)
      set(s1, 'curvEnd', k11)
      spiral1.append(s1)
      planView.append(spiral1)

      
      sections = road.find('lanes').findall('laneSection')
      elevas = road.find('elevationProfile').findall('elevation')
      widths = road.find('lanes').findall('.//width')
      k_length = new_length/length
      for section in sections:
        set(section, 's', get(section, 's')*k_length)
      for eleva in elevas:
        set(eleva, 's', get(eleva, 's')*k_length)
      for width in widths:
        set(width, 'sOffset', get(width, 'sOffset')*k_length)
      break
     

'''

# 获取需要的点
  
  a = math.sqrt((x2-x1)**2+(y2-y1)**2)
  b = math.sqrt((x1-x0)**2+(y1-y0)**2)
  c = math.sqrt((x0-x2)**2+(y0-y2)**2)
  S = abs((x1-x0)*(y2-y0)-(x2-x0)*(y1-y0))
  K = 2*S/(a*b*c)
  maxK = 2/c
  value = maxK if K+value > maxK else K+value
  if K == 0:
    return x0, y0, hdg0, (x0+x2)/2, (y0+y2)/2, hdg1, x2, y2, hdg2
  
  positive = (hdg2-hdg0)%(2*math.pi) < math.pi

  fi = math.atan((x2-x0)/(y0-y2))
  l = math.sqrt(1/K**2-c**2/4)
  Ox = (x0+x2)/2+l*math.cos(fi)
  Oy = (x0+x2)/2+l*math.sin(fi)
  n1 = [x2-x0, y2-y0]
  n2 = [Ox-x0, Oy-y0]
  if (n1[0]*n2[1]-n1[1]*n2[0] > 0) != positive:
    Ox = (x0+x2)/2-l*math.cos(fi)
    Oy = (x0+x2)/2-l*math.sin(fi)
  X = Ox+(x2-x0)/(K*c)
  Y = Oy-(y2-y0)/(K*c)

  return x0, y0, hdg0, X, Y, x2, y2, hdg2
'''