import numpy as np
import pygame
from helpers_fluidsim import *
from math import floor

# simulation constants
G = 50
FPS = 60
SIZE = 16
DAMP_FACTOR = 0.99


density = np.zeros((SIZE,SIZE))
density[5:11,5:11] = 1.0

velocity = np.zeros((SIZE, SIZE, 2), dtype=float)

# force = np.zeros((SIZE, SIZE, 2))

dt = 1 / FPS


# pygame initialization
pygame.init()
screen = pygame.display.set_mode((SIZE*20, SIZE*20))
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # velocity loop
    for i in range(SIZE):
        for j in range(SIZE):

            velocity[i,j][1] += G * dt
            if velocity[SIZE-1, j, 1] > 0:
                velocity[SIZE-1, j, 1] = 0
            # top row (optional)
            if velocity[0, j, 1] < 0:
                velocity[0, j, 1] = 0
    

    velocity *= DAMP_FACTOR


    # density loop
    new_density = np.zeros_like(density)
    for i in range(SIZE):
        for j in range(SIZE):
            source_x = j - velocity[i,j][0]*dt
            source_y = i - velocity[i,j][1]*dt

            source_x, source_y = reflect((source_x, source_y), SIZE)

            x0 = floor(source_x)
            x1 = min(x0+1, SIZE-1)
            y0 = floor(source_y)
            y1 = min(y0+1, SIZE-1)
            
            wx0, wx1, wy0, wy1 = target_weights(source_x, source_y, x0, y0)

            new_density[i,j] = (
                density[y0,x0]*wy0*wx0 +
                density[y0,x1]*wy0*wx1 +
                density[y1,x0]*wy1*wx0 +
                density[y1,x1]*wy1*wx1
            )

    density = new_density

    # render
    for i in range(SIZE):
        for j in range(SIZE):
            color = int(min(density[i, j] * 255, 255))
            pygame.draw.rect(screen, (0, 0, color), (j*20, i*20, 20, 20))


    pygame.display.flip()
    dt = clock.tick(FPS) / 1000
