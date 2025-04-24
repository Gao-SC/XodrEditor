import odrparser as odr
import detector as det
from constants import *
from width import *
from elevation import *
from curvature import *

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    plt.ion()
    while True:
        openPath = input("Enter the xodr file path here: ")
        if openPath == 'exit':
            plt.ioff()
            break
        if odr.openXodr(openPath) == False:
            continue
        det.readJson(openPath)

        test, command = False, None
        while True:
            if not test:
                command = input().split()
            else:
                test = False

            match command[0]:
                case "save":
                    odr.write()
                case "close":
                    odr.write()
                    break
                case "undo":
                    odr.redoTrees()
                case "saveName":
                    odr.saveName = command[1]
                case "test":
                    command = det.testModify()
                    if command[0] == "curve":
                        param = command[1].split('=')
                        gsize = initRoadArc(id=param[1], md=0.01, st=1.0)
                        gi = random.randint(0, gsize-1)
                        command.append(f"gi={gi}")
                    test = True

                case "width":
                    odr.pushNewTree()
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
                    odr.pushNewTree()
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
                    odr.pushNewTree()
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
                    odr.pushNewTree()
                    id = None
                    x0, y0, h0, v0 = 0, 0, 0, 0
                    x1, y1, h1, v1 = 0, 0, 0, 0
                    gi = 0
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'x0': x0 = float(param[1])
                            case 'y0': y0 = float(param[1])
                            case 'h0': h0 = float(param[1])
                            case 'v0': v0 = float(param[1])
                            case 'x1': x1 = float(param[1])
                            case 'y1': y1 = float(param[1])
                            case 'h1': h1 = float(param[1])
                            case 'v1': v1 = float(param[1])
                            case 'gi': gi = int(param[1])
                            case _: print("Illegal parameter!")

                    if id == None:
                        print("Illegal command! Required parameter missing.")
                        continue
                    editRoadArc(id=id, x0=x0, y0=y0, h0=h0, v0=v0, x1=x1, y1=y1, h1=h1, v1=v1, gi=gi)

                    

            