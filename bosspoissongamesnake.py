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

# =========================
# BOSS INIT
# =========================

def initialize_boss(player_pos):

    node0 = (player_pos[0] - 200, player_pos[1])
    node1 = player_pos  # pinned to player

    dx = node1[0] - node0[0]
    dy = node1[1] - node0[1]
    rest_length = math.hypot(dx, dy)

    boss = {
        "nodes": [node0, node1],
        "velocity": [0.0, 0.0],  # velocity of node0 only
        "rest_length": rest_length,
        "base_stiffness": 8.0,
        "poisson_ratio": -.1,  # fake 1D coupling THIS CHANGES THE LENGTH TO GIRTH RATIO.  TRY .1-2.  DO NOT GO NEGATIVE!!!
        "damping": 0.94,
        "mass": 1.0
    }

    return boss


# =========================
# UPDATE
# =========================

def update_boss(boss, player_pos, dt):

    # Pin node1 to player
    boss["nodes"][1] = player_pos

    x0, y0 = boss["nodes"][0]
    x1, y1 = boss["nodes"][1]

    dx = x1 - x0
    dy = y1 - y0
    L = math.hypot(dx, dy)

    if L == 0:
        return

    strain = (L - boss["rest_length"]) / boss["rest_length"]

    # --- Fake Poisson effect ---
    # As it stretches, stiffness increases
    stiffness = boss["base_stiffness"] * (1 + boss["poisson_ratio"] * abs(strain))

    # Spring force
    F = stiffness * (L - boss["rest_length"])

    fx = F * dx / L
    fy = F * dy / L

    vx, vy = boss["velocity"]

    ax = fx / boss["mass"]
    ay = fy / boss["mass"]

    vx += ax * dt
    vy += ay * dt

    vx *= boss["damping"]
    vy *= boss["damping"]

    x0 += vx * dt
    y0 += vy * dt

    boss["nodes"][0] = (x0, y0)
    boss["velocity"] = [vx, vy]


# =========================
# DRAW
# =========================

def draw_boss(screen, boss):

    node0 = boss["nodes"][0]
    node1 = boss["nodes"][1]

    # Thickness changes with strain (visual Poisson illusion)
    dx = node1[0] - node0[0]
    dy = node1[1] - node0[1]
    L = math.hypot(dx, dy)

    strain = (L - boss["rest_length"]) / boss["rest_length"]

    thickness = max(3, int(12 * (1 - boss["poisson_ratio"] * strain)))

    pygame.draw.line(screen, SPRING_COLOR, node0, node1, thickness)

    pygame.draw.circle(screen, BOSS_COLOR, (int(node0[0]), int(node0[1])), 15)
    pygame.draw.circle(screen, BOSS_COLOR, (int(node1[0]), int(node1[1])), 15)


# =========================
# MAIN
# =========================

def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2-Node Elastic Boss")

    clock = pygame.time.Clock()

    player_pos = [WIDTH // 2, HEIGHT // 2]
    boss = initialize_boss(player_pos)

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

        update_boss(boss, tuple(player_pos), dt)

        screen.fill(BACKGROUND)

        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (int(player_pos[0]), int(player_pos[1])),
            15
        )

        draw_boss(screen, boss)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

