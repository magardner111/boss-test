# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 18:27:13 2026

@author: Tyler
"""

import pygame
import math
import sys

# =========================
# CONFIG
# =========================

WIDTH, HEIGHT = 900, 600
BACKGROUND = (15, 15, 25)
PLAYER_COLOR = (80, 200, 255)
BOSS_COLOR = (220, 120, 120)
SPRING_COLOR = (255, 180, 180)

PLAYER_SPEED = 350

NUM_NODES = 20
NODE_RADIUS = 48

# =========================
# ELASTIC CHAIN CLASS
# =========================

class ElasticChain:

    def __init__(self, anchor_pos):

        self.nodes = []
        self.velocities = []

        spacing = 0.5

        for i in range(NUM_NODES):
            self.nodes.append(
                (anchor_pos[0] - spacing * (NUM_NODES - i), anchor_pos[1])
            )
            self.velocities.append([0.0, 0.0])

        self.rest_lengths = []
        for i in range(NUM_NODES - 1):
            dx = self.nodes[i + 1][0] - self.nodes[i][0]
            dy = self.nodes[i + 1][1] - self.nodes[i][1]
            self.rest_lengths.append(math.hypot(dx, dy))

        self.base_stiffness = 20.0
        self.poisson_ratio = 0.4
        self.damping = 0.8
        self.mass = 5.0

    # -------------------------
    # UPDATE PHYSICS
    # -------------------------

    def update(self, anchor_pos, dt):

        # kinematic final node
        self.nodes[-1] = anchor_pos
        self.velocities[-1] = [0.0, 0.0]

        forces = [[0.0, 0.0] for _ in range(NUM_NODES)]

        # spring forces
        for i in range(NUM_NODES - 1):

            x0, y0 = self.nodes[i]
            x1, y1 = self.nodes[i + 1]

            dx = x1 - x0
            dy = y1 - y0
            L = math.hypot(dx, dy)

            if L == 0:
                continue

            rest = self.rest_lengths[i]
            strain = (L - rest) / rest

            stiffness = self.base_stiffness * (
                1 + self.poisson_ratio * abs(strain)
            )

            F = stiffness * (L - rest)

            fx = F * dx / L
            fy = F * dy / L

            forces[i][0] += fx
            forces[i][1] += fy
            forces[i + 1][0] -= fx
            forces[i + 1][1] -= fy

        # integrate free nodes
        for i in range(NUM_NODES - 1):

            vx, vy = self.velocities[i]

            ax = forces[i][0] / self.mass
            ay = forces[i][1] / self.mass

            vx += ax * dt
            vy += ay * dt

            vx *= self.damping
            vy *= self.damping

            x, y = self.nodes[i]
            x += vx * dt
            y += vy * dt

            self.nodes[i] = (x, y)
            self.velocities[i] = [vx, vy]

    # -------------------------
    # DRAW
    # -------------------------

    def draw(self, screen):

        for i in range(NUM_NODES - 1):

            p0 = self.nodes[i]
            p1 = self.nodes[i + 1]

            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            L = math.hypot(dx, dy)

            rest = self.rest_lengths[i]
            strain = (L - rest) / rest

            thickness = max(
                3,
                int(10 * (1 - self.poisson_ratio * strain))
            )

            pygame.draw.line(screen, SPRING_COLOR, p0, p1, thickness)

        for x, y in self.nodes:
            pygame.draw.circle(
                screen,
                BOSS_COLOR,
                (int(x), int(y)),
                NODE_RADIUS
            )

# =========================
# MAIN
# =========================

def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("OOP Elastic Chain")

    clock = pygame.time.Clock()

    player_pos = [WIDTH // 2, HEIGHT // 2]
    chain = ElasticChain(player_pos)

    running = True
    while running:

        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            player_pos[1] -= PLAYER_SPEED * dt
        if keys[pygame.K_s]:
            player_pos[1] += PLAYER_SPEED * dt
        if keys[pygame.K_a]:
            player_pos[0] -= PLAYER_SPEED * dt
        if keys[pygame.K_d]:
            player_pos[0] += PLAYER_SPEED * dt

        chain.update(tuple(player_pos), dt)

        screen.fill(BACKGROUND)

        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (int(player_pos[0]), int(player_pos[1])),
            15
        )

        chain.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
