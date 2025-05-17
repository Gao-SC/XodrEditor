import math

from utils.lambdas import *
from jsons.jsonParser import JParser
from xodrs.xodrDataGetter import xDataGetter
from jsons.jsonDataGetter import jDataGetter

class editor(object):
  def __init__(self):
    pass
  
  def edit(self):
    pass

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
            bU, cU, dU, bV, cV, dV = xDataGetter.getPoly3Params(poly)
            t = carInfo["pos"]-s0
            u = bU*t+cU*t**2+dU*t**3
            v = bV*t+cV*t**2+dV*t**3
            x += u*math.cos(hdg)-v*math.sin(hdg)
            y += u*math.sin(hdg)+v*math.cos(hdg)
            hdg += math.atan2(bV+2*cV*t+3*dV*t**2, bU+2*cU*t+3*dU*t**2)

            x += carInfo["dis"]*math.sin(hdg)
            y -= carInfo["dis"]*math.cos(hdg)
            ord = jDataGetter.getOrd(carInfo)
            ord["position"]['x'] = x
            ord["position"]['z'] = y
            if ord.get("angle") != None:
              if carInfo["dis"] > 0:
                ord["angle"]["y"] =  hdg2ang(hdg)
              else:
                ord["angle"]["y"] = -hdg2ang(hdg)
            else:
              if carInfo["dis"] > 0:
                ord["rotation"]["y"] =  hdg2ang(hdg)
              else:
                ord["rotation"]["y"] = -hdg2ang(hdg)
            break