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
BOSS_MAX_LIFE = 30

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
font = pygame.font.SysFont("arial", 24, bold=True)
big_font = pygame.font.SysFont("arial", 32, bold=True)
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

# ==================================================
# CUSTOM NODE LAYOUT
# ==================================================
def compute_custom_nodes(player_pos):
    """Compute 5-node graph dynamically; node 4 = player."""
    node4 = pygame.Vector2(player_pos)           # Player node
    node3 = pygame.Vector2(WIDTH/2, HEIGHT/2)   # Center node
    edge_len = 200

    # Node 0: one step from player toward center
    dir_to_center = (node3 - node4)
    if dir_to_center.length_squared() == 0:
        dir_to_center = pygame.Vector2(0, -1)
    else:
        dir_to_center = dir_to_center.normalize()
    node0 = node4 + dir_to_center * edge_len

    # Nodes 1 & 2: ±120° from dir_to_center around node0
    angle = math.radians(120)
    rot = lambda v, a: pygame.Vector2(
        v.x * math.cos(a) - v.y * math.sin(a),
        v.x * math.sin(a) + v.y * math.cos(a)
    )
    node1 = node0 + rot(dir_to_center, angle) * edge_len
    node2 = node0 + rot(dir_to_center, -angle) * edge_len

    nodes = {0: node0, 1: node1, 2: node2, 3: node3, 4: node4}
    edges = [(0,1),(0,2),(0,3),(0,4)]
    neighbors = {0:[1,2,3,4], 1:[0], 2:[0], 3:[0], 4:[0]}

    return nodes, edges, neighbors

# ------------------ NODE UTILS ------------------
def nearest_node(pos, nodes):
    return min(nodes.keys(), key=lambda n: (nodes[n]-pos).length_squared())

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
    state["player_pos"] = custom_nodes[4]  # reset player on node 4
    state["boss_node"] = 0
    state["boss_world"] = custom_nodes[0]
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
    state["player_knockback_vel"] = pygame.Vector2(0,0)
    state["player_knockback_timer"] = 0.0
    state["bullets"].clear()

