# -*- coding: utf-8 -*-
"""
Graph-Based Boss Fight
Boss Hit Reactions + Knockback + No Shooting During Shake
"""

import pygame
import math
import sys
import random

# ==================================================
# CONFIG
# ==================================================
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_RADIUS = 12
PLAYER_SPEED = 220

BOSS_SIZE = 200
BOSS_SPEED = 210
BOSS_MAX_LIFE = 100

GRID_W = 6
GRID_H = 6
CELL_W = WIDTH / GRID_W
CELL_H = HEIGHT / GRID_H

BULLET_SPEED = 520
BULLET_RADIUS = 4
FIRE_COOLDOWN = 0.25

# Shake
SHAKE_DURATION = 0.8
SHAKE_STRENGTH = 14

# Player stomp pause
PLAYER_PAUSE_TIME = 0.8

# Boss hit reaction
BOSS_HIT_SLOW_TIME = 0.6
BOSS_HIT_SPEED_MULT = 0.4
BOSS_FLASH_INTERVAL = 0.08
BOSS_FLASHES = 3

# Player knockback
PLAYER_KNOCKBACK_SPEED = 420
PLAYER_KNOCKBACK_TIME = 0.18

# ==================================================
# INIT
# ==================================================
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Graph Theory Boss Fight")
clock = pygame.time.Clock()

# Load stomp sounds
quake_sounds = []
for i in range(1, 4):
    try:
        s = pygame.mixer.Sound(f"quake{i}.wav")
        s.set_volume(0.8)
        quake_sounds.append(s)
    except:
        pass

# quake_index = 0  # (Not needed; you already track this in state["quake_index"])

