import numpy
import math
import variables as vars
from collections import deque
from constants import *

def changeRoadsSlope(id, value, mode, move, maxStep=0, sameHdg=0, new = True):
  if mode == 'mul' and move == cons.MOVE_BOTH:
    print('Params error!')
    return
  slope, eleva = value, value

  for road in vars.root.iter('road'):
    if road.get('id') == id:
      elevations = road.find('elevationProfile').findall('elevation')
      geometries = road.find('planView').findall('geometry')
      size = len(geometries)
      length = get(road, 'length')

      if mode == 'add':
        if move == cons.MOVE_TAIL:
          slope = value/length*-1
        elif move == cons.MOVE_HEAD:
          slope = value/length
        else:
          slope = 0
      elif mode == 'mul':
        if move == cons.MOVE_TAIL:
          eleva = value*length*-1
        elif move == cons.MOVE_HEAD:
          eleva = value*length
        
      for i in range(size):
        g = geometries[i]
        e = elevations[i]
        s = get(g, 's')

        if mode == 'add':
          set(e, 'b', get(e, 'b')+slope)
          if move == cons.MOVE_BOTH:
            set(e, 'a', get(e, 'a')+eleva)
          elif move == cons.MOVE_TAIL:
            set(e, 'a', get(e, 'a')+slope*(s-length))
          elif move == cons.MOVE_HEAD:
            set(e, 'a', get(e, 'a')+slope*s)
          
        elif mode == 'mul':
          set(e, 'b', get(e, 'b')+slope)
          if move == cons.MOVE_TAIL:
            set(e, 'a', get(e, 'a')+slope*(s-length))
          elif move == cons.MOVE_HEAD:
            set(e, 'a', get(e, 'a')+slope*s)

      if not new:
        return
      vars.edits = numpy.zeros(1000)
      vars.edits[int(id)] = cons.BOTH_LOCKED

      link = road.find('link')
      pre = link.find('predecessor')
      suc = link.find('successor')
      if move == cons.MOVE_HEAD and pre != None: 
        lockChange(cons.TAIL, int(id))
      if move == cons.MOVE_TAIL and suc != None: 
        lockChange(cons.HEAD, int(id))


      if move != cons.MOVE_HEAD and pre != None:
        hdg = get(geometries[0], 'hdg')
        setChange(cons.TAIL, int(id), maxStep, sameHdg, hdg)
      if move != cons.MOVE_TAIL and suc != None:
        hdg = get(geometries[size-1], 'hdg')
        setChange(cons.HEAD, int(id), maxStep, sameHdg, hdg)

      for r in vars.root.iter('road'):
        newId = r.get('id')
        num = vars.edits[int(newId)]
        if num == cons.TAIL_EDITED or num == cons.TAIL_EDITED2:   # change tail
          print("move tail" + newId)
          changeRoadsSlope(newId, eleva, 'add', cons.MOVE_TAIL, new=False)
        elif num == cons.HEAD_EDITED or num == cons.HEAD_EDITED2: # change head
          print("move head" + newId)
          changeRoadsSlope(newId, eleva, 'add', cons.MOVE_HEAD, new=False)
        elif num == cons.BOTH_EDITED:                             # change both
          print("move both" + newId)
          changeRoadsSlope(newId, eleva, 'add', cons.MOVE_BOTH, new=False)

      return

def lockChange(direction, id):
  for info in vars.connectSets[id]:
    if info[1] == direction:
      dir2 = info[2]
      if dir2:
        vars.edits[info[0]] = cons.HEAD_LOCKED
      else:
        vars.edits[info[0]] = cons.TAIL_LOCKED

