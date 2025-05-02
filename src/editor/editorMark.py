import xml.etree.ElementTree as ET
from editor.editor import editor

from Xodr.xodrParser import XParser
from Json.carDetector import detector
from utils.constants import *

class editorMark(editor):
  def __init__(self):
    editor.__init__(self)
      
  ## 修改指定道路的指定车道的道路线信息.
  def edit(self, id, laneId, infoMap):
    road = XParser.roads[id]
    sections = road.find("lanes").findall("laneSection")

    for section in sections:
      lanes = section.findall(".//lane")

      for lane in lanes:
        if lane.get('id') != laneId:
          continue

        roadMark = lane.find("roadMark")
        if roadMark == None:
          roadMark = ET.Element("roadMark")
          lane.append(roadMark)
        
        roadMark.set("sOffset",     infoMap["sOffset"])
        roadMark.set("type",        infoMap["typ"])
        roadMark.set("weight",      infoMap["weight"])
        roadMark.set("color",       infoMap["color"])
        roadMark.set("laneChange",  infoMap["laneChange"])
        break

