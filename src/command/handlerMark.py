from editor.editorMark import editorMark
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

from collections import defaultdict

class handlerMark:
  def __init__(self):
    self.editorM = editorMark()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    li = "random"
    infoMap = defaultdict(dict)
    infoMap["sOffset"]	 	= "0"
    infoMap['type'] 			= "solid"
    infoMap['weight'] 		= "standard"
    infoMap['color'] 			= "standard"
    infoMap['laneChange'] = "none"

    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = param[1]
        case 'li': li = param[1]
        case 'info': 
          xList = param[1].split(',')
          for x in xList:
            nameValue = x.split(':')
            infoMap[nameValue[0]] = nameValue[1]

    self.editorM.edit(id=id, laneId=li, infoMap=infoMap)
    
handlerM = handlerMark()
