import math
import numpy
from scipy.integrate import quad
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

PATH = "D:\\Users\\cling\\Documents\\Homework\\Codes\\xodr_project\\test\\"

getData = lambda a, b :float(a.get(b))
setData = lambda a, b, c :a.set(b, str(c))

def getLength(param, t):
  bU, cU, dU, bV, cV, dV = param
  def integrand(p):
    du = bU+2*cU*p+3*dU*p**2
    dv = bV+2*cV*p+3*dV*p**2
    return numpy.sqrt(du**2+dv**2)
  length, _ = quad(integrand, 0, t)
  return length

colors = [
  '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
  '#42d4f4', '#f032e6', '#fabed4', '#469990', '#dcbeff', 
  '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', 
  '#a9a9a9', '#ffffff', '#000000'
]

import matplotlib.pyplot as plt
import random
def random_color():
    return (random.random(), random.random(), random.random())
def showCurve(params):
  plt.clf()
  t = numpy.linspace(0, 1, 10000)
  for i in range(len(params)):
    print(params[i])
    bU, cU, dU, bV, cV, dV, aU, aV = params[i]
    u = aU+bU*t+cU*t**2+dU*t**3
    v = aV+bV*t+cV*t**2+dV*t**3
    plt.plot(u, v, color=colors[i])
    plt.axis('equal')
  plt.show()