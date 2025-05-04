from handler.handler import handler
from editor.editorCurve import editorCurve
from editor.editorFit import editorFit
from xodrs.xodrParser import XParser
from jsons.jsonParser import JParser
from utils.random import *
from error.errors import *

class handlerCurve(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorC = editorCurve()
    self.editorF = editorFit()

  def handle(self, command):
    XParser.pushNewData()
    JParser.pushNewData()
    gi = "random"
    x0, y0, h0, v0 = 0, 0, 0, 0
    x1, y1, h1, v1 = 0, 0, 0, 0
    
    for i in range(1, len(command)):
      param = command[i].split('=')
      match param[0]:
        case 'id': id = getRandomId(param[1])
        case 'x0': x0 = getRandomValue(param[1])
        case 'y0': y0 = getRandomValue(param[1])
        case 'h0': h0 = getRandomValue(param[1])
        case 'v0': v0 = getRandomValue(param[1])
        case 'x1': x1 = getRandomValue(param[1])
        case 'y1': y1 = getRandomValue(param[1])
        case 'h1': h1 = getRandomValue(param[1])
        case 'v1': v1 = getRandomValue(param[1])
        case 'gi': 
          if param[1] != 'random':  gi = int(param[1])
        case _: print("Illegal parameter!")

    if 'id' not in locals():
      print("Id not given!")
      return "Id not given!"
    
    returnString = f"curve id={id} gi={gi} x0={x0} y0={y0} h0={h0} v0={v0} x1={x1} y1={y1} h1={h1} v1={v1}" 
    if gi == "random":
      id, lenGs = self.editorF.edit(id=id, md=0.01, st=1.0)
      gi = getRandomInt(lenGs)
      self.editorC.edit(id=id, gi=gi, x0=x0, y0=y0, h0=h0, v0=v0, x1=x1, y1=y1, h1=h1, v1=v1)
      return "fit"+returnString
    return returnString

handlerC = handlerCurve()

