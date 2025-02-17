import xml.etree.ElementTree as ET
import variables
from constants import *

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