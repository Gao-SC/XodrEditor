from editor.editorSignal import editorSignal
from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from utils.random import *

class handlerSignal:
  def __init__(self):
    self.editorSi = editorSignal()

  def handle(self, command):
    pass


handlerSi = handlerSignal()