import copy
import numpy
from collections import deque


trees = deque()
def updateTrees(new_val):
    global trees
    trees.append(copy.deepcopy(new_val))
    if len(trees) > 256:
        trees.popleft()

def redoTrees():
    global trees
    if len(trees) > 1:
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