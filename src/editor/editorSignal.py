import xml.etree.ElementTree as ET
from editor.editor import editor

from Xodr.xodrParser import XParser
from Json.carDetector import detector
from utils.constants import *

class editorSignal(editor):
  def __init__(self):
    pass
      
  ## 修改指定道路的指定车道的道路线信息.
  def edit(self):
    print("TO BE DONE")