def setChange(di, id, maxStep, sameHdg, hdg):
  queue = deque()

  for info in vars.connectSets[id]:
    if info[1] == di:
      queue.append({"id": info[0], "di": info[2], "step": 0})

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
        case cons.NOT_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "step": step+1})

        case cons.TAIL_LOCKED:
          vars.edits[id] = cons.HEAD_EDITED2
          for info in vars.connectSets[id]:
            if info[1] == cons.HEAD:
              queue.append({"id": info[0], "di": info[2], "step": step+1})

        case cons.HEAD_LOCKED:
          vars.edits[id] = cons.TAIL_EDITED2
          for info in vars.connectSets[id]:
            if info[1] == cons.TAIL:
              queue.append({"id": info[0], "di": info[2], "step": step+1})

        case cons.TAIL_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "step": step+1})
        case cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
          for info in vars.connectSets[id]:
            queue.append({"id": info[0], "di": info[2], "step": step+1})
        case _:
          continue
    
    elif step == maxStep and di == cons.TAIL:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.TAIL_EDITED
        case cons.HEAD_LOCKED:
          vars.edits[id] = cons.TAIL_EDITED2
        case cons.HEAD_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.TAIL:
          queue.append({"id": info[0], "di": info[2], "step": step})
    elif step == maxStep and di == cons.HEAD:
      match vars.edits[id]:
        case cons.NOT_EDITED:
          vars.edits[id] = cons.HEAD_EDITED
        case cons.TAIL_LOCKED:
          vars.edits[id] = cons.HEAD_EDITED2
        case cons.TAIL_EDITED:
          vars.edits[id] = cons.BOTH_EDITED
        case _:
          continue
      for info in vars.connectSets[id]:
        if info[1] == cons.HEAD:
          queue.append({"id": info[0], "di": info[2], "step": step})


'''def adjustElevation(id, start, h, layer, maxLayer):
  if layer >= maxLayer:
    return
  
  for road in vars.root.iter('road'):
    if int(road.get('id')) == id:
      jId = road.get('junction')

      if jId != '-1':
        for r in vars.root.iter('road'):
          if r.get('junction') == jId:
            changeRoadSlope(r.get('id'), h, 'add', 0,  False)
            link = r.find('link')
            pre, suc = link.find('predecessor'), link.find('successor')
            if pre != None:
              id = int(pre.get('elementId'))
              newStart = pre.get('contactPoint') == "start"
              adjustElevation(id, newStart, h, layer, maxLayer)
            if suc != None:
              id = int(suc.get('elementId'))
              newStart = suc.get('contactPoint') == "start"
              adjustElevation(id, newStart, h, layer, maxLayer)
      
      else:
        if vars.edits[id] == 0:
          if start:
            vars.edits[id] = 1
          else:
            vars.edits[id] = 2
        elif vars.edits[id] == 1 and not start:
          vars.edits[id] = 3
        elif vars.edits[id] == 2 and start:
          vars.edits[id] = 3

        elevations = road.find('elevationProfile').findall('elevation')
        geometries = road.find('planView').findall('geometry')
        if start:
          geoLength = get(geometries[ 0], 'length')
          a = get(elevations[0], 'a')+h
          b = get(elevations[0], 'b')+h/geoLength*-1
          set(elevations[0], 'a', a)
          set(elevations[0], 'b', b)
        else:
          geoLength = get(geometries[-1], 'length')
          b = get(elevations[-1], 'b')+h/geoLength
          set(elevations[-1], 'b', b)

      return
'''

