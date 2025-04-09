import xml.etree.ElementTree as ET
import variables as vars
import sys
from constants import *
from width import *
from elevation import *
from curvature import *

PATH = "D:\\Users\\cling\\Documents\\Homework\\Codes\\xodr_project\\test\\"

def write():
    vars.trees[-1].write(PATH+vars.saveName+"_test.xodr", encoding="utf-8", xml_declaration=True)
    print('Already saved.')

def open(name):
    tree = None 
    try:
        tree = ET.parse(PATH+'selected_map\\'+name+".xodr")
    except Exception:
        print("File not found!")
        return False
    vars.saveName = name
    vars.clearTrees()
    vars.updateTrees(tree)
    vars.updateRoot(vars.trees[-1].getroot())
    updateData()
    return True

def updateData():
    vars.roadConnections = {}
    vars.laneConnections = {}
    jSets = {}
    for road in vars.root.iter('road'):
        id = road.get('id')
        gs = road.findall('.//geometry')

        h0 = get(gs[0], 'hdg')
        h1 = get(gs[-1],'hdg')
        poly1 = gs[-1].find('paramPoly3')
        if poly1 != None:
            bU, cU, dU = get(poly1, 'bU'), get(poly1, 'cU'), get(poly1, 'dU')
            bV, cV, dV = get(poly1, 'bV'), get(poly1, 'cV'), get(poly1, 'dV')
            h1 = (h1+math.atan((bV+2*cV+3*dV)/(bU+2*cU+3*dU)))%(2*numpy.pi)
        vars.hdgs[id] = []
        vars.hdgs[id].append(h0)
        vars.hdgs[id].append(h1)

        vars.roadConnections[id] = [[], []]
        vars.roadBackup[id] = cons.NOT_EDITED
        vars.laneConnections[id] = {}
        vars.laneBackup[id] = {}
        jSets[id] = [-1, -1]
        for lane in road.findall('.//lane'):
            lid = lane.get('id')
            if lid != '0':
                vars.laneBackup[id][lid] = cons.NOT_EDITED
                vars.laneConnections[id][lid] = [[], []]

    for road in vars.root.iter('road'):
        id = road.get('id')
        link = road.find('link')

        pre = link.find('predecessor')
        if pre != None:
            direction = int(pre.get("contactPoint") == "end")
            preId = pre.get("elementId")
            if pre.get("elementType") == "road":
                if [preId, direction] not in vars.roadConnections[id][cons.TAIL]:
                    vars.roadConnections[id][cons.TAIL].append([preId, direction])
                if [id, cons.TAIL] not in vars.roadConnections[preId][direction]:
                    vars.roadConnections[preId][direction].append([id, cons.TAIL])
                for lane in road.findall('.//lane'):
                    lid = lane.get('id')
                    Pre = lane.find('link').find('predecessor')
                    if Pre != None:
                        preLid = Pre.get('id')
                        if [preId, preLid, direction] not in vars.laneConnections[id][lid][cons.TAIL]:
                            vars.laneConnections[id][lid][cons.TAIL].append([preId, preLid, direction])
                        if [id, lid, cons.TAIL] not in vars.laneConnections[preId][preLid][direction]:    
                            vars.laneConnections[preId][preLid][direction].append([id, lid, cons.TAIL])
            else:
                jSets[id][0] = pre.get("elementId")

        suc = link.find('successor')
        if suc != None:
            direction = int(suc.get("contactPoint") == "end")
            sucId = suc.get("elementId")
            if suc.get("elementType") == "road":
                if [sucId, direction] not in vars.roadConnections[id][cons.HEAD]:
                    vars.roadConnections[id][cons.HEAD].append([sucId, direction])
                if [id, cons.HEAD] not in vars.roadConnections[sucId][direction]:
                    vars.roadConnections[sucId][direction].append([id, cons.HEAD])
                for lane in road.findall('.//lane'):
                    lid = lane.get('id')
                    Suc = lane.find('link').find('successor')
                    if Suc != None:
                        sucLid = Suc.get('id')
                        if [sucId, sucLid, direction] not in vars.laneConnections[id][lid][cons.HEAD]:
                            vars.laneConnections[id][lid][cons.HEAD].append([sucId, sucLid, direction])
                        if [id, lid, cons.HEAD] not in vars.laneConnections[sucId][sucLid][direction]:    
                            vars.laneConnections[sucId][sucLid][direction].append([id, lid, cons.HEAD])
            else:
                jSets[id][1] = suc.get("elementId")
        
    for junction in vars.root.iter('junction'):
        jId = junction.get('id')
        for connection in junction.iter('connection'):
            direction = int(connection.get("contactPoint") == "end")
            incId = connection.get('incomingRoad'  )
            conId = connection.get('connectingRoad')
            point = int(jSets[incId][1] == jId)
            incLid = connection.find('laneLink').get('from')
            conLid = connection.find('laneLink').get('to'  )
            if [conId, conLid, direction] not in vars.laneConnections[incId][incLid][point]:
                vars.laneConnections[incId][incLid][point].append([conId, conLid, direction])
            if [conId, direction] not in vars.roadConnections[incId][point]:
                vars.roadConnections[incId][point].append([conId, direction])

def pushNewTree():
    vars.updateTrees(vars.trees[-1])
    vars.updateRoot(vars.trees[-1].getroot())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    plt.ion()
    while True:
        openPath = input("Enter the xodr file path here: ")
        if openPath == 'exit':
            plt.ioff()
            break
        if open(openPath) == False:
            continue

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
                    s = 0
                    ms = 0
                    sh = False
                    li = []
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 's': s = int(param[1])
                            case 'ms': ms = int(param[1])
                            case 'sh': sh = int(param[1])
                            case 'li':
                                lanes = param[1].split(',')
                                for lane in lanes:
                                    li.append(lane)
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    editRoadWidth(id=id, value=v, smooth=s, maxStep=ms, sameHdg=sh, laneIds=li)

                case "slope":
                    pushNewTree()
                    id = None
                    v = None
                    m = 'add'
                    mv = cons.MOVE_BOTH
                    ms = 0
                    sh = False
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = float(param[1])
                            case 'm': m = param[1]
                            case 'mv': mv = int(param[1])
                            case 'ms': ms = int(param[1])
                            case 'sh': sh = int(param[1])
                            case _: print("Illegal parameter!")

                    if id == None or v == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    editRoadSlope(id=id, value=v, mode=m, move=mv, maxStep=ms, sameHdg=sh)

                case "fit":
                    pushNewTree()
                    id = None
                    md = 0.01
                    st = 1.0
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'md': md = float(param[1])
                            case 'st': st = float(param[1])
                            case _: print("Illegal parameter!")

                    if id == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    initRoadArc(id=id, md=md, st=st)

                case "curve":
                    pushNewTree()
                    id = None
                    v0 = 0
                    v1 = 0
                    h0 = 0
                    h1 = 0
                    gi = 0
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v0': v0 = float(param[1])
                            case 'v1': v1 = float(param[1])
                            case 'h0': h0 = float(param[1])
                            case 'h1': h1 = float(param[1])
                            case 'gi': gi = int(param[1])
                            case _: print("Illegal parameter!")

                    if id == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    editRoadArc(id=id, v0=v0, v1=v1, h0=h0, h1=h1, gi=gi)
            
                    

            