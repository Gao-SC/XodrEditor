import Xodr.xodrParser as Xparser
import Json.jsonParser as JParser
import llm.llm as llm
import utils.path as path
from utils.random import getRandomValue
from utils.pltShow import plt
from utils.constants import *

from editor.editorCurve import editorCurve
from editor.editorFit import editorFit
from editor.editorSlope import editorSlope
from editor.editorWidth import editorWidth
from test import *

import random

if __name__ == '__main__':
    LLMon = False
    commandList = []

    
    editorC = editorCurve()
    editorF = editorFit()
    editorS = editorSlope()
    editorW = editorWidth()

    plt.ion()
    while True:
        if commandList != []:
            fileName = commandList[0]
            commandList.pop(0)
        fileName = input("Enter the xodr file path here: ")
        if fileName == 'exit':
            plt.ioff()
            break
        if fileName == 'llm':
            commandList = llm.translate()
            continue

        if Xparser.openXodr(fileName) == False:
            continue
        if JParser.readJson(fileName) == False:
            continue
        path.editSaveName(fileName)

        while True:
            command = None
            if commandList != []:
                command = commandList[0]
                commandList.pop(0)
            else:
                command = input().split()
                if command == []:
                    continue

            match command[0]:
                case "save":
                    Xparser.writeXodr()
                    JParser.writeJson()
                case "close":
                    break
                case "undo":
                    Xparser.redoData()
                    JParser.redoData()
                case "saveName":
                    path.saveName = command[1]
                case "llm":
                    LLMon = True

                case "width":
                    Xparser.pushNewData()
                    JParser.pushNewData()
                    id = "random"
                    v = 0
                    s = 0
                    ms = 0
                    sh = False
                    li = []
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = getRandomValue(param[1])
                            case 's': s = int(param[1])
                            case 'ms': ms = int(param[1])
                            case 'sh': sh = int(param[1])
                            case 'li':
                                lanes = param[1].split(',')
                                for lane in lanes:
                                    li.append(lane)
                            case _: print("Illegal parameter!")

                    editorW.edit(id=id, value=v, smooth=s, maxStep=ms, sameHdg=sh, laneIds=li)

                case "slope":
                    Xparser.pushNewData()
                    JParser.pushNewData()
                    id = "random"
                    v = 0
                    m = 'add'
                    mv = cons.MOVE_BOTH
                    ms = 0
                    sh = False
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'v': v = getRandomValue(param[1])
                            case 'm': m = param[1]
                            case 'mv': mv = int(param[1])
                            case 'ms': ms = int(param[1])
                            case 'sh': sh = int(param[1])
                            case _: print("Illegal parameter!")

                    editorS.edit(id=id, value=v, mode=m, move=mv, maxStep=ms, sameHdg=sh)

                case "fit":
                    Xparser.pushNewData()
                    JParser.pushNewData()
                    id = "random"
                    md = 0.01
                    st = 1.0
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'md': md = getRandomValue(param[1])
                            case 'st': st = getRandomValue(param[1])
                            case _: print("Illegal parameter!")

                    editorF.edit(id=id, md=md, st=st)

                case "curve":
                    Xparser.pushNewData()
                    JParser.pushNewData()
                    id = "random"
                    x0, y0, h0, v0 = 0, 0, 0, 0
                    x1, y1, h1, v1 = 0, 0, 0, 0
                    gi = "random"
                    for i in range(1, len(command)):
                        param = command[i].split('=')
                        match param[0]:
                            case 'id': id = param[1]
                            case 'x0': x0 = getRandomValue(param[1])
                            case 'y0': y0 = getRandomValue(param[1])
                            case 'h0': h0 = getRandomValue(param[1])
                            case 'v0': v0 = getRandomValue(param[1])
                            case 'x1': x1 = getRandomValue(param[1])
                            case 'y1': y1 = getRandomValue(param[1])
                            case 'h1': h1 = getRandomValue(param[1])
                            case 'v1': v1 = getRandomValue(param[1])
                            case 'gi': 
                                if param[1] != 'random':  gi = int(param[1])
                            case _: print("Illegal parameter!")
                    
                    if gi == "random":
                        id, lenGs = editorC.edit(id=id, md=0.01, st=1.0)
                        gi = random.randrange(0, lenGs)
                    editorC.edit(id=id, x0=x0, y0=y0, h0=h0, v0=v0, x1=x1, y1=y1, h1=h1, v1=v1, gi=gi)