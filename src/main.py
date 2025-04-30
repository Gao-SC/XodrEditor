
import llm.llm as llm
import utils.path as path
from utils.random import *
from utils.constants import *

from Xodr.xodrParser import XParser
from Json.jsonParser import JParser

from command.handlerCurve 	import handlerC
from command.handlerFit 		import handlerF
from command.handlerMark 		import handlerM
from command.handlerSignal	import handlerSi
from command.handlerSlope 	import handlerSl
from command.handlerWidth 	import handlerW

import matplotlib.pyplot as plt

if __name__ == '__main__':
	LLMon = False
	fileName, commandList = None, []

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
					handlerC.handle(command)

				case "fit":
					handlerF.handle(command)

				case "mark":
					handlerM.handle(command)

				case "signal":
					handlerSi.handle(command)
		
				case "slope":
					handlerSl.handle(command)

				case "width":
					handlerW.handle(command)