'''# Integration approximation
def f(params, x):
  a = math.pow(params[0]+2*params[1]*x+3*params[2]*x**2, 2)
  b = math.pow(params[3]+2*params[4]*x+3*params[5]*x**2, 2)
  return math.sqrt(a+b)
def simpson(a, b, f, params):
  mid = (a+b)/2
  return (b-a)*(f(params, a)+4*f(params, mid)+f(params, b))/6
def work(l, r, f, params):
  mid = (l+r)/2
  if abs(simpson(l, mid, f, params)+simpson(mid, r, f, params)-simpson(l, r, f, params)) < 1e-3:
    return simpson(l, r, f, params)
  return work(l, mid, f, params)+work(mid, r, f, params)

def applyElevations(presice = False):
  for road in constants.root.iter('road'):
    elevations = road.find('elevationProfile').findall('elevation')
    geometries = road.find('planView').findall('geometry')
    size = len(geometries)

    for i in range(size):
      g = geometries[i]
      e = elevations[i]
      x, y = get(g, 'x'), get(g, 'y')
      x1, x2, x3 = 0, 0, 0
      y1, y2, y3 = 0, 0, 0
      hdg = get(g, 'hdg')
      length = get(g, 'length')

      # condition line
      if g.find('line') != None:  
        dx, dy = length*math.cos(hdg), length*math.sin(hdg)
        if presice:
          x1, y1 = x+dx/3,   y+dy/3
          x2, y2 = x+dx/3*2, y+dy/3*2
          x3, y3 = x+dx,     y+dy
        else:
          x1, y1 = x+dx,     y+dy
      # condition arc
      elif g.find('arc') != None:
        arc = g.find('arc')
        cur = get(arc, 'curvature')
        theta = cur*length

        if presice:
          x_1 = math.sin(theta/3)/cur
          y_1 = (1-math.cos(theta/3))/cur
          x_2 = math.sin(theta/3*2)/cur
          y_2 = (1-math.cos(theta/3*2))/cur
          x_3 = math.sin(theta)/cur
          y_3 = (1-math.cos(theta))/cur
          x1 = x_1*math.cos(hdg)-y_1*math.sin(hdg)+x
          y1 = x_1*math.sin(hdg)+y_1*math.cos(hdg)+y
          x2 = x_2*math.cos(hdg)-y_2*math.sin(hdg)+x
          y2 = x_2*math.sin(hdg)+y_2*math.cos(hdg)+y
          x3 = x_3*math.cos(hdg)-y_3*math.sin(hdg)+x
          y3 = x_3*math.sin(hdg)+y_3*math.cos(hdg)+y
        else:
          x_ = math.sin(theta)/cur
          y_ = (1-math.cos(theta))/cur
          x1 = x_*math.cos(hdg)-y_*math.sin(hdg)+x
          y1 = x_*math.sin(hdg)+y_*math.cos(hdg)+y
      # condition poly3
      elif g.find('paramPoly3') != None:
        poly3 = g.find('paramPoly3')
        bU = get(poly3, 'bU')
        cU = get(poly3, 'cU')
        dU = get(poly3, 'dU')
        bV = get(poly3, 'bV')
        cV = get(poly3, 'cV')
        dV = get(poly3, 'dV')
        params = [bU, cU, dU, bV, cV, dV]

        if presice:
          k1 = 1/3
          while True:
            res = work(0, k1, f, params)-length*1/3
            if res < 1e-4:
              break
            k1 = k1-res/f(params, k1)
          k2 = 2/3
          while True:
            res = work(0, k2, f, params)-length*2/3
            if res < 1e-4:
              break
            k2 = k2-res/f(params, k2)
          x_1 = bU*k1+cU*k1**2+dU*k1**3
          x_2 = bU*k2+cU*k2**2+dU*k2**3
          x_3 = bU   +cU      +dU
          y_1 = bV*k1+cV*k1**2+dV*k1**3
          y_2 = bV*k2+cV*k2**2+dV*k2**3
          y_3 = bV   +cV      +dV
          x1 = x_1*math.cos(hdg)-y_1*math.sin(hdg)+x
          y1 = x_1*math.sin(hdg)+y_1*math.cos(hdg)+y
          x2 = x_2*math.cos(hdg)-y_2*math.sin(hdg)+x
          y2 = x_2*math.sin(hdg)+y_2*math.cos(hdg)+y
          x3 = x_3*math.cos(hdg)-y_3*math.sin(hdg)+x
          y3 = x_3*math.sin(hdg)+y_3*math.cos(hdg)+y
        else:
          x_ = bU+cU+dU
          y_ = bV+cV+dV
          x1 = x_*math.cos(hdg)-y_*math.sin(hdg)+x
          y1 = x_*math.sin(hdg)+y_*math.cos(hdg)+y
      else:
        print('TO BE DONE')
        continue
      
      h0 = terrain[int(x )][int(y )]
      h1 = terrain[int(x1)][int(y1)]
      if presice:
        h2 = terrain[int(x2)][int(y2)]
        h3 = terrain[int(x3)][int(y3)]
        b, c, d = length/3, length/3*2, length
        A = numpy.array([[1, 0, 0, 0], [1, b, b**2, b**3], [1, c, c**2, c**3], [1, d, d**2, d**3]])
        B = numpy.array([h0, h1, h2, h3])
        ans = numpy.linalg.solve(A, B)
        set(e, 'a', ans[0])
        set(e, 'b', ans[1])
        set(e, 'c', ans[2])
        set(e, 'd', ans[3])
      else:
        A = numpy.array([[1, 0], [1, length]])
        B = numpy.array([h0, h1])
        ans = numpy.linalg.solve(A, B)
        set(e, 'a', ans[0])
        set(e, 'b', ans[1])
        set(e, 'c', 0)
        set(e, 'd', 0)'''