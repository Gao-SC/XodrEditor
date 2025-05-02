from handler.handler import handler
from editor.editorLane import editorLane
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

from collections import defaultdict

class handlerLane(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorM = editorLane()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    id = "random"
    li = "random"
    infoMap = defaultdict(dict)
    infoMap["type"]         = "driving"
    infoMap["level"]        = "false"
    infoMap["MsOffset"]	 	  = "0"
    infoMap['Mtype'] 			  = "solid"
    infoMap['Mweight'] 		  = "standard"
    infoMap['Mcolor'] 			= "standard"
    infoMap['MlaneChange']  = "none"

    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = getRandomId1(param[1])
        case 'li': li = param[1]
        case 'info': 
          xList = param[1].split(',')
          for x in xList:
            nameValue = x.split(':')
            infoMap[nameValue[0]] = nameValue[1]

    self.editorM.edit(id=id, laneId=li, infoMap=infoMap)

handlerL = handlerLane()
