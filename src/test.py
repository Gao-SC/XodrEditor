import os
import random
import math

dir_path = ".\\data\\OpenSCENARIO\\"
A_B = [-1, 1]

def generateRandomWidth():
  ms = random.randint(0,10)
  v = (1+random.random())*random.choice(A_B)
  command = f"width id=random_1_1 s=1 sh=1 ms={ms} v={v}\n"
  return command

def generateRandomSlope():
  x = [0, 1]
  ms = random.randint(0,10)
  v = (1+random.random())*random.choice(A_B)/20
  mv = random.choice(x)
  command = f"slope id=random_1_1 ms={ms} v={v} ms={ms} mv={mv}\n"
  return command

def generateRandomCurve():
  v0 = (1+random.random())*random.choice(A_B)/4
  v1 = (1+random.random())*random.choice(A_B)/4
  h0, h1 = 0, 0
  if random.random() > 0.95:
    h0 = (1+random.random())*random.choice(A_B)*math.pi/8
    h1 = (1+random.random())*random.choice(A_B)*math.pi/8
  command = f"curve id=random_1_1 v0={v0} v1={v1} h0={h0} h1={h1}\n"
  return command

filenames = []
with os.scandir(dir_path) as entries:
  for entry in entries:
    if entry.is_file() and entry.name.endswith("xodr"):
      name = entry.name[0:-5]
      filenames.append(name)
random.shuffle(filenames)

with open('.\\data\\script\\test.odrScript', 'w', encoding='utf-8') as f:
  size = len(filenames)
  for i in range(size):
    f.write(f"{filenames[i]}\n")
    if i < size/3:
      f.write(generateRandomWidth())
    elif i < size/3*2:
      f.write(generateRandomSlope())
    else:
      f.write(generateRandomCurve())
    f.write("close\n")

print("OK")