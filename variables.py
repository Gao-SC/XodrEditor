import numpy


tree = None
def updateTree(new_val):
    global tree
    tree = new_val

root = None
def updateRoot(new_val):
    global root
    root = new_val

connectSets = [[] for _ in range(1000)]
edits = numpy.zeros(1000)



saveName = 'test1.xodr'
openPath = None