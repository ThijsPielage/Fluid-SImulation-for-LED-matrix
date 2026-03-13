import pygame
import random
from math import sin, cos

# Simulation settings
G = 15
FPS = 60
SIZE = 20

NUM_PARTICLES = 300

H = 1.5
REST_DENSITY = 8
PRESSURE_K = 0.002
ITERATIONS = 5

DAMP_FACTOR = 0.995

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

    # Apply forces + predict positions
    for p in particles:
        p.vx += gx * DT
        p.vy += gy * DT

        p.px = p.x + p.vx * DT
        p.py = p.y + p.vy * DT

    cell_size =  H
    grid = {}

    for i, p in enumerate(particles):
        cx = int(p.px // cell_size)
        cy = int(p.py // cell_size)

        if (cx, cy) not in grid:
            grid[(cx, cy)] = []

        grid[(cx, cy)].append(i)

    for _ in range(ITERATIONS):

        densities = [0] * len(particles)

        # --- density estimate ---
        for i, p in enumerate(particles):

            cx = int(p.px // cell_size)
            cy = int(p.py // cell_size)

            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):

                    cell = (cx + ox, cy + oy)

                    if cell not in grid:
                        continue

                    for j in grid[cell]:
                        q = particles[j]

                        dx = p.px - q.px
                        dy = p.py - q.py

                        if dx*dx + dy*dy < H*H:
                            densities[i] += 1

        # --- pressure solve ---
        for i, p in enumerate(particles):

            if densities[i] <= REST_DENSITY:
                continue

            pressure = (densities[i] - REST_DENSITY) * PRESSURE_K

            cx = int(p.px // cell_size)
            cy = int(p.py // cell_size)

            for ox in (-1,0,1):
                for oy in (-1,0,1):

                    cell = (cx+ox, cy+oy)

                    if cell not in grid:
                        continue

                    for j in grid[cell]:

                        if i == j:
                            continue

                        q = particles[j]

                        dx = p.px - q.px
                        dy = p.py - q.py

                        dist2 = dx*dx + dy*dy
                        if dist2 >= H*H or dist2 == 0:
                            continue

                        dist = max(0.001, dist2 ** 0.5)

                        nx = dx / dist
                        ny = dy / dist

                        corr = pressure * (1 - dist / H)

                        p.px += nx * corr * 0.5
                        p.py += ny * corr * 0.5

                        q.px -= nx * corr * 0.5
                        q.py -= ny * corr * 0.5

    # --- integrate ---
    for p in particles:

        p.vx = (p.px - p.x) / DT
        p.vy = (p.py - p.y) / DT

        p.vx *= DAMP_FACTOR
        p.vy *= DAMP_FACTOR

        p.x = p.px
        p.y = p.py

        # walls
        # margin = H * 2
        # if p.x < margin:
        #     p.vx += (margin - p.x) * 100 * DT
        # elif p.x > SIZE - margin:
        #     p.vx += (SIZE - margin - p.x) * 100 * DT

        # if p.y < margin:
        #     p.vy += (margin - p.y) * 100 * DT
        # elif p.y > SIZE - margin:
        #     p.vy += (SIZE - margin - p.y) * 100 * DT

        if p.x < 0:
            p.x = 0
            p.vx *= -0.5
        elif p.x > SIZE - 1:
            p.x = SIZE - 1
            p.vx *= -0.5

        if p.y < 0:
            p.y = 0
            p.vy *= -0.5
        elif p.y > SIZE - 1:
            p.y = SIZE - 1
            p.vy *= -0.5

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


pygame.quit()