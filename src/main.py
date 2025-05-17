
import utils.path as path

from xodrs.xodrParser 			import XParser
from jsons.jsonParser 			import JParser
# from llm.llmXHXF 					import chater
from llm.llmMaxKB 					import chater
from script.script					import script
from handler.handlerCurve 	import handlerC
from handler.handlerFit 		import handlerF
from handler.handlerLane 		import handlerL
from handler.handlerObject 	import handlerO
from handler.handlerSignal	import handlerSi
from handler.handlerSlope 	import handlerSl
from handler.handlerWidth 	import handlerW
from logger.logger 					import Logger

import matplotlib.pyplot as plt

if __name__ == '__main__':
	logger = Logger()
	commandList = []
	plt.ion()

	while True:
		if commandList == []:
			mode = input("Please choose the mode of interaction.\nInput 'C' for command line interaction.\nInput 'S' for reading command script.\nInput 'L' for asking the large language model.\nInput 'E' to exit.\n")
			
			if mode == 'S':
				commandList = script.read()
				if commandList == []:
					print("ERROR: commandList is empty.")
					continue
			elif mode == 'L':
				commandList = chater.translate()
				if commandList == []:
					print("ERROR: commandList is empty.")
					continue
			elif mode == 'E':
				plt.ioff()
				break
			elif mode != 'C':
				print("WRONG MODE!")
				continue
		
		if commandList != []:
			fileName = commandList[0]
			commandList.pop(0)
		else:
			fileName = input("Enter the xodr file path here: ")

		if XParser.openXodr(fileName) == False:
			continue
		if JParser.readJson(fileName) == False:
			print("The json file is not exist.")

		path.editSaveName(fileName)
		logger.write(fileName)

		while True:
			if commandList != []:
				command = commandList[0].split()
				commandList.pop(0)
			else:
				command = input().split()
				if command == []:
					continue

			match command[0]:
				case "close":
					plt.close()
					break

				case "undo":
					XParser.undo()
					JParser.undo()

				case "savename":
					path.editSaveName(command[1])
					JParser.editSaveName(command[1])
					print("Save name is now: ", path.saveName)

				case "curve":
					logger.write(handlerC.handle(command))
					XParser.writeXodr()
					JParser.writeJson()

				case "fit":
					logger.write(handlerF.handle(command))
					XParser.writeXodr()
					JParser.writeJson()

				case "lane":
					logger.write(handlerL.handle(command))
					XParser.writeXodr()
					JParser.writeJson()
				
				case "object":
					logger.write(handlerO.handle(command))
					XParser.writeXodr()
					JParser.writeJson()

				case "signal":
					logger.write(handlerSi.handle(command))
					XParser.writeXodr()
					JParser.writeJson()
		
				case "slope":
					logger.write(handlerSl.handle(command))
					XParser.writeXodr()
					JParser.writeJson()

				case "width":
					logger.write(handlerW.handle(command))
					XParser.writeXodr()
					JParser.writeJson()

				case _:
					print("Illegal command!")
