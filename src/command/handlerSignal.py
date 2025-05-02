from command.handler import handler
from editor.editorSignal import editorSignal
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

from collections import defaultdict

class handlerSignal(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorSi = editorSignal()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    infoMap = defaultdict(dict)
    infoMap["s"]	 	            = "0"
    infoMap['t'] 			          = "0"
    infoMap['id'] 		          = None
    infoMap['name'] 			      = None
    infoMap['dynamic']          = "no"
    infoMap["orientation"]      = "+"
    infoMap['zOffset'] 			    = "0"
    infoMap['country'] 		      = "DE"
    infoMap['countryRevision']  = "2025"
    infoMap['type']             = "none"
    infoMap["subtype"]	 	      = "none"
    infoMap['value'] 			      = None
    infoMap['height'] 		      = "0"
    infoMap['width'] 			      = "0"
    infoMap['hOffset']          = "0"

    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = getRandomId1(param[1])
        case 'si': si = int(param[1])
        case 'info': 
          xList = param[1].split(',')
          for x in xList:
            nameValue = x.split(':')
            infoMap[nameValue[0]] = nameValue[1]

    self.editorSi.edit(id=id, signalId=si, infoMap=infoMap)

handlerSi = handlerSignal()