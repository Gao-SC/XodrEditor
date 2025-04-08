import math
class cons:
    NOT_EDITED = 0
    TAIL_EDITED = 1
    HEAD_EDITED = 2
    HEAD_EDITED2 = 3
    TAIL_EDITED2 = 4
    BOTH_EDITED = 5
    TAIL_LOCKED = 6
    HEAD_LOCKED = 7
    BOTH_LOCKED = 8

    MOVE_BOTH = 0
    MOVE_TAIL = 1
    MOVE_HEAD = 2

    TAIL = 0
    HEAD = 1

get = lambda a, b :float(a.get(b))
set = lambda a, b, c :a.set(b, str(c))

def getHdg(g, num):
  h = get(g, 'hdg')%(2*math.pi)
  poly = g.find('paramPoly3')
  if poly != None:
    bU, cU, dU = get(poly, 'bU'), get(poly, 'cU'), get(poly, 'dU')
    bV, cV, dV = get(poly, 'bV'), get(poly, 'cV'), get(poly, 'dV')
    if num == 0:
      h = (h+math.atan(bV/bU))%(2*math.pi)
    else:
      h = (h+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*math.pi)
  return h

def hdgToDxDy(h):
  dx, dy = 0, 0
  match h:
    case h if h == 0:        dx, dy =  1, 0
    case h if h == math.pi: dx, dy = -1, 0
    case h if h >  math.pi: dx, dy = -1/math.tan(h), -1
    case h if h <  math.pi: dx, dy =  1/math.tan(h), 1
  return dx, dy
