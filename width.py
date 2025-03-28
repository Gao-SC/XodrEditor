import xml.etree.ElementTree as ET
import math
import variables as vars
from constants import *
from collections import deque
import numpy

def setWidth(width: ET.Element, value, mode, distance=0):
  a = get(width, 'a')
  b = get(width, 'b')
  c = get(width, 'c')
  d = get(width, 'd')
  match mode:
    case 'add':
      set(width, 'a', value+get(width, 'a'))
    case 'stail1':
      x = distance-get(width, 'sOffset')
      newC = c-3*value/x**2
      newD = d+2*value/x**3
      set(width, 'a', a+value)
      set(width, 'c', newC)
      set(width, 'd', newD)
    case 'shead1':
      x = distance-get(width, 'sOffset')
      newC = c+3*value/x**2
      newD = d-2*value/x**3
      set(width, 'c', newC)
      set(width, 'd', newD)
    case 'stail2':
      x = distance-get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b-value/distance)
    case 'shead2':
      x = get(width, 'sOffset')
      value*x/distance
      set(width, 'a', a+value/distance*x)
      set(width, 'b', b+value/distance)

    case 'mul':
      set(width, 'a', value*get(width, 'a'))
      set(width, 'b', value*get(width, 'b'))
      set(width, 'c', value*get(width, 'c'))
      set(width, 'd', value*get(width, 'd'))
    case _:
      return
    
# change specific road width (on lanes)
# Infos: [-1, -1, 2]
## 仅有一个LaneSection
def changeRoadsWidth(id, value, mode='add', smooth=0, maxStep=0, sameHdg=0, laneIds=[], new=True):
  for road in vars.root.iter('road'):
    if road.get('id') == id:
      length = get(road, 'length')
      section = road.find('lanes').find('laneSection')

      if laneIds == []:
        for lane in section.findall('.//lane'):
          if lane.get('id') != '0':
            laneIds.append(int(lane.get('id')))
      lanesNum = len(laneIds)

      v = value/lanesNum if mode != 'mul' else value
      for lane in section.findall('.//lane'):
        lid = int(lane.get('id'))
        if lid not in laneIds:
          continue
        widths = lane.findall('width')
        widthNum = len(widths)


        for j in range(widthNum):
          match (mode, smooth):
            case ('add', x):
              setWidth(widths[j], v, 'add')
            case ('mul', x):
              setWidth(widths[j], v, 'mul')
            case ('addt', 1):
              if j == 0:
                nextS = get(widths[j+1], 'sOffset')
                setWidth(widths[j], v, 'stail1', distance=nextS)
            case ('addh', 1):
              if j == widthNum-2:
                nextS = get(widths[j+1], 'sOffset')
                setWidth(widths[j], v, 'shead1', distance=nextS)

            case ('addt', 2):
              setWidth(widths[j], v, 'stail2', distance=length)
            case ('addh', 2):
              setWidth(widths[j], v, 'shead2', distance=length)
            case _:
              continue

      if not new:
        return
      
      #tailV, headV = value, value
      #if mode == 'mul':
      #  tailV =
      vars.edits = numpy.zeros(1000)
      vars.edits[int(id)] = cons.BOTH_LOCKED
      vars.laneEdits = [[] for _ in range(1000)]
      vars.laneEdits[int(id)] = laneIds

      link = road.find('link')
      pre = link.find('predecessor')
      suc = link.find('successor')
      geometries = road.find('planView').findall('geometry')
      size = len(geometries)

      if pre != None:
        hdg = get(geometries[0], 'hdg')
        setChange(cons.TAIL, int(id), maxStep, sameHdg, hdg)
      if suc != None:
        hdg = get(geometries[size-1], 'hdg')
        setChange(cons.HEAD, int(id), maxStep, sameHdg, hdg)

      for r in vars.root.iter('road'):
        newId = r.get('id')
        num = vars.edits[int(newId)]
        if newId == "14":
          print(num)
        if num == cons.TAIL_EDITED and smooth:   # change tail #TODO
          changeRoadsWidth(newId, value, 'addt', smooth, laneIds=vars.laneEdits[int(newId)], new=False)
        elif num == cons.HEAD_EDITED and smooth: # change head
          changeRoadsWidth(newId, value, 'addh', smooth, laneIds=vars.laneEdits[int(newId)], new=False)
        elif num == cons.BOTH_EDITED: # change both
          changeRoadsWidth(newId, value, 'add', laneIds=vars.laneEdits[int(newId)], new=False)
      return

def setChange(di, id, maxStep, sameHdg, hdg):
  queue = deque()
  step = 0

  for info in vars.connectSets[id]:
    if info[1] == di:
      queue.append({"id": info[0], "di": info[2], "step": 0})
      vars.laneEdits[info[0]] = searchLane(id, info[0])

  while len(queue) > 0:
    item = queue.popleft()
    id = item['id']
    di = item['di']
    step = item['step']

    if sameHdg:
      for road in vars.root.iter('road'):
        if get(road, 'id') == id:
          planView = road.find('planView')
          for geometry in planView.iter('geometry'):
            newHdg = get(geometry, 'hdg')
            angle = (newHdg-hdg)%(2*math.pi)
            if angle > math.pi/4 and angle < math.pi/4*3 or angle > math.pi/4*5 and angle < math.pi/4*7:
              step = maxStep
              break
          break

    if step < maxStep:
      match vars.edits[id]:
        case cons.NOT_EDITED | cons.TAIL_EDITED | cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "step": step+1})
            vars.laneEdits[info[0]] = searchLane(id, info[0])
        case _:
          continue
    
    elif step == maxStep and not di:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.TAIL_EDITED
        case cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.TAIL:
          queue.append({"id": info[0], "di": info[2], "step": step})
          vars.laneEdits[info[0]] = searchLane(id, info[0])
    elif step == maxStep and di:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.HEAD_EDITED
        case cons.TAIL_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.HEAD:
          queue.append({"id": info[0], "di": info[2], "step": step})
          vars.laneEdits[info[0]] = searchLane(id, info[0])

def searchLane(id1, id2):
  ans = []
  for i in vars.laneEdits[id1]:
    x = vars.laneMap[str(id1)+" "+str(id2)+" "+str(i)]
    ans.append(int(x))
  return ans

'''
def  changeRoadWidth(id, value, mode='add', smooth=False, infos=[]):
  print(infos)
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

          for lane in section.findall('.//lane'):
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
'''