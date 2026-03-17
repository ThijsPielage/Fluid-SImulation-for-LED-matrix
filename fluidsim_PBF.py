import pygame
import random
from math import sin, cos

# Simulation settings
G = 60
FPS = 60
SIZE = 20

NUM_PARTICLES = 300

H = 1.5
REST_DENSITY = 8
PRESSURE_K = 0.002
ITERATIONS = 5

DAMP_FACTOR = 0.997
VISCOSITY = 0.05

CELL_SIZE = 1000 // SIZE

# Colors
BACKGROUND_COLOR = (20, 20, 35)
PARTICLE_COLOR = (50, 140, 255)

TILT = 0.0
DT = 1 / FPS


class Particle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.vx = 0.0
        self.vy = 0.0

        self.px = self.x
        self.py = self.y


particles = []
for _ in range(NUM_PARTICLES):
    px = random.uniform(SIZE * 0.2, SIZE * 0.8)
    py = random.uniform(SIZE * 0.2, SIZE * 0.8)
    particles.append(Particle(px, py))


def update_particles(particles, gx, gy):
    cell_size = H
    grid = {}


    # --- Apply forces + predict positions ---
    for p in particles:
        # gravity
        p.vx += gx * DT
        p.vy += gy * DT

        # predict positions
        p.px = p.x + p.vx * DT
        p.py = p.y + p.vy * DT

        # assign to grid
        cx = int(p.px // cell_size)
        cy = int(p.py // cell_size)
        if (cx, cy) not in grid:
            grid[(cx, cy)] = []
        grid[(cx, cy)].append(p)

    # --- SPH iterations ---
    for _ in range(ITERATIONS):
        densities = {}

        # --- density estimate (poly6 smoothing) ---
        for cell_particles in grid.values():
            for p in cell_particles:
                densities[p] = 0
                cx = int(p.px // cell_size)
                cy = int(p.py // cell_size)
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        neighbor_cell = (cx + ox, cy + oy)
                        if neighbor_cell not in grid:
                            continue
                        for q in grid[neighbor_cell]:
                            dx = p.px - q.px
                            dy = p.py - q.py
                            r2 = dx*dx + dy*dy
                            if r2 < H*H:
                                densities[p] += (H*H - r2)**3  # smoother density

        # --- pressure solve ---
        for cell_particles in grid.values():
            for p in cell_particles:
                rho = densities[p]
                if rho <= REST_DENSITY:
                    continue

                pressure = (rho - REST_DENSITY) * PRESSURE_K
                cx = int(p.px // cell_size)
                cy = int(p.py // cell_size)

                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        neighbor_cell = (cx + ox, cy + oy)
                        if neighbor_cell not in grid:
                            continue
                        for q in grid[neighbor_cell]:
                            if p == q:
                                continue
                            dx = p.px - q.px
                            dy = p.py - q.py
                            r2 = dx*dx + dy*dy
                            if r2 >= H*H or r2 == 0:
                                continue
                            dist = max(0.001, r2**0.5)
                            nx, ny = dx / dist, dy / dist
                            corr = pressure * (1 - dist / H)
                            p.px += nx * corr * 0.5
                            p.py += ny * corr * 0.5
                            q.px -= nx * corr * 0.5
                            q.py -= ny * corr * 0.5

                # --- clamp predicted positions inside container ---
                p.px = max(0.0, min(SIZE, p.px))
                p.py = max(0.0, min(SIZE, p.py))

    # --- integrate velocities and positions ---
    for p in particles:
        # velocity from predicted positions
        p.vx = (p.px - p.x) / DT
        p.vy = (p.py - p.y) / DT

        # damping
        p.vx *= DAMP_FACTOR
        p.vy *= DAMP_FACTOR

        # viscosity (optional smoothing)
        cx = int(p.px // cell_size)
        cy = int(p.py // cell_size)
        for ox in (-1,0,1):
            for oy in (-1,0,1):
                neighbor_cell = (cx + ox, cy + oy)
                if neighbor_cell not in grid:
                    continue
                for q in grid[neighbor_cell]:
                    if p == q:
                        continue
                    p.vx += (q.vx - p.vx) * VISCOSITY * DT
                    p.vy += (q.vy - p.vy) * VISCOSITY * DT

        # update positions
        p.x = p.px
        p.y = p.py

        # --- soft walls ---
        margin = H
        k_wall = 50
        if p.x < margin:
            p.vx += (margin - p.x) * k_wall * DT
        elif p.x > SIZE - margin:
            p.vx += (SIZE - margin - p.x) * k_wall * DT
        if p.y < margin:
            p.vy += (margin - p.y) * k_wall * DT
        elif p.y > SIZE - margin:
            p.vy += (SIZE - margin - p.y) * k_wall * DT

    return particles

def render(screen): 
    screen.fill(BACKGROUND_COLOR) 
    for p in particles: 
        px = int(p.x / SIZE * SIZE * CELL_SIZE)
        py = int(p.y / SIZE * SIZE * CELL_SIZE)

        pygame.draw.circle(screen, PARTICLE_COLOR, (px, py), 9) 
        # tilt vector
        cx = SIZE * CELL_SIZE // 2
        cy = SIZE * CELL_SIZE // 2
        length = SIZE * CELL_SIZE // 2

        ex = int(cx + sin(TILT) * length)
        ey = int(cy + cos(TILT) * length)
        pygame.draw.line(screen, (255, 60, 60), (cx, cy), (ex, ey), 3)

def render_grid(screen):
    screen.fill(BACKGROUND_COLOR)
    surf = pygame.Surface((SIZE * CELL_SIZE, SIZE * CELL_SIZE), pygame.SRCALPHA)

    # initialize grid densities
    grid_density = [[0 for _ in range(SIZE)] for _ in range(SIZE)]

    # For each particle, add its contribution to nearby cells
    for p in particles:
        px = int(p.x / SIZE * SIZE)
        py = int(p.y / SIZE * SIZE)

        # radius in cells
        r_cells = int(H)
        for gx in range(max(0, px - r_cells), min(SIZE, px + r_cells + 1)):
            for gy in range(max(0, py - r_cells), min(SIZE, py + r_cells + 1)):
                # distance from particle center
                dx = (p.x / SIZE * SIZE - gx - 0.5)
                dy = (p.y / SIZE * SIZE - gy - 0.5)
                r2 = dx*dx + dy*dy
                if r2 < H*H:
                    grid_density[gx][gy] += 0.15

    # draw cells
    for gx in range(SIZE):
        for gy in range(SIZE):
            alpha = max(0, min(255, int(grid_density[gx][gy] * 200)))
            if alpha > 0:
                color = (50, 140, 255, alpha)
                pygame.draw.rect(surf, color, (gx*CELL_SIZE, gy*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    screen.blit(surf, (0, 0))

    # optional: draw tilt vector
    cx = SIZE * CELL_SIZE // 2
    cy = SIZE * CELL_SIZE // 2
    length = SIZE * CELL_SIZE // 2
    ex = int(cx + sin(TILT) * length)
    ey = int(cy + cos(TILT) * length)
    pygame.draw.line(screen, (255, 60, 60), (cx, cy), (ex, ey), 3)


pygame.init()
screen = pygame.display.set_mode((SIZE * CELL_SIZE, SIZE * CELL_SIZE))
clock = pygame.time.Clock()

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    keys = pygame.key.get_pressed()

    ROT_SPEED = 2.5

    if keys[pygame.K_LEFT]:
        TILT -= ROT_SPEED * DT
    if keys[pygame.K_RIGHT]:
        TILT += ROT_SPEED * DT

    if keys[pygame.K_UP]:
        TILT -= ROT_SPEED * DT * 3
    if keys[pygame.K_DOWN]:
        TILT += ROT_SPEED * DT * 3

    gx = G * sin(TILT)
    gy = G * cos(TILT)

    particles = update_particles(particles, gx, gy)

    render(screen)

    pygame.display.flip()

    DT = clock.tick(FPS) / 1000

pygame.init()
screen = pygame.display.set_mode((SIZE * CELL_SIZE, SIZE * CELL_SIZE))
clock = pygame.time.Clock()

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    keys = pygame.key.get_pressed()

    ROT_SPEED = 2.5

    if keys[pygame.K_LEFT]:
        TILT -= ROT_SPEED * DT
    if keys[pygame.K_RIGHT]:
        TILT += ROT_SPEED * DT

    if keys[pygame.K_UP]:
        TILT -= ROT_SPEED * DT * 3
    if keys[pygame.K_DOWN]:
        TILT += ROT_SPEED * DT * 3

    gx = G * sin(TILT)
    gy = G * cos(TILT)

    particles = update_particles(particles, gx, gy)

    render_grid(screen)

    pygame.display.flip()

    DT = clock.tick(FPS) / 1000


pygame.quit()