from datetime import datetime

logPath = ".\\log\\"

class Logger():
	def __init__(self):
		self.logPath = ".\\log\\"
		self.timeStamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 

	def write(self, command):
		try:
			with open(logPath+self.timeStamp+".log", 'a') as file:
				timeStamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
				file.write(timeStamp+":					"+command+"\n")
				return True
    
		except FileNotFoundError:
			print("Error: File not found!")
			return False
		