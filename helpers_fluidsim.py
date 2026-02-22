import numpy as np

def target_weights(x, y, x0, y0):
    wx1 = x -x0
    wx0 = 1 - wx1

    wy1 = y - y0
    wy0 = 1 - wy1

    return wx0, wx1, wy0, wy1

def reflect(point, size):
    x, y = point

    if x < 0:
        x = -x
    elif x > size - 1:
        x = 2 * (size - 1) - x

    if y < 0:
        y = -y
    elif y > size - 1:
        y = 2 * (size - 1) - y
    
    return x, y

