import math
import numpy
from scipy.integrate import quad

## 以下为定义的常量
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

  MOVE_TAIL = 0
  MOVE_HEAD = 1
  MOVE_BOTH = 2

  TAIL = 0
  HEAD = 1

## 以下为通用的工具类 
getData = lambda a, b :float(a.get(b))
setData = lambda a, b, c :a.set(b, str(c))