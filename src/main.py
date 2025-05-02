
import utils.path as path

from xodrs.xodrParser 			import XParser
from jsons.jsonParser 			import JParser
from llm.llm 								import chater
from handler.handlerCurve 	import handlerC
from handler.handlerFit 		import handlerF
from handler.handlerLane 		import handlerL
from handler.handlerSignal	import handlerSi
from handler.handlerSlope 	import handlerSl
from handler.handlerWidth 	import handlerW
from log.logger 						import Logger

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
		logger = Logger()
		logger.write(fileName)

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
					logger.write(handlerC.handle(command))

				case "fit":
					logger.write(handlerF.handle(command))

				case "lane":
					logger.write(handlerL.handle(command))

				case "signal":
					logger.write(handlerSi.handle(command))
		
				case "slope":
					logger.write(handlerSl.handle(command))

				case "width":
					logger.write(handlerW.handle(command))

				case _:
					print("Illegal command!")
