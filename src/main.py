
import llm.llm as llm
import utils.path as path
from utils.random import *
from utils.constants import *

from Xodr.xodrParser import XParser
from Json.jsonParser import JParser
from editor.editorCurve import editorCurve
from editor.editorFit import editorFit
from editor.editorSlope import editorSlope
from editor.editorWidth import editorWidth

import matplotlib.pyplot as plt
from collections import defaultdict

if __name__ == '__main__':
	LLMon = False
	fileName, commandList = None, []

	editorC = editorCurve()
	editorF = editorFit()
	editorS = editorSlope()
	editorW = editorWidth()

	plt.ion()
	while True:
		if commandList != []:
			fileName = commandList[0]
			commandList.pop(0)
		else:
			fileName = input("Enter the xodr file path here: ")

		if fileName == 'exit':
			plt.ioff()
			break
		if fileName == 'llm':
			commandList = llm.translate()
			continue

		if XParser.openXodr(fileName) == False:
			continue
		if JParser.readJson(fileName) == False:
			continue
		path.editSaveName(fileName)

		while True:
			command = None
			if commandList != []:
				command = commandList[0].split()
				commandList.pop(0)
			else:
				command = input().split()
				if command == []:
					continue

			id = "random"

			match command[0]:
				case "save":
					XParser.writeXodr()
					JParser.writeJson()
				case "close":
					break
				case "undo":
					XParser.redoData()
					JParser.undo()
				case "saveName":
					path.saveName = command[1]

				case "curve":
					XParser.pushNewData()
					JParser.pushNewData()
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
						id, lenGs = editorF.edit(id=id, md=0.01, st=1.0)
						gi = getRandomInt(lenGs)
					editorC.edit(id=id, x0=x0, y0=y0, h0=h0, v0=v0, x1=x1, y1=y1, h1=h1, v1=v1, gi=gi)

				case "fit":
					XParser.pushNewData()
					JParser.pushNewData()
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

				case "mark":
					XParser.pushNewData()
					JParser.pushNewData()
					li = "random"
					infoMap = defaultdict(dict)
					infoMap["sOffset"]	 	= "0"
					infoMap['type'] 			= "solid"
					infoMap['weight'] 		= "standard"
					infoMap['color'] 			= "standard"
					infoMap['laneChange'] = "none"

					for i in range(1, len(command)):
						param = command[i].split('=')
						match param[0]:
							case 'id': id = param[1]
							case 'li': li = param[1]
							case 'info': 
								xList = param[1].split(',')
								for x in xList:
									nameValue = x.split(':')
									infoMap[nameValue[0]] = nameValue[1]
								
				case "slope":
					XParser.pushNewData()
					JParser.pushNewData()
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

				case "width":
					XParser.pushNewData()
					JParser.pushNewData()
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