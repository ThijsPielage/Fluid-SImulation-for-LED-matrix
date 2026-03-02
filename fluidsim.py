import numpy as np
import pygame
from math import floor, sin, cos
import random

# Simulation settings
G = 100
FPS = 30
SIZE = 16
DAMP_FACTOR = 0.95
UPSCALE = 3

# Color and Size settings
FLUID_COLOR = (0, 80, 255)
BACKGROUND_COLOR = (20, 20, 35)

TILT = 0.0
DT = 1 / FPS
SIM_SIZE = SIZE * UPSCALE
NUM_PARTICLES = SIM_SIZE * SIM_SIZE // 6
V_TERMINAL = SIM_SIZE
CELL_SIZE = 1000 // SIZE

class Particle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-2.0, 2.0)
        self.vy = 0.0


particles = []
for _ in range(NUM_PARTICLES):
    px = random.uniform(SIM_SIZE * 0.4, SIM_SIZE * 0.6)
    py = random.uniform(SIM_SIZE * 0.4, SIM_SIZE * 0.6)
    particles.append(Particle(px, py))


def build_grid(particles):
    grid = np.zeros((SIM_SIZE, SIM_SIZE), dtype=bool)
    for p in particles:
        ix = int(p.x)
        iy = int(p.y)
        if 0 <= ix < SIM_SIZE and 0 <= iy < SIM_SIZE:
            grid[iy, ix] = True
    return grid


def update_particles(particles, gx, gy, grid):
    def cell_free(cx, cy):
        if cx < 0 or cx >= SIM_SIZE or cy < 0 or cy >= SIM_SIZE:
            return False
        return not grid[cy, cx]

    def gravity_dirs(gx, gy):
        dirs = [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (-1, 1), (1, -1), (-1, -1)
        ]

        g_len = (gx*gx + gy*gy) ** 0.5
        if g_len < 1e-6:
            return [(0, 1)]

        ngx = gx / g_len
        ngy = gy / g_len

        # Sort directions by dot product with gravity
        dirs.sort(key=lambda d: d[0]*ngx + d[1]*ngy, reverse=True)

        return dirs
    
    dirs = gravity_dirs(gx, gy)

    for p in particles:
        p.vx += gx * DT
        p.vy += gy * DT

        ix = int(p.x)
        iy = int(p.y)

        moved = False
        
        for dx, dy in dirs:
            tx = ix + dx
            ty = iy + dy
            if cell_free(tx, ty):
                grid[iy, ix] = False
                p.x = float(tx)
                p.y = float(ty)
                p.vx *= DAMP_FACTOR
                p.vy *= DAMP_FACTOR
                grid[ty, tx] = True
                moved = True
                break

        # --- Fully blocked ---
        if not moved:
            p.vx *= 0.5
            p.vy *= 0.5
            p.x = float(max(0, min(SIM_SIZE - 1, ix)))
            p.y = float(max(0, min(SIM_SIZE - 1, iy)))


    return particles


def render(screen, grid):
    screen.fill(BACKGROUND_COLOR)

    for y in range(SIZE):
        for x in range(SIZE):

            count = 0

            # Examine UPSCALE×UPSCALE block
            for dy in range(UPSCALE):
                for dx in range(UPSCALE):
                    sy = y * UPSCALE + dy
                    sx = x * UPSCALE + dx
                    if grid[sy, sx]:
                        count += 1

            # Compute fill ratio (0.0 to 1.0)
            ratio = count / (UPSCALE * UPSCALE)

            # Map ratio to brightness (adjust 80→255)
            brightness = int(175 * ratio)  # 80 = base, 255 = max
            color = (0, 0, min(brightness*2, 255))

            rect = (
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE - 1,
                CELL_SIZE - 1
            )
            pygame.draw.rect(screen, color, rect)

    # --- Draw tilt vector ---
    center_x = SIZE * CELL_SIZE // 2
    center_y = SIZE * CELL_SIZE // 2

    # Vector length in pixels
    vector_len = SIZE * CELL_SIZE // 2

    # Compute end point from TILT angle
    end_x = int(center_x + sin(TILT) * vector_len)
    end_y = int(center_y + cos(TILT) * vector_len)  # negative because screen y grows downward

    pygame.draw.line(screen, (255, 50, 50), (center_x, center_y), (end_x, end_y), 3)


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
                    px = random.uniform(SIM_SIZE * 0.3, SIM_SIZE * 0.7)
                    py = random.uniform(0.5, 3.0)
                    particles.append(Particle(px, py))
            if event.key == pygame.K_SPACE:
                for _ in range(10):
                    px = random.uniform(SIM_SIZE * 0.3, SIM_SIZE * 0.7)
                    py = random.uniform(0.0, 1.0)
                    particles.append(Particle(px, py))

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_held = True
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_held = False

    keys = pygame.key.get_pressed()

    ROT_SPEED = 2.5  # radians per second

    if keys[pygame.K_LEFT]:
        TILT -= ROT_SPEED * DT
    if keys[pygame.K_RIGHT]:
        TILT += ROT_SPEED * DT

    if keys[pygame.K_UP]:
        TILT -= ROT_SPEED * DT * 3
    if keys[pygame.K_DOWN]:
        TILT += ROT_SPEED * DT * 3

    # Click/drag to pour particles
    if mouse_held:
        mx, my = pygame.mouse.get_pos()
        cell_x = mx // CELL_SIZE * UPSCALE
        cell_y = my // CELL_SIZE * UPSCALE
        if 0 <= cell_x < SIM_SIZE and 0 <= cell_y < SIM_SIZE:
            for _ in range(3):
                p = Particle(cell_x + random.uniform(-0.5, 0.5),
                             cell_y + random.uniform(-0.5, 0.5))
                particles.append(p)

    # Gravity vector from tilt angle
    gx = G * sin(TILT)
    gy = G * cos(TILT)
    grid = build_grid(particles)
    for _ in range(3):
        particles = update_particles(particles, gx, gy, grid)
    render(screen, grid)
    pygame.display.flip()
    DT = clock.tick(FPS) / 1000

pygame.quit()