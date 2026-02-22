import numpy as np
from math import floor

def bilinear_sample(field, x, y):
    size = len(field)
    x0 = int(floor(x))
    y0 = int(floor(y))
    x1 = min(x0+1, size-1)
    y1 = min(y0+1, size-1)
    wx1 = x - x0
    wx0 = 1 - wx1
    wy1 = y - y0
    wy0 = 1 - wy1
    return (
        field[y0,x0]*wy0*wx0 +
        field[y0,x1]*wy0*wx1 +
        field[y1,x0]*wy1*wx0 +
        field[y1,x1]*wy1*wx1
    )

def clamp(v, minv, maxv):
    return np.maximum(minv, np.minimum(v, maxv))

