from datetime import datetime
import time

logPath = ".\\log\\"

class Logger():
	def __init__(self):
		self.logPath = ".\\log\\"
		self.timeStamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		self.lastTime = None

	def countTime(self):
		self.lastTime = time.perf_counter()

	def write(self, command):
		try:
			with open(logPath+self.timeStamp+".log", 'a') as file:
				timeStamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
				nowTime = time.perf_counter()
				exeTime = nowTime-self.lastTime
				file.write(timeStamp+"		"+str(exeTime).rjust(32, ' ')+":		"+command+"\n")
				return True
    
		except FileNotFoundError:
			print("Error: File not found!")
			return False
		