import xml.etree.ElementTree as ET
import variables as vars

from constants import *
from width import *
from elevation import *
from curvature import *

PATH = "D:\\Users\\cling\\Documents\\Homework\\Codes\\xodr_project\\test\\"

def write():
    vars.trees[-1].write(PATH+vars.saveName+".xodr", encoding="utf-8", xml_declaration=True)
    print('Already saved.')

def open(str):
    vars.clearTrees()
    vars.updateTrees(ET.parse(PATH+'OpenSCENARIO\\'+str+".xodr"))
    vars.updateRoot(vars.trees[-1].getroot())
    vars.connectSets = [[] for _ in range(1000)]
    vars.laneMap = {}

    jSets = [[-1, -1] for _ in range(1000)]
    for road in vars.root.iter('road'):
        id = road.get('id')
        link = road.find('link')
        pre = link.find('predecessor')
        suc = link.find('successor')
        if pre != None:
            direction = pre.get("contactPoint") == "end"
            preId = pre.get("elementId")

            if pre.get("elementType") == "road":
                if [int(preId), bool(cons.TAIL), direction] not in vars.connectSets[int(id)]:
                    vars.connectSets[int(id)].append([int(preId), bool(cons.TAIL), direction])
                if [int(id), direction, bool(cons.TAIL)] not in vars.connectSets[int(preId)]:
                    vars.connectSets[int(preId)].append([int(id), direction, bool(cons.TAIL)])
                for lane in road.findall('.//lane'):
                    laneId = lane.get('id')
                    Pre = lane.find('link').find('predecessor')
                    if Pre != None:
                        vars.laneMap[id+" "+preId+" "+laneId] = Pre.get('id')
                        vars.laneMap[preId+" "+id+" "+Pre.get('id')] = laneId
            else:
                jSets[int(id)][0] = int(pre.get("elementId"))

        if suc != None:
            direction = suc.get("contactPoint") == "end"
            sucId = suc.get("elementId")
            if suc.get("elementType") == "road":
                if [int(sucId), bool(cons.HEAD), direction] not in vars.connectSets[int(id)]:
                    vars.connectSets[int(id)].append([int(sucId), bool(cons.HEAD), direction])
                if [int(id), direction, bool(cons.HEAD)] not in vars.connectSets[int(sucId)]:
                    vars.connectSets[int(sucId)].append([int(id), direction, bool(cons.HEAD)])
                for lane in road.findall('.//lane'):
                    laneId = lane.get('id')
                    Suc = lane.find('link').find('successor')
                    if Suc != None:
                        vars.laneMap[id+" "+sucId+" "+laneId] = Suc.get('id')
                        vars.laneMap[sucId+" "+id+" "+Suc.get('id')] = laneId
            else:
                jSets[int(id)][1] = int(suc.get("elementId"))
        
    for junction in vars.root.iter('junction'):
        jId = int(junction.get('id'))
        for connection in junction.iter('connection'):
            direction = connection.get("contactPoint") == "end"
            incId = connection.get('incomingRoad'  )
            conId = connection.get('connectingRoad')
            point = jSets[int(incId)][1] == jId
            incLid = connection.find('laneLink').get('from')
            conLid = connection.find('laneLink').get('to'  )
            vars.laneMap[incId+" "+conId+" "+incLid] = conLid
            if [int(conId), point, direction] not in vars.connectSets[int(incId)]:
                vars.connectSets[int(incId)].append([int(conId), point, direction])

def pushNewTree():
    vars.updateTrees(vars.trees[-1])
    vars.updateRoot(vars.trees[-1].getroot())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while True:
        openPath = input("Enter the xodr file path here: ")
        if openPath == 'exit':
            break
        open(openPath)

        while True:
            command = input().split()
            match command[0]:
                case "save":
                    write()
                case "close":
                    write()
                    break
                case "undo":
                    vars.redoTrees()
                case "saveName":
                    vars.saveName = command[1]

                case "width":
                    pushNewTree()
                    id = None
                    v = None
                    m = 'add'
                    s = 0
                    ms = 0
                    sh = False
                    li = []
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 'm': m = param[1]
                            case 's': s = int(param[1])
                            case 'ms': ms = int(param[1])
                            case 'sh': sh = int(param[1])
                            case 'li':
                                lanes = param[1].split(',')
                                for lane in lanes:
                                    li.append(int(lane))
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadsWidth(id=id, value=v, mode=m, smooth=s, maxStep=ms, sameHdg=sh, laneIds=li)

                case "slope":
                    pushNewTree()
                    id = None
                    v = None
                    m = 'add'
                    mv = cons.MOVE_BOTH
                    s = 0
                    sh = False
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 'm': m = param[1]
                            case 'mv': mv = int(param[1])
                            case 's': s = int(param[1])
                            case 'sh': sh = int(param[1])
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadsSlope(id=id, value=v, mode=m, move=mv, maxStep=s, sameHdg=sh)

                case "curve":
                    pushNewTree()
                    id = None
                    v0 = None
                    v1 = None
                    h0 = 0
                    h1 = 0
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v0': v0 = float(param[1])
                            case 'v1': v1 = float(param[1])
                            case 'h0': h0 = float(param[1])
                            case 'h1': h1 = float(param[1])
                            case _: print("Illegal parameter!")

                    if id == None or v0 == None or v1 == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadArc(id=id, v0=v0, v1=v1, h0=h0, h1=h1)
            
                    

            