# ==================================================
# GRID UTILS
# ==================================================
def world_to_node(pos):
    gx = int(pos.x // CELL_W)
    gy = int(pos.y // CELL_H)
    gx = max(0, min(GRID_W-1, gx))
    gy = max(0, min(GRID_H-1, gy))
    return gx, gy

def node_to_world(node):
    gx, gy = node
    x = gx * CELL_W + CELL_W / 2
    y = gy * CELL_H + CELL_H / 2
    return pygame.Vector2(x, y)

def get_neighbors(node):
    x, y = node
    neighbors = []
    if x > 0: neighbors.append((x-1, y))
    if x < GRID_W-1: neighbors.append((x+1, y))
    if y > 0: neighbors.append((x, y-1))
    if y < GRID_H-1: neighbors.append((x, y+1))
    return neighbors

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

# ==================================================
# COLLISION
# ==================================================
def circle_rect_collision(cx, cy, cr, rx, ry, rw, rh):
    closest_x = max(rx, min(cx, rx + rw))
    closest_y = max(ry, min(cy, ry + rh))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy <= cr * cr

# ==================================================
# BULLET
# ==================================================
class Bullet:
    def __init__(self, pos, vel):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)

    def update(self, dt):
        self.pos += self.vel * dt

# ==================================================
# RESET
# ==================================================
def reset_room(state):
    state["player_pos"] = pygame.Vector2(WIDTH // 2, HEIGHT - 100)

    state["boss_node"] = (GRID_W//2, GRID_H//2)
    state["boss_world"] = node_to_world(state["boss_node"])
    state["boss_target_node"] = None
    state["boss_prev_node"] = None
    state["boss_wait_timer"] = 0.0
    state["boss_move_progress"] = 0.0
    state["boss_life"] = BOSS_MAX_LIFE

    state["shake_timer"] = 0.0
    state["player_pause_timer"] = 0.0

    state["boss_hit_timer"] = 0.0
    state["boss_speed_multiplier"] = 1.0
    state["boss_flash_timer"] = 0.0
    state["boss_flash_count"] = 0

    state["player_knockback_vel"] = pygame.Vector2(0, 0)
    state["player_knockback_timer"] = 0.0

    state["bullets"].clear()

# ==================================================
# STATE
# ==================================================
state = {
    "player_pos": pygame.Vector2(WIDTH // 2, HEIGHT - 100),

    "boss_life": BOSS_MAX_LIFE,
    "boss_node": (GRID_W//2, GRID_H//2),
    "boss_world": node_to_world((GRID_W//2, GRID_H//2)),
    "boss_target_node": None,
    "boss_prev_node": None,
    "boss_wait_timer": 0.0,
    "boss_move_progress": 0.0,

    "boss_hit_timer": 0.0,
    "boss_speed_multiplier": 1.0,
    "boss_flash_timer": 0.0,
    "boss_flash_count": 0,

    "quake_index": 0,

    "shake_timer": 0.0,
    "player_pause_timer": 0.0,

    "player_knockback_vel": pygame.Vector2(0, 0),
    "player_knockback_timer": 0.0,

    "bullets": [],
    "fire_timer": 0.0,
}

# ==================================================
# BOSS AI
# ==================================================
def update_boss_grid(state, dt):

    if state["boss_wait_timer"] > 0:
        state["boss_wait_timer"] -= dt
        return

    player_node = world_to_node(state["player_pos"])
    boss_node = state["boss_node"]

    if state["boss_target_node"] is None:
        neighbors = get_neighbors(boss_node)
        if state["boss_prev_node"] in neighbors:
            neighbors = [n for n in neighbors if n != state["boss_prev_node"]]
        best = min(neighbors, key=lambda n: manhattan(n, player_node))
        state["boss_target_node"] = best
        state["boss_move_progress"] = 0.0

    start_pos = node_to_world(state["boss_node"])
    end_pos = node_to_world(state["boss_target_node"])
    distance = (end_pos - start_pos).length()

    current_speed = BOSS_SPEED * state["boss_speed_multiplier"]

    if distance == 0:
        t = 1.0
    else:
        t = state["boss_move_progress"] + (current_speed * dt) / distance
        t = min(t, 1.0)

    t_smooth = t * t * (3 - 2 * t)
    state["boss_world"] = start_pos.lerp(end_pos, t_smooth)

    footfall_offset = math.sin(t_smooth * math.pi) * 10
    state["boss_world"].y += footfall_offset

    state["boss_move_progress"] = t

    # ✅ LANDING EVENT (sound + shake only once)
    if t >= 1.0:
        state["boss_prev_node"] = state["boss_node"]
        state["boss_node"] = state["boss_target_node"]
        state["boss_target_node"] = None
        state["boss_wait_timer"] = 0.6

        state["shake_timer"] = SHAKE_DURATION
        state["player_pause_timer"] = PLAYER_PAUSE_TIME

        # Play stomp sound (alternate quake1/2/3)
        if quake_sounds:
            idx = state["quake_index"]
            quake_sounds[idx].play()
            state["quake_index"] = (idx + 1) % len(quake_sounds)

# ==================================================
# MAIN LOOP
# ==================================================
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # ---------------- PLAYER MOVEMENT ----------------
    if state["player_knockback_timer"] > 0:
        state["player_knockback_timer"] -= dt
        state["player_pos"] += state["player_knockback_vel"] * dt
        state["player_knockback_vel"] *= 0.85

    elif state["player_pause_timer"] > 0:
        state["player_pause_timer"] -= dt

    else:
        move = pygame.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        if move.length_squared() > 0:
            move = move.normalize()
            state["player_pos"] += move * PLAYER_SPEED * dt

    state["player_pos"].x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, state["player_pos"].x))
    state["player_pos"].y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, state["player_pos"].y))

    # ---------------- SHOOTING ----------------
    state["fire_timer"] -= dt
    mouse_pressed = pygame.mouse.get_pressed()

    if (
        mouse_pressed[0]
        and state["fire_timer"] <= 0
        and state["shake_timer"] <= 0
    ):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        dir_vec = mouse_pos - state["player_pos"]
        if dir_vec.length_squared() > 0:
            dir_vec = dir_vec.normalize()
            vel = dir_vec * BULLET_SPEED
            state["bullets"].append(Bullet(state["player_pos"], vel))
            state["fire_timer"] = FIRE_COOLDOWN

    # ---------------- BULLETS ----------------
    for b in state["bullets"][:]:
        b.update(dt)
        if b.pos.x < 0 or b.pos.x > WIDTH or b.pos.y < 0 or b.pos.y > HEIGHT:
            state["bullets"].remove(b)

    # ---------------- BOSS ----------------
    update_boss_grid(state, dt)

    boss_rect = pygame.Rect(
        state["boss_world"].x - BOSS_SIZE // 2,
        state["boss_world"].y - BOSS_SIZE // 2,
        BOSS_SIZE,
        BOSS_SIZE,
    )

    # Boss hit
    for b in state["bullets"][:]:
        if boss_rect.collidepoint(b.pos.x, b.pos.y):
            state["bullets"].remove(b)
            state["boss_life"] -= 1

            state["boss_hit_timer"] = BOSS_HIT_SLOW_TIME
            state["boss_speed_multiplier"] = BOSS_HIT_SPEED_MULT

            state["boss_flash_count"] = BOSS_FLASHES * 2
            state["boss_flash_timer"] = BOSS_FLASH_INTERVAL

            if state["boss_life"] <= 0:
                reset_room(state)

    # Boss slow timer
    if state["boss_hit_timer"] > 0:
        state["boss_hit_timer"] -= dt
        if state["boss_hit_timer"] <= 0:
            state["boss_speed_multiplier"] = 1.0

    # Flash logic
    if state["boss_flash_count"] > 0:
        state["boss_flash_timer"] -= dt
        if state["boss_flash_timer"] <= 0:
            state["boss_flash_timer"] = BOSS_FLASH_INTERVAL
            state["boss_flash_count"] -= 1

    # Player collision
    if circle_rect_collision(
        state["player_pos"].x,
        state["player_pos"].y,
        PLAYER_RADIUS,
        boss_rect.x,
        boss_rect.y,
        boss_rect.width,
        boss_rect.height,
    ):
        direction = state["player_pos"] - state["boss_world"]
        if direction.length_squared() > 0:
            direction = direction.normalize()
            state["player_knockback_vel"] = direction * PLAYER_KNOCKBACK_SPEED
            state["player_knockback_timer"] = PLAYER_KNOCKBACK_TIME

    # ---------------- CAMERA SHAKE ----------------
    camera_offset = pygame.Vector2(0, 0)

    if state["shake_timer"] > 0:
        state["shake_timer"] -= dt
        intensity = (state["shake_timer"] / SHAKE_DURATION) * SHAKE_STRENGTH
        camera_offset.x = random.uniform(-intensity, intensity)
        camera_offset.y = random.uniform(-intensity, intensity)

    # ---------------- DRAW ----------------
    screen.fill((20, 22, 28))

    for i in range(1, GRID_W):
        pygame.draw.line(screen, (50,50,50),
            (i*CELL_W + camera_offset.x, 0 + camera_offset.y),
            (i*CELL_W + camera_offset.x, HEIGHT + camera_offset.y))

    for j in range(1, GRID_H):
        pygame.draw.line(screen, (50,50,50),
            (0 + camera_offset.x, j*CELL_H + camera_offset.y),
            (WIDTH + camera_offset.x, j*CELL_H + camera_offset.y))

    pygame.draw.circle(screen, (90, 200, 255),
        state["player_pos"] + camera_offset,
        PLAYER_RADIUS)

    # Flash color
    if state["boss_flash_count"] % 2 == 1:
        boss_color = (255, 255, 120)
    else:
        boss_color = (220, 80, 80)

    pygame.draw.rect(screen, boss_color,
        boss_rect.move(camera_offset.x, camera_offset.y))

    for b in state["bullets"]:
        pygame.draw.circle(screen, (255, 240, 120),
            b.pos + camera_offset,
            BULLET_RADIUS)

    pygame.display.flip()

pygame.quit()
sys.exit()
