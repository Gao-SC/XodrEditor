from jsons.jsonParser import JParser
from utils.lambdas import *

class jsonDataGetter:
  def __init__(self):
    pass

  def getOrd(self, carInfo):
    carId = carInfo["carId"]
    ordId = carInfo["ordId"]
    car = JParser.data[-1]["agents"][carId]
    if car['uid'] != "":
      if ordId == 0:
        return car['transform']
      else:
        return car['destinationPoint']
    else:
      if ordId == 0:
        return car['transform']
      else:
        return car['waypoints'][ordId-1]

jDataGetter = jsonDataGetter()