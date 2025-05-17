from utils.path import scriptPath

class scriptReader:
  def __init__(self):
    pass

  def read(self):
    name = input("input the name of odrScript file: ")
    print(scriptPath+name+".odrScript")
    try:
      with open(scriptPath+name+".odrScript", 'r') as file:
        answer = file.readlines()
        for i in range(len(answer)):
          answer[i] = answer[i].rstrip()
        return answer
    
    except FileNotFoundError:
      print("Error: File not found!")
      return []

script = scriptReader()