from handler.handler import handler
from editor.editorSlope import editorSlope
from xodrs.xodrParser import XParser
from jsons.jsonParser import JParser
from utils.random import *

class handlerSlope(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorSl = editorSlope()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    v = 0
    m = 'mul'
    mv = 0
    ms = 0
    sh = False
    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = getRandomId1(param[1])
        case 'v': v = getRandomValue(param[1])
        case 'm': m = param[1]
        case 'mv': mv = int(param[1])
        case 'ms': ms = int(param[1])
        case 'sh': sh = int(param[1])
        case _: print("Illegal parameter!")

    if 'id' not in locals():
      print("Id not given!")
      return "Id not given!"
    self.editorSl.edit(id=id, value=v, mode=m, move=mv, maxStep=ms, sameHdg=sh)
    return f"slope id={id} v={v} m={m} ms={ms} sh={sh}" 


handlerSl = handlerSlope()