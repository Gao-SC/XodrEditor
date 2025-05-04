from utils.path import scriptPath

class scriptReader:
  def __init__(self):
    pass

  def read(self, name):
    try:
      with open(scriptPath+name+".odrScript", 'r') as file:
        return file.readlines()
    
    except FileNotFoundError:
      print("Error: File not found!")
      return False

script = scriptReader()