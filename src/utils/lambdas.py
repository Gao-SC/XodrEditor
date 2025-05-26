import math

getData = lambda a, b :float(a.get(b))
setData = lambda a, b, c :a.set(b, str(c))

hdg2ang  = lambda h: (90-(h*180/math.pi))%360
hdg2ang2 = lambda h: -(h*180/math.pi)%360
ang2hdg  = lambda a: (math.pi/2-a*math.pi/180)%(math.pi*2)
ang2hdg2 = lambda a: (a*math.pi/180)%(math.pi*2)

def findMaxCubic(a, b, c, d, upperLimit):
  candidates = [0.0, float(upperLimit)]
  if d == 0:
    if c != 0:
      x_crit = -b / (2 * c)
      if 0 <= x_crit <= upperLimit:
        candidates.append(x_crit)
  else:
    discriminant = 4*c**2-12*d*b
    if discriminant >= 0:
      sqrt_disc = math.sqrt(discriminant)
      x1 = (-2*c+sqrt_disc) / (6*d)
      x2 = (-2*c-sqrt_disc) / (6*d)
      for x in [x1, x2]:
        if 0 <= x <= upperLimit:
          candidates.append(x)
  
  maxY = -math.inf
  for x in candidates:
    y = a+b*x+c*x**2+d*x**3
    if y > maxY:
      maxY = y
  return maxY