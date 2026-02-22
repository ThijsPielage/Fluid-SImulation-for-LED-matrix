import numpy as np
import pygame
from helpers_fluidsim import *
from math import floor

# simulation constants
G = 50
FPS = 60
SIZE = 16
DAMP_FACTOR = 0.99
ITER = 10


density = np.zeros((SIZE,SIZE))
density[5:11,5:11] = 1.0

velocity = np.zeros((SIZE,SIZE,2), dtype=float)
pressure = np.zeros((SIZE,SIZE), dtype=float)

DT = 1 / FPS


# pygame initialization
pygame.init()
screen = pygame.display.set_mode((SIZE*20, SIZE*20))
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # velocity loop
    new_velocity = np.zeros_like(velocity)
    for i in range(SIZE):
        for j in range(SIZE):

            src_x = j - velocity[i,j][0]*DT
            src_y = i - velocity[i,j][1]*DT

            src_x = max(0, min(src_x, SIZE-1-1e-6))
            src_y = max(0, min(src_y, SIZE-1-1e-6))

            for c in range(2):
                new_velocity[i,j,c] = bilinear_sample(velocity[:, :, c], 
                                                      src_x, src_y)
    
    velocity = new_velocity 

    # Apply gravity and damping
    velocity[:, :, 1] += G * DT
    velocity *= DAMP_FACTOR

    # Solid walls
    velocity[SIZE-1,:,1] = np.minimum(velocity[SIZE-1,:,1], 0)
    velocity[0,:,1] = np.maximum(velocity[0,:,1], 0)
    velocity[:,0,0] = np.maximum(velocity[:,0,0], 0)
    velocity[:,SIZE-1,0] = np.minimum(velocity[:,SIZE-1,0], 0)


    # Pressure projection
    div = np.zeros((SIZE, SIZE))
    for i in range(1, SIZE - 1):
        for j in range(1, SIZE - 1):
            div[i, j] = -0.5 * (velocity[i, j+1, 0] - velocity[i, j-1, 0] +  
                                velocity[i+1, j, 1] - velocity[i-1, j, 1])
            
    pressure.fill(0)
    for _ in range(ITER):
        for i in range(1, SIZE-1):
            for j in range(1, SIZE -1):
                pressure[i,j] = (div[i,j] + 
                                 pressure[i-1, j] + 
                                 pressure[i+1, j] + 
                                 pressure[i, j-1] + 
                                 pressure[i, j+1]) / 4
                
    for i in range(1,SIZE-1):
        for j in range(1,SIZE-1):
            velocity[i,j,0] -= 0.5 * (pressure[i,j+1] - pressure[i,j-1])
            velocity[i,j,1] -= 0.5 * (pressure[i+1,j] - pressure[i-1,j])


    # density loop
    new_density = np.zeros_like(density)
    for i in range(SIZE):
        for j in range(SIZE):
            src_x = j - velocity[i,j,0]*DT
            src_y = i - velocity[i,j,1]*DT
            src_x = clamp(src_x, 0, SIZE-1-1e-6)
            src_y = clamp(src_y, 0, SIZE-1-1e-6)
            new_density[i,j] = bilinear_sample(density, src_x, src_y)
    density = new_density

    # render
    for i in range(SIZE):
        for j in range(SIZE):
            color = int(min(density[i, j] * 255, 255))
            pygame.draw.rect(screen, (0, 0, color), (j*20, i*20, 20, 20))


    pygame.display.flip()
    DT = clock.tick(FPS) / 1000