# ==================================================
# STATE
# ==================================================
initial_player_pos = pygame.Vector2(WIDTH//2, HEIGHT-100)
custom_nodes, custom_edges, custom_neighbors = compute_custom_nodes(initial_player_pos)

state = {
    "player_pos": custom_nodes[4],
    "boss_life": BOSS_MAX_LIFE,
    "boss_node": 0,
    "boss_world": custom_nodes[0],
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
    "taunt_shown": False,
    "taunt_timer": 0.0
}

# ==================================================
# BOSS AI
# ==================================================
def update_boss_graph(state, dt):
    if state["boss_wait_timer"] > 0:
        state["boss_wait_timer"] -= dt
        return

    boss_node = state["boss_node"]
    player_node = nearest_node(state["player_pos"], custom_nodes)

    if state["boss_target_node"] is None:
        neighbors = custom_neighbors[boss_node]
        # avoid going back
        if state["boss_prev_node"] in neighbors:
            neighbors = [n for n in neighbors if n != state["boss_prev_node"]]
        if not neighbors:
            neighbors = [state["boss_prev_node"]] if state["boss_prev_node"] is not None else [boss_node]

        # pick neighbor closest to player
        best = min(neighbors, key=lambda n: (custom_nodes[n]-custom_nodes[player_node]).length_squared())
        state["boss_target_node"] = best
        state["boss_move_progress"] = 0.0

    start_pos = custom_nodes[boss_node]
    end_pos = custom_nodes[state["boss_target_node"]]
    distance = (end_pos - start_pos).length()
    current_speed = BOSS_SPEED * state["boss_speed_multiplier"]

    if distance == 0:
        t = 1.0
    else:
        t = state["boss_move_progress"] + (current_speed*dt)/distance
        t = min(t, 1.0)

    t_smooth = t*t*(3-2*t)
    state["boss_world"] = start_pos.lerp(end_pos, t_smooth)
    state["boss_world"].y += math.sin(t_smooth*math.pi)*10
    state["boss_move_progress"] = t

    if t >= 1.0:
        state["boss_prev_node"] = boss_node
        state["boss_node"] = state["boss_target_node"]
        state["boss_target_node"] = None
        state["boss_wait_timer"] = 0.6
        state["shake_timer"] = SHAKE_DURATION
        state["player_pause_timer"] = PLAYER_PAUSE_TIME
        if quake_sounds:
            idx = state["quake_index"]
            quake_sounds[idx].play()
            state["quake_index"] = (idx+1)%len(quake_sounds)

# ==================================================
# MAIN LOOP
# ==================================================
running = True
while running:
    dt = clock.tick(FPS)/1000.0

    # Recompute dynamic nodes so node 4 = player
    if state["boss_wait_timer"] > 0:
        custom_nodes, custom_edges, custom_neighbors = compute_custom_nodes(state["player_pos"])

    if state["taunt_timer"] > 0:
        state["taunt_timer"] -= dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # ---------------- PLAYER MOVEMENT ----------------
    if state["player_knockback_timer"] > 0:
        state["player_knockback_timer"] -= dt
        state["player_pos"] += state["player_knockback_vel"]*dt
        state["player_knockback_vel"] *= 0.85
    elif state["player_pause_timer"] > 0:
        state["player_pause_timer"] -= dt
    else:
        move = pygame.Vector2(keys[pygame.K_d]-keys[pygame.K_a],
                              keys[pygame.K_s]-keys[pygame.K_w])
        if move.length_squared() > 0:
            move = move.normalize()
            state["player_pos"] += move*PLAYER_SPEED*dt

    # Clamp to screen
    state["player_pos"].x = max(PLAYER_RADIUS, min(WIDTH-PLAYER_RADIUS, state["player_pos"].x))
    state["player_pos"].y = max(PLAYER_RADIUS, min(HEIGHT-PLAYER_RADIUS, state["player_pos"].y))

    # ---------------- SHOOTING ----------------
    state["fire_timer"] -= dt
    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0] and state["fire_timer"] <= 0 and state["shake_timer"] <= 0:
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        dir_vec = mouse_pos - state["player_pos"]
        if dir_vec.length_squared() > 0:
            vel = dir_vec.normalize()*BULLET_SPEED
            state["bullets"].append(Bullet(state["player_pos"], vel))
            state["fire_timer"] = FIRE_COOLDOWN

    # ---------------- BULLETS ----------------
    for b in state["bullets"][:]:
        b.update(dt)
        if b.pos.x<0 or b.pos.x>WIDTH or b.pos.y<0 or b.pos.y>HEIGHT:
            state["bullets"].remove(b)

    # ---------------- BOSS ----------------
    update_boss_graph(state, dt)
    boss_rect = pygame.Rect(state["boss_world"].x-BOSS_SIZE//2,
                            state["boss_world"].y-BOSS_SIZE//2,
                            BOSS_SIZE, BOSS_SIZE)

    # Boss hit
    for b in state["bullets"][:]:
        if boss_rect.collidepoint(b.pos.x, b.pos.y):
            state["bullets"].remove(b)
            state["boss_life"] -= 1
            if state["boss_life"] <= BOSS_MAX_LIFE*0.25 and not state["taunt_shown"]:
                state["taunt_shown"] = True
                state["taunt_timer"] = 4.0
            state["boss_hit_timer"] = BOSS_HIT_SLOW_TIME
            state["boss_speed_multiplier"] = BOSS_HIT_SPEED_MULT
            state["boss_flash_count"] = BOSS_FLASHES*2
            state["boss_flash_timer"] = BOSS_FLASH_INTERVAL
            if state["boss_life"] <= 0:
                reset_room(state)

    if state["boss_hit_timer"] > 0:
        state["boss_hit_timer"] -= dt
        if state["boss_hit_timer"] <= 0:
            state["boss_speed_multiplier"] = 1.0

    if state["boss_flash_count"] > 0:
        state["boss_flash_timer"] -= dt
        if state["boss_flash_timer"] <= 0:
            state["boss_flash_timer"] = BOSS_FLASH_INTERVAL
            state["boss_flash_count"] -= 1

    # Player collision
    if circle_rect_collision(state["player_pos"].x, state["player_pos"].y, PLAYER_RADIUS,
                             boss_rect.x, boss_rect.y, boss_rect.width, boss_rect.height):
        direction = state["player_pos"] - state["boss_world"]
        if direction.length_squared() > 0:
            state["player_knockback_vel"] = direction.normalize()*PLAYER_KNOCKBACK_SPEED
            state["player_knockback_timer"] = PLAYER_KNOCKBACK_TIME

    # Camera shake
    camera_offset = pygame.Vector2(0,0)
    if state["shake_timer"] > 0:
        state["shake_timer"] -= dt
        intensity = (state["shake_timer"]/SHAKE_DURATION)*SHAKE_STRENGTH
        camera_offset.x = random.uniform(-intensity,intensity)
        camera_offset.y = random.uniform(-intensity,intensity)

    # ---------------- DRAW ----------------
    screen.fill((20,22,28))

    # Draw edges
    for a,b in custom_edges:
        pygame.draw.line(screen,(80,80,80),custom_nodes[a]+camera_offset,custom_nodes[b]+camera_offset,2)

    # Draw nodes
    for n,pos in custom_nodes.items():
        color = (100,200,255) if n==4 else (200,200,200)
        pygame.draw.circle(screen,color,pos+camera_offset,10)

    # Draw player
    pygame.draw.circle(screen,(90,200,255),state["player_pos"]+camera_offset,PLAYER_RADIUS)

    # Draw boss
    boss_color = (255,255,120) if state["boss_flash_count"]%2==1 else (220,80,80)
    pygame.draw.rect(screen,boss_color,boss_rect.move(camera_offset.x,camera_offset.y))

    # Draw bullets
    for b in state["bullets"]:
        pygame.draw.circle(screen,(255,240,120),b.pos+camera_offset,BULLET_RADIUS)

    # Taunt
    if state["taunt_timer"] > 0:
        text1 = big_font.render("I used to be the captain of the basketball team.", True, (255,240,200))
        text2 = big_font.render("I will trash you, smalls.", True, (255,180,180))
        box_w = max(text1.get_width(), text2.get_width())+40
        box_h = text1.get_height()+text2.get_height()+30
        box_x = WIDTH//2 - box_w//2
        box_y = 40
        pygame.draw.rect(screen,(0,0,0),(box_x,box_y,box_w,box_h))
        pygame.draw.rect(screen,(200,60,60),(box_x,box_y,box_w,box_h),2)
        screen.blit(text1,(WIDTH//2 - text1.get_width()//2, box_y+8))
        screen.blit(text2,(WIDTH//2 - text2.get_width()//2, box_y+8+text1.get_height()))

    pygame.display.flip()

pygame.quit()
sys.exit()

