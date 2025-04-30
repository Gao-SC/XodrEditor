from command.handler import handler
from editor.editorSignal import editorSignal
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

class handlerSignal(handler):
  def __init__(self):
    handler.__init__(self)
    self.editorSi = editorSignal()

  def handle(self, command):
    pass


handlerSi = handlerSignal()