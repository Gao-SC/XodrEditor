from utils.constants import *

class xodrDataGetter:
  def __init__(self):
    pass

  def getPoly3Params(self, poly):
    bU, cU, dU = getData(poly, 'bU'), getData(poly, 'cU'), getData(poly, 'dU')
    bV, cV, dV = getData(poly, 'bV'), getData(poly, 'cV'), getData(poly, 'dV')
    return bU, cU, dU, bV, cV, dV

  def getLanesWidth(self, road, pos):
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
      for i in range(1, len(widths)):
        sOffset = getData(widths[i], 'sOffset')
        if sOffset >= pos:
          w = widths[i-1]
          pos -= getData(w, 'sOffset')
          a, b = getData(w, 'a'), getData(w, 'b')
          c, d = getData(w, 'c'), getData(w, 'd')
          num = a+b*pos+c*pos**2+d*pos**3
          # TODO: 此处默认车道序号降序排列
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

dataGetter = xodrDataGetter()