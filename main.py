import xml.etree.ElementTree as ET
import variables as vars

from constants import *
from width import *
from elevation import *

def write():
    vars.tree.write("D:\\Users\\cling\\Documents\\Homework\\Codes\\xodr_project\\test\\"+vars.saveName, encoding="utf-8", xml_declaration=True)
    print('Already saved.')

def open(str):
    vars.updateTree(ET.parse("D:\\Users\\cling\\Documents\\Homework\\Codes\\xodr_project\\test\\"+str))
    vars.updateRoot(vars.tree.getroot())

    jSets = [[-1, -1] for _ in range(1000)]
    for road in vars.root.iter('road'):
        id = int(road.get('id'))
        link = road.find('link')
        pre = link.find('predecessor')
        suc = link.find('successor')
        if pre != None:
            direction = pre.get("contactPoint") == "end"
            preId = int(pre.get("elementId"))
            if pre.get("elementType") == "road":
                if [preId, bool(cons.TAIL), direction] not in vars.connectSets[id]:
                    vars.connectSets[id].append([preId, bool(cons.TAIL), direction])
                if [id, direction, bool(cons.TAIL)] not in vars.connectSets[preId]:
                    vars.connectSets[preId].append([id, direction, bool(cons.TAIL)])
            else:
                jSets[id][0] = int(pre.get("elementId"))
        if suc != None:
            direction = suc.get("contactPoint") == "end"
            sucId = int(suc.get("elementId"))
            if suc.get("elementType") == "road":
                if [sucId, bool(cons.HEAD), direction] not in vars.connectSets[id]:
                    vars.connectSets[id].append([sucId, bool(cons.HEAD), direction])
                if [id, direction, bool(cons.HEAD)] not in vars.connectSets[sucId]:
                    vars.connectSets[sucId].append([id, direction, bool(cons.HEAD)])
            else:
                jSets[id][1] = int(suc.get("elementId"))
        
    for junction in vars.root.iter('junction'):
        jId = int(junction.get('id'))
        for connection in junction.iter('connection'):
            direction = connection.get("contactPoint") == "end"
            incId = int(connection.get('incomingRoad'  ))
            conId = int(connection.get('connectingRoad'))
            point = jSets[incId][1] == jId
            if [conId, point, direction] not in vars.connectSets[incId]:
                vars.connectSets[incId].append([conId, point, direction])
    
'''    for i in range(len(vars.connectSets)):
        _ = vars.connectSets[i]
        if _ != []:
            print(i)
            print(_)'''

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

                case "width":
                    id = None
                    v = None
                    m = 'add'
                    s = False
                    i = []
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 'm': m = param[1]
                            case 's': s = bool(param[1])
                            case 'i': i = param[1] #TODO
                            case _: print("Illegal parameter!")
                            
                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadWidth(id=id, value=v, mode=m, smooth=s, infos=i)

                case "widths":
                    id = None
                    v = None
                    m = 'add'
                    s = 0
                    sh = False
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 'm': m = param[1]
                            case 's': s = int(param[1])
                            case 'sh': sh = bool(param[1])
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadsWidth(id=id, value=v, mode=m, maxStep=s, sameHdg=sh)

                case "slope":
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
                            case 'sh': sh = bool(param[1])
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    changeRoadsSlope(id=id, value=v, mode=m, move=mv, maxStep=s, sameHdg=sh)
