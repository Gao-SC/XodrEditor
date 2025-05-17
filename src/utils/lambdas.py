import math

getData = lambda a, b :float(a.get(b))
setData = lambda a, b, c :a.set(b, str(c))

hdg2ang = lambda h: (270-(h*180/math.pi))%360
ang2hdg = lambda a: (math.pi/2-a*math.pi/180)%(math.pi*2)