from command.handler import handler
from editor.editorSlope import editorSlope
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

class handlerSlope(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorSl = editorSlope()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    v = 0
    m = 'add'
    mv = 0
    ms = 0
    sh = False
    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = param[1]
        case 'v': v = getRandomValue(param[1])
        case 'm': m = param[1]
        case 'mv': mv = int(param[1])
        case 'ms': ms = int(param[1])
        case 'sh': sh = int(param[1])
        case _: print("Illegal parameter!")

    self.editorSl.edit(id=id, value=v, mode=m, move=mv, maxStep=ms, sameHdg=sh)


handlerSl = handlerSlope()