import xml.etree.ElementTree as ET
import variables as vars
from constants import *
from collections import deque
import numpy

def setWidth(width: ET.Element, value, mode, smooth = 0, distance = 0):
  match mode:
    case 'add':
      if smooth == -1:
        a = get(width, 'a')
        b = get(width, 'b')
        c = get(width, 'c')
        d = get(width, 'd')
        x = distance-get(width, 'sOffset')
        newC = c+3*value/x**2
        newD = d-2*value/x**3
        set(width, 'c', newC)
        set(width, 'd', newD)
      elif smooth == 1:
        a = get(width, 'a')
        b = get(width, 'b')
        c = get(width, 'c')
        d = get(width, 'd')
        x = distance-get(width, 'sOffset')
        newC = c-3*value/x**2
        newD = d+2*value/x**3
        set(width, 'a', a+value)
        set(width, 'c', newC)
        set(width, 'd', newD)
      else:
        set(width, 'a', value+get(width, 'a'))

    case 'mul':
      if smooth == -1:
        a = get(width, 'a')
        b = get(width, 'b')
        c = get(width, 'c')
        d = get(width, 'd')
        x = distance-get(width, 'sOffset')
        newC = c*value-(3*a+2*b*x)*(1-value)/x**2
        newD = d*value+(2*a+  b*x)*(1-value)/x**3
        set(width, 'c', newC)
        set(width, 'd', newD)
      elif smooth == 1:
        a = get(width, 'a')
        b = get(width, 'b')
        c = get(width, 'c')
        d = get(width, 'd')
        x = distance-get(width, 'sOffset')
        newC = c+(3*a+2*b*x)*(1-value)/x**2
        newD = d-(2*a+  b*x)*(1-value)/x**3
        set(width, 'a', a*value)
        set(width, 'b', b*value)
        set(width, 'c', newC)
        set(width, 'd', newD)
      else:
        set(width, 'a', value*get(width, 'a'))
        set(width, 'b', value*get(width, 'b'))
        set(width, 'c', value*get(width, 'c'))
        set(width, 'd', value*get(width, 'd'))
    case 'addt':
      a = get(width, 'a')
      b = get(width, 'b')
      x = distance-get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b-value/distance)
    case 'addh':
      a = get(width, 'a')
      b = get(width, 'b')
      x = get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b+value/distance)
    case _:
      return
    
# change specific road width (on lanes)
# Infos: [{"id":0, "lanes": [-1, 1, 2]}]

def changeRoadWidth(id, value, mode = 'add', smooth = False, infos = []):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      sections = road.find('lanes').findall('laneSection')
      sectsNum = len(sections)
      if infos == []:
        for i in range(sectsNum):
          lanesNum = len(sections[i].findall('.//lane'))-1
          value = value/lanesNum if mode == 'add' else value

          for lane in sections[i].findall('.//lane'):

            widths = lane.findall('width')
            widthNum = len(widths)

            for j in range(widthNum-1):
              if smooth and i == 0 and j == 0:
                  nextS = get(widths[j+1], 'sOffset')
                  setWidth(widths[j], value, mode, -1, nextS)
              elif smooth and i == sectsNum-1 and j == widthNum-2:
                  nextS = get(widths[j+1], 'sOffset')
                  setWidth(widths[j], value, mode,  1, nextS)
              else:
                setWidth(widths[j], value, mode)
      # Following codes won't be used now
      else:
        ids = []
        for i in infos:
          ids.append(i['id'])

        for i in infos:
          sectsNum = len(sections)
          if i['id'] >= sectsNum:
            print("Error, out of range.")
            return
          
          lanesNum = len(i['lanes'])
          value = value/lanesNum if mode == 'add' else value
          section = sections[i['id']]
          for lane in section.iter('.//lane'):
            if int(lane.get('id')) not in i['lanes']:
                continue
            
            widths = lane.findall('width')
            widthNum = len(widths)
            for j in range(widthNum-1):
              if smooth and j == 0 and i['id']-1 not in ids:
                nextS = get(widths[j+1], 'sOffset')
                setWidth(widths[j], value, mode, -1, nextS)
              elif smooth and j == widthNum-2 and i['id']+1 not in ids:
                nextS = get(widths[j+1], 'sOffset')
                setWidth(widths[j], value, mode,  1, nextS)
              else:
                setWidth(widths[j], value, mode)
      break

## 限制同向传播
## mul
def changeRoadsWidth(id, value, mode = 'add', maxLayer = 0, new = True):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      length = get(road, 'length')
      sections = road.find('lanes').findall('laneSection')
      sectsNum = len(sections)
      
      for i in range(sectsNum):
        lanesNum = len(sections[i].findall('.//lane'))-1
        w = value/lanesNum

        for lane in sections[i].findall('.//lane'):

          widths = lane.findall('width')
          widthNum = len(widths)

          for j in range(widthNum):
            setWidth(widths[j], w, mode, distance=length)
      
      if not new:
        return
      
      #tailV, headV = value, value
      #if mode == 'mul':
      #  tailV =
      vars.edits = numpy.zeros(1000)
      vars.edits[int(id)] = cons.BOTH_LOCKED

      link = road.find('link')
      pre = link.find('predecessor')
      suc = link.find('successor')

      if pre != None:
        setChange(cons.TAIL, int(id), maxLayer)
      if suc != None:
        setChange(cons.HEAD, int(id), maxLayer)

      for r in vars.root.iter('road'):
        newId = r.get('id')
        num = vars.edits[int(newId)]
        if num == cons.TAIL_EDITED:   # change tail
          print('tail')
          print(newId)
          changeRoadsWidth(newId, value, 'addt', new=False)
        elif num == cons.HEAD_EDITED: # change head
          print('head')
          print(newId)
          changeRoadsWidth(newId, value, 'addh', new=False)
        elif num == cons.BOTH_EDITED: # change both
          print('both')
          print(newId)
          changeRoadsWidth(newId, value, 'add', new=False)

      return

def setChange(di, id, maxLayer):
  queue = deque()
  layer = 0

  for info in vars.connectSets[id]:
    if info[1] == di:
      queue.append({"id": info[0], "di": info[2], "layer": 0})

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    di = item['di']
    layer = item['layer']

    if layer < maxLayer:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "layer": layer+1})

        case cons.TAIL_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "layer": layer+1})
        case cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "layer": layer+1})
        case _:
          continue
    
    elif layer == maxLayer and not di:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.TAIL_EDITED
        case cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.TAIL:
          queue.append({"id": info[0], "di": info[2], "layer": layer})
    elif layer == maxLayer and di:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.HEAD_EDITED
        case cons.TAIL_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.HEAD:
          queue.append({"id": info[0], "di": info[2], "layer": layer})