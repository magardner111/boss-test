import pygame
import math
import sys

# --------------------------------------------------
# Config
# --------------------------------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_RADIUS = 12
PLAYER_SPEED = 220  # pixels/sec

NPC_SIZE = 24
NPC_SPEED = 1.5     # pattern time multiplier

# Pattern translation offsets
NPC_OFFSET_X = WIDTH // 2
NPC_OFFSET_Y = HEIGHT // 2

RESET_DELAY_MS = 400

# --------------------------------------------------
# Init (pygame-ce)
# --------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zelda-like Dodge Room (pygame-ce)")
clock = pygame.time.Clock()

# --------------------------------------------------
# Collision
# --------------------------------------------------
def circle_rect_collision(cx, cy, cr, rx, ry, rw, rh):
    closest_x = max(rx, min(cx, rx + rw))
    closest_y = max(ry, min(cy, ry + rh))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy <= cr * cr

# --------------------------------------------------
# NPC Movement Patterns (pure geometry)
# --------------------------------------------------
def pattern_circle(t):
    r = 160
    return math.cos(t) * r, math.sin(t) * r

def pattern_figure_8(t):
    a = 160
    return math.sin(t) * a, math.sin(t * 2) * a * 0.5

def pattern_lissajous(t):
    a = 160
    return math.sin(t * 3) * a, math.sin(t * 2) * a

def pattern_zigzag(t):
    x = math.sin(t) * 200
    y = ((t * 60) % 300) - 150
    return x, y

def pattern_square_patrol(t):
    size = 180
    speed = 120
    phase = int((t * speed) // size) % 4
    offset = (t * speed) % size

    if phase == 0:
        return -size / 2 + offset, -size / 2
    elif phase == 1:
        return size / 2, -size / 2 + offset
    elif phase == 2:
        return size / 2 - offset, size / 2
    else:
        return -size / 2, size / 2 - offset

# 🔁 Choose your pattern here
NPC_PATTERN = pattern_figure_8

# --------------------------------------------------
# Reset
# --------------------------------------------------
def reset_room():
    return {
        "player_pos": pygame.Vector2(WIDTH // 2, HEIGHT - 100),
        "npc_time": 0.0,
        "reset_cooldown": RESET_DELAY_MS,
    }

state = reset_room()

# --------------------------------------------------
# Main Loop
# --------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # ----------------------------------------------
    # Player Movement (WASD)
    # ----------------------------------------------
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_w]:
        move.y -= 1
    if keys[pygame.K_s]:
        move.y += 1
    if keys[pygame.K_a]:
        move.x -= 1
    if keys[pygame.K_d]:
        move.x += 1

    if move.length_squared() > 0:
        move = move.normalize()
        state["player_pos"] += move * PLAYER_SPEED * dt

    state["player_pos"].x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, state["player_pos"].x))
    state["player_pos"].y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, state["player_pos"].y))

    # ----------------------------------------------
    # NPC Pattern Motion
    # ----------------------------------------------
    state["npc_time"] += dt * NPC_SPEED
    ox, oy = NPC_PATTERN(state["npc_time"])

    npc_rect = pygame.Rect(
        NPC_OFFSET_X + ox - NPC_SIZE // 2,
        NPC_OFFSET_Y + oy - NPC_SIZE // 2,
        NPC_SIZE,
        NPC_SIZE,
    )

    # ----------------------------------------------
    # Collision + Reset
    # ----------------------------------------------
    if state["reset_cooldown"] > 0:
        state["reset_cooldown"] -= clock.get_time()
    else:
        if circle_rect_collision(
            state["player_pos"].x,
            state["player_pos"].y,
            PLAYER_RADIUS,
            npc_rect.x,
            npc_rect.y,
            npc_rect.width,
            npc_rect.height,
        ):
            state = reset_room()

    # ----------------------------------------------
    # Draw
    # ----------------------------------------------
    screen.fill((24, 24, 30))

    # Player
    pygame.draw.circle(
        screen,
        (90, 200, 255),
        state["player_pos"],
        PLAYER_RADIUS,
    )

    # NPC
    pygame.draw.rect(screen, (220, 80, 80), npc_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()
