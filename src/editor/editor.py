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
    print("here")
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
    id = road.get('id')
    for infos in JParser.carPosition[-1][id].values():
      for carInfo in infos:
        carInfo["pos"] *= k_l
        for i in range(len(gs)):
          s0 = getData(gs[i], "s")
          s1 = getData(road, "length") if i == len(gs)-1 else getData(gs[i+1], "s")
          
          if carInfo["pos"] >= s0 and carInfo["pos"] < s1:
            hdg  = getData(gs[i], 'hdg')
            x, y = getData(gs[i], 'x'), getData(gs[i], 'y')
            s = carInfo["pos"]-s0

            line = gs[i].find('line')
            if line != None:
              x += s*math.cos(hdg)
              y += s*math.sin(hdg)
            else:
              poly = gs[i].find('paramPoly3')
              u, v, h = xDataGetter.getPolyPosXYH(poly, s)      
              x += u*math.cos(hdg)-v*math.sin(hdg)
              y += u*math.sin(hdg)+v*math.cos(hdg)
              hdg += h

            x += carInfo["dis"]*math.sin(hdg)
            y -= carInfo["dis"]*math.cos(hdg)
            ord = jDataGetter.getOrd(carInfo)
            ord["position"]['x'] = x
            ord["position"]['z'] = y
            if ord.get("angle") != None:
              ord["angle"]["y"] = hdg2ang(carInfo["dhdg"]+hdg)
            else:
              ord["rotation"]["y"] = hdg2ang(carInfo["dhdg"]+hdg)
            break