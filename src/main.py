
import utils.path as path

from Xodr.xodrParser 				import XParser
from Json.jsonParser 				import JParser
from llm.llm 								import chater
from command.handlerCurve 	import handlerC
from command.handlerFit 		import handlerF
from command.handlerLane 		import handlerL
from command.handlerSignal	import handlerSi
from command.handlerSlope 	import handlerSl
from command.handlerWidth 	import handlerW

import matplotlib.pyplot as plt

if __name__ == '__main__':
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
			commandList = chater.translate()
			continue

		if XParser.openXodr(fileName) == False:
			continue
		if JParser.readJson(fileName) == False:
			print("The json file is not exist.")
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

			match command[0]:
				case "save":
					XParser.writeXodr()
					JParser.writeJson()

				case "close":
					plt.close()
					break

				case "undo":
					XParser.redoData()
					JParser.undo()

				case "savename":
					path.editSaveName(command[1])
					print("Save name is now: ", path.saveName)

				case "curve":
					handlerC.handle(command)

				case "fit":
					handlerF.handle(command)

				case "mark":
					handlerL.handle(command)

				case "signal":
					handlerSi.handle(command)
		
				case "slope":
					handlerSl.handle(command)

				case "width":
					handlerW.handle(command)

				case _:
					print("Illegal command!")
