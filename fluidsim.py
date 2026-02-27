import numpy as np
import pygame
from math import floor, sin, cos
import random

# Simulation settings
G = 10
FPS = 30
SIZE = 16
DAMP_FACTOR = 0.6
NUM_PARTICLES = 40

# Color and Size settings
FLUID_COLOR = (0, 80, 255)
BACKGROUND_COLOR = (20, 20, 35)
CELL_SIZE = 10 # pixels per cell

# Global variables
TILT = 0.0
DT = 1 / FPS

class Particle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-2.0, 2.0)
        self.vy = 0.0


particles = []
for _ in range(NUM_PARTICLES):
    px = random.uniform(SIZE * 0.4, SIZE * 0.6)
    py = random.uniform(SIZE * 0.4, SIZE * 0.6)
    particles.append(Particle(px, py))


def build_grid(particles):
    grid = np.zeros((SIZE, SIZE), dtype=bool)
    for p in particles:
        ix = int(p.x)
        iy = int(p.y)
        if 0 <= ix < SIZE and 0 <= iy < SIZE:
            grid[iy, ix] = True
    return grid



def clamp(v, minv, maxv):
    return min(max(v, minv), maxv)

def update_particles(particles, gx, gy):
    random.shuffle(particles)
    grid = build_grid(particles)

    # Find direction of gravity
    if abs(gy) >= abs(gx):
        down_x, down_y = 0, (1 if gy > 0 else -1)
        side_x, side_y = 1, 0
    else:
        down_x, down_y = (1 if gx > 0 else -1), 0
        side_x, side_y = 0, (1 if gy >= 0 else -1)


    def cell_free(cx, cy):
        if cx < 0 or cx >= SIZE or cy < 0 or cy >= SIZE:
            return False
        return not grid[cy, cx]


    for p in particles:
        # Calculate new velocity
        p.vx += gx * DT
        p.vy += gy * DT

        # Clamp speed to terminal velocity
        p.vx = clamp(p.vx, -3.0, 3.0)
        p.vy = clamp(p.vy, -3.0, 3.0)

        # Store the current cell-location
        ix = int(p.x)
        iy = int(p.y)

        p_down = p.vx * down_x + p.vy * side_y
        p_side = p.vx * side_x + p.vy * down_y

        # Find candidate position
        nx = int(p.x + p.vx * DT)
        ny = int(p.y + p.vy * DT)
        
        moved = False

        if cell_free(nx, ny):
            grid[iy, ix] = False
            p.x = nx
            p.y = ny

            if int(p.x) <= 0:
                p.x = 0.5
                p.vx = abs(p.vx) * DAMP_FACTOR
            if int(p.x) >= SIZE - 1:
                p.x = SIZE - 1.5
                p.vx = -abs(p.vx) * DAMP_FACTOR
            if int(p.y) <= 0:
                p.y = 0.5
                p.vy = abs(p.vy) * DAMP_FACTOR
            if int(p.y) >= SIZE - 1:
                p.y = SIZE - 1.5
                p.vy = -abs(p.vy) * DAMP_FACTOR
            grid[int(p.y), int(p.x)] = True
            moved = True

        # Blocked — try falling diagonally
        if not moved:
            dirs = [-1, 1] if random.random() < 0.5 else [1, -1]
            if p_side > 0.1:  dirs = [1, -1]
            elif p_side < -0.1: dirs = [-1, 1]

            for d in dirs:
                diag_x = ix + down_x + d * side_x
                diag_y = iy + down_y + d * side_y
                if cell_free(diag_x, diag_y):
                    grid[iy, ix] = False
                    p.x = float(diag_x)
                    p.y = float(diag_y)
                    # Convert downward momentum into sideways
                    p.vx = down_x * p_down * DAMP_FACTOR + \
                        d * side_x * abs(p_down) * 0.4
                    p.vy = down_y * p_down * DAMP_FACTOR + \
                        d * side_y * abs(p_down) * 0.4
                    grid[diag_y, diag_x] = True
                    moved = True
                    break

        # --- Try sliding sideways (pressure spreading) ---
        if not moved:
            dirs = [-1, 1] if random.random() < 0.5 else [1, -1]
            if p_side > 0.3:  dirs = [1, -1]
            elif p_side < -0.3: dirs = [-1, 1]

            for d in dirs:
                slide_x = ix + d * side_x
                slide_y = iy + d * side_y
                if cell_free(slide_x, slide_y):
                    grid[iy, ix] = False
                    p.x = float(slide_x)
                    p.y = float(slide_y)
                    p.vx = d * side_x * 0.8
                    p.vy = d * side_y * 0.8
                    grid[slide_y, slide_x] = True
                    moved = True
                    break

        # --- Fully blocked: come to rest ---
        if not moved:
            p.vx *= 0.5
            p.vy *= 0.5
            p.x = float(max(0, min(SIZE - 1, ix)))
            p.y = float(max(0, min(SIZE - 1, iy)))

    return particles


def render(screen, particles):
    grid = build_grid(particles)
    for y in range(SIZE):
        for x in range(SIZE):
            rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
            color = FLUID_COLOR if grid[y, x] else BACKGROUND_COLOR
            pygame.draw.rect(screen, color, rect)






pygame.init()
screen = pygame.display.set_mode((SIZE * CELL_SIZE, SIZE * CELL_SIZE + 24))
pygame.display.set_caption("LED Fluid Sim — Cellular Automaton")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 11)

running = True
mouse_held = False


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_r:
                particles = []
                for _ in range(NUM_PARTICLES):
                    px = random.uniform(SIZE * 0.3, SIZE * 0.7)
                    py = random.uniform(0.5, 3.0)
                    particles.append(Particle(px, py))
            if event.key == pygame.K_SPACE:
                for _ in range(10):
                    px = random.uniform(SIZE * 0.3, SIZE * 0.7)
                    py = random.uniform(0.0, 1.0)
                    particles.append(Particle(px, py))
            # Arrow keys to test tilt
            if event.key == pygame.K_LEFT:  TILT -= 0.1
            if event.key == pygame.K_RIGHT: TILT += 0.1

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_held = True
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_held = False

    # Click/drag to pour particles
    if mouse_held:
        mx, my = pygame.mouse.get_pos()
        cell_x = mx // CELL_SIZE
        cell_y = my // CELL_SIZE
        if 0 <= cell_x < SIZE and 0 <= cell_y < SIZE:
            for _ in range(3):
                p = Particle(cell_x + random.uniform(-0.5, 0.5),
                             cell_y + random.uniform(-0.5, 0.5))
                particles.append(p)

    # Gravity vector from tilt angle
    gx = G * sin(TILT)
    gy = G * cos(TILT)

    particles = update_particles(particles, gx, gy)
    render(screen, particles)
    pygame.display.flip()
    DT = clock.tick(FPS) / 1000

pygame.quit()