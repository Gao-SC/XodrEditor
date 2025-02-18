class cons:
    NOT_EDITED = 0
    TAIL_EDITED = 1
    HEAD_EDITED = 2
    HEAD_EDITED2 = 3
    TAIL_EDITED2 = 4
    BOTH_EDITED = 5
    TAIL_LOCKED = 6
    HEAD_LOCKED = 7
    BOTH_LOCKED = 8

    MOVE_BOTH = 0
    MOVE_TAIL = 1
    MOVE_HEAD = 2

    TAIL = False
    HEAD = True

get = lambda a, b :float(a.get(b))
set = lambda a, b, c :a.set(b, str(c))
