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
        link = road.get('link')
        pre = link.get('predecessor')
        suc = link.get('successor')
        if pre != None:
            direction = pre.get("contactPoint") == "end"
            preId = int(pre.get("elementId"))
            if pre.get("elementType") == "road":
                vars.connectSets[id].append([preId, cons.TAIL, direction])
            else:
                jSets[id][0] = int(pre.get("elementId"))
        if suc != None:
            direction = pre.get("contactPoint") == "end"
            sucId = int(suc.get("elementId"))
            if suc.get("elementType") == "road":
                vars.connectSets[id].append([sucId, cons.TAIL, direction])
            else:
                jSets[id][1] = int(suc.get("elementId"))
        
    for junction in vars.root.iter('junction'):
        jId = int(junction.get('id'))
        for connection in junction.iter('connection'):
            direction = pre.get("contactPoint") == "end"
            incId = int(connection.get('incomingRoad'  ))
            conId = int(connection.get('connectingRoad'))
            point = jSets[incId][1] == jId
            vars.connectSets[incId].append([conId, point, direction])

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
                    if len(command) <= 2:
                        print('Need more params.')
                    elif len(command) == 3:
                        changeRoadWidth(command[1], float(command[2]))
                    elif len(command) == 4:
                        changeRoadWidth(command[1], float(command[2]), command[3])
                    elif len(command) == 5:
                        changeRoadWidth(command[1], float(command[2]), command[3], bool(command[4]))
                    elif len(command) == 6:
                        print("TBD")
                    else:
                        print("Too much params!")
                case "slope":
                    if len(command) <= 2:
                        print('Need more params.')
                    elif len(command) == 3:
                        changeRoadSlope(command[1], float(command[2]))
                    elif len(command) == 4:
                        changeRoadSlope(command[1], float(command[2]), command[3])
                    elif len(command) == 5:
                        changeRoadSlope(command[1], float(command[2]), command[3], int(command[4]))
                    else:
                        print("Too much params!")
                        
                
    

    

