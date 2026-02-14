# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 19:15:30 2026

@author: Tyler
"""

import pygame
import math
import sys
import time
import random

# =========================
# CONFIG
# =========================

WIDTH, HEIGHT = 1000, 650
BACKGROUND = (15, 15, 25)
PLAYER_COLOR = (80, 200, 255)
BOSS_COLOR = (220, 120, 120)
SPRING_COLOR = (255, 180, 180)

PLAYER_SPEED = 350

# =========================
# BOSS INIT
# =========================

def initialize_boss(player_pos):

    node0 = (player_pos[0] - 250, player_pos[1])
    node1 = player_pos

    dx = node1[0] - node0[0]
    dy = node1[1] - node0[1]
    rest_length = math.hypot(dx, dy)

    return {
        "nodes": [node0, node1],
        "velocity": [0.0, 0.0],
        "rest_length": rest_length,
        "stiffness": 8.0,
        "damping": 0.94,
        "mass": 1.0,
        "wave_speed": 10.0,
        "color": (255, 180, 180),
        "shock": {
            "active": False,
            "t": 0.0,
            "speed": 10,
            "width": .08,
            "strength": 60
            
        }
    }


# =========================
# UPDATE PHYSICS
# =========================

def update_boss(boss, player_pos, dt):

    boss["nodes"][1] = player_pos

    x0, y0 = boss["nodes"][0]
    x1, y1 = boss["nodes"][1]

    dx = x1 - x0
    dy = y1 - y0
    L = math.hypot(dx, dy)

    if L == 0:
        return

    strain = (L - boss["rest_length"]) / boss["rest_length"]

    F = boss["stiffness"] * (L - boss["rest_length"])

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

    # ---- Update shock pulse ----
    shock = boss["shock"]

    if shock["active"]:
        shock["t"] += shock["speed"] * dt
        if shock["t"] > 1.0:
            shock["active"] = False
            shock["t"] = 0.0

    # Auto-trigger shock if overstretched
    if abs(strain) > 0.25 and not shock["active"]:
        shock["active"] = True
        shock["t"] = 0.0


# =========================
# DRAW SINE EDGE WITH SHOCK
# =========================

def draw_sine_edge(screen, boss, time_elapsed):

    node0 = boss["nodes"][0]
    node1 = boss["nodes"][1]

    x0, y0 = node0
    x1, y1 = node1

    dx = x1 - x0
    dy = y1 - y0
    L = math.hypot(dx, dy)

    if L == 0:
        return

    ux = dx / L
    uy = dy / L

    px = -uy
    py = ux

    strain = (L - boss["rest_length"]) / boss["rest_length"]

    base_amplitude = 9 * (1 + abs(strain))
    frequency = 5 + 6 * abs(strain)

    shock = boss["shock"]

    points = []
    segments = 80

    for i in range(segments + 1):

        t = i / segments

        base_x = x0 + ux * L * t
        base_y = y0 + uy * L * t

        wave = base_amplitude * math.sin(
            frequency * t * math.pi +
            time_elapsed * boss["wave_speed"]
        )

        # ---- Shock pulse modulation ----
        if shock["active"]:
            center = shock["t"]
            width = shock["width"]
            strength = shock["strength"]

            gaussian = math.exp(-((t - center) ** 2) / (2 * width ** 2))
            wave += gaussian * strength

        final_x = base_x + px * wave
        final_y = base_y + py * wave

        points.append((final_x, final_y))

    pygame.draw.lines(screen, boss["color"], False, points, 3)


def draw_boss(screen, boss, time_elapsed):

    draw_sine_edge(screen, boss, time_elapsed)

    for node in boss["nodes"]:
        pygame.draw.circle(
            screen,
            BOSS_COLOR,
            (int(node[0]), int(node[1])),
            16
        )


# =========================
# MAIN
# =========================

def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Shock Pulse Boss")

    clock = pygame.time.Clock()

    player_pos = [WIDTH // 2, HEIGHT // 2]
    boss = initialize_boss(player_pos)

    start_time = time.time()

    running = True
    while running:

        dt = clock.tick(60) / 1000.0
        time_elapsed = time.time() - start_time

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

        # Manual shock trigger
        if keys[pygame.K_SPACE] and not boss["shock"]["active"]:
            boss["shock"]["active"] = True
            boss["shock"]["t"] = 0.0
        
            # Change to random color
            boss["color"] = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )

        update_boss(boss, tuple(player_pos), dt)

        screen.fill(BACKGROUND)

        pygame.draw.circle(
            screen,
            PLAYER_COLOR,
            (int(player_pos[0]), int(player_pos[1])),
            15
        )

        draw_boss(screen, boss, time_elapsed)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

