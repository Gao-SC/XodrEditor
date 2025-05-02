from utils.path import logPath
from datetime import datetime

class Logger():
	def __init__(self):
		self.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

	def write(self, command):
		with open(logPath+self.timeStamp+".log", 'a') as file:
			timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			file.write(timeStamp, ": ", command, "\n")

	# TODO
		