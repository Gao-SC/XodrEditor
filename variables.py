import numpy
from collections import deque


trees = deque()
def updateTrees(new_val):
    global trees
    trees.append(new_val)
    if trees.count() > 256:
        trees.popleft()

def redoTrees():
    global trees
    if trees.count() > 0:
        trees.pop()

def clearTrees():
    global trees
    trees.clear()

root = None
def updateRoot(new_val):
    global root
    root = new_val

connectSets = [[] for _ in range(1000)]
edits = numpy.zeros(1000)



saveName = 'test1.xodr'
openPath = None