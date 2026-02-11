import pygame
import math
import random
import sys

# =====================================================
# CONFIG (SAFE FOR NOVICES TO EDIT)
# =====================================================
WIDTH, HEIGHT = 800, 600
FPS = 60

# ---------------- PLAYER ----------------
PLAYER_RADIUS = 12
PLAYER_SPEED = 220
PLAYER_MAX_HP = 5
INVULN_TIME = 1.5
KNOCKBACK_FORCE = 600

# Sword
SWORD_RANGE = 43
SWORD_ARC_DEG = 180
SWORD_TIME = 0.20
SWORD_AFTERIMAGE_TIME = 0.03

# ---------------- BOSS ----------------
BOSS_SIZE = 28
BOSS_MAX_HP = 12
BOSS_MOVE_SPEED = 500
BOSS_CHARGE_SPEED = 770

TOP_MIDDLE = pygame.Vector2(WIDTH // 2, BOSS_SIZE // 2 + 18)

BETWEEN_PATTERN_PAUSE = 1.0
TELEGRAPH_TIME = 0.7
BLINK_RATE = 0.15

# ---------------- PROJECTILES ----------------
PROJECTILE_SPEED = 280
PROJECTILE_SIZE = 10
PROJECTILE_INTERVAL = 0.12
PROJECTILE_LIFETIME = 2.5
PROJECTILE_FADE_TIME = 0.4

# ---------------- PATTERN TIMING ----------------
PATTERN_TIME = 4.0
CIRCLE_TIME = 2.0
CHARGE_TIME = 0.7

# Circle pattern
CIRCLE_CENTER = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
CIRCLE_RADIUS = 170
CIRCLE_ANG_SPEED = 2.6

# =====================================================
# INIT
# =====================================================
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boss Pattern Demo (Combat Restored)")
clock = pygame.time.Clock()
attack_sounds = [
    pygame.mixer.Sound("attack1.wav"),
    pygame.mixer.Sound("attack2.wav")
]
# =====================================================
# HELPERS
# =====================================================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def move_towards(pos, target, speed, dt):
    delta = target - pos
    dist = delta.length()
    if dist < 1:
        return target
    return pos + delta.normalize() * min(speed * dt, dist)

def circle_rect_collision(circle_pos, radius, rect):
    cx, cy = circle_pos
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy <= radius * radius

# =====================================================
# PROJECTILE
# =====================================================
class Projectile:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, PROJECTILE_SPEED)
        self.age = 0.0
        self.alpha = 255
        self.rect = pygame.Rect(0, 0, PROJECTILE_SIZE, PROJECTILE_SIZE)
        self.rect.center = self.pos

    def update(self, dt):
        self.age += dt
        self.pos += self.vel * dt
        self.rect.center = self.pos

        time_left = PROJECTILE_LIFETIME - self.age
        if time_left <= PROJECTILE_FADE_TIME:
            self.alpha = int(255 * max(time_left / PROJECTILE_FADE_TIME, 0))
        else:
            self.alpha = 255

    def alive(self):
        return self.age < PROJECTILE_LIFETIME

    def draw(self, surf):
        if self.alpha <= 0:
            return
        s = pygame.Surface((PROJECTILE_SIZE, PROJECTILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (*PROJECTILE_COLOR, self.alpha), s.get_rect())
        surf.blit(s, self.rect)

# =====================================================
# STATE
# =====================================================
state = {
    # Player
    "player_pos": pygame.Vector2(WIDTH // 2, HEIGHT - 80),
    "player_vel": pygame.Vector2(0, 0),
    "player_hp": PLAYER_MAX_HP,
    "invuln": 0.0,
    "facing": pygame.Vector2(0, -1),

    # Sword
    "sword_timer": 0.0,
    "sword_active": False,
    "afterimages": [],
    "space_was_down": False,       # <-- NEW: prevents hold-to-repeat
    "sword_hit_this_swing": False, # <-- NEW: prevents multi-hit per swing

    # Boss
    "boss_pos": TOP_MIDDLE.copy(),
    "boss_hp": BOSS_MAX_HP,
    "boss_state": "pause",

    "pause_timer": 0.0,
    "telegraph_timer": 0.0,
    "pattern_index": 0,
    "pattern_timer": 0.0,
    "pattern_data": {},

    # Boss damage flash (3 red flashes)
    "boss_flash_on": True,
    "boss_flash_timer": 0.0,
    "boss_flash_interval": 0.08,   # speed of flashing
    "boss_flashes_left": 0,        # counts red flashes left
}

# ---------------- COLORS ----------------
BG_COLOR = (20, 20, 30)

PLAYER_COLOR = (90, 200, 255)

BOSS_BASE_COLOR = (60, 200, 80)     # Green
BOSS_HIT_COLOR = (255, 40, 40)      # Flash red
BOSS_TELEGRAPH_BLUE = (120, 200, 255)
BOSS_TELEGRAPH_YELLOW = (255, 220, 80)

PROJECTILE_COLOR = (255, 140, 40)

UI_TEXT_COLOR = (240, 240, 240)
UI_SUBTEXT_COLOR = (200, 200, 200)


projectiles = []

# Game end state
game_over = False
game_result = ""  # "WIN" or "LOSE"

# =====================================================
# DAMAGE FUNCTIONS
# =====================================================
def damage_player(from_pos):
    if state["invuln"] > 0:
        return
    state["player_hp"] -= 1
    state["invuln"] = INVULN_TIME

    knock = state["player_pos"] - from_pos
    if knock.length() == 0:
        knock = pygame.Vector2(0, 1)
    state["player_vel"] = knock.normalize() * KNOCKBACK_FORCE

def damage_boss(from_pos):
    # Boss takes 1 damage
    state["boss_hp"] -= 1

    # Start "flash red 3 times"
    state["boss_flashes_left"] = 3
    state["boss_flash_on"] = True   # start with red ON
    state["boss_flash_timer"] = 0.0

    # ---- NEW: knock player back ----
    knock = state["player_pos"] - from_pos
    if knock.length() == 0:
        knock = pygame.Vector2(0, 1)
    state["player_vel"] = knock.normalize() * KNOCKBACK_FORCE

# =====================================================
# PATTERN CONTROL
# =====================================================
def start_return():
    state["boss_state"] = "return"
    state["pattern_data"] = {}
    projectiles.clear()

# =====================================================
# PATTERNS
# =====================================================
def pattern_projectile_rain(dt):
    data = state["pattern_data"]
    data.setdefault("spawn", 0.0)

    state["boss_pos"] = move_towards(state["boss_pos"], TOP_MIDDLE, BOSS_MOVE_SPEED, dt)

    data["spawn"] += dt
    while data["spawn"] >= PROJECTILE_INTERVAL:
        data["spawn"] -= PROJECTILE_INTERVAL
        projectiles.append(Projectile(random.randint(20, WIDTH - 20), -20))

def pattern_direct_charge(dt):
    data = state["pattern_data"]

    if "dir" not in data:
        d = state["player_pos"] - state["boss_pos"]
        data["dir"] = d.normalize() if d.length() else pygame.Vector2(0, 1)
        data["time"] = 0.0

    data["time"] += dt
    state["boss_pos"] += data["dir"] * BOSS_CHARGE_SPEED * dt

    if data["time"] >= CHARGE_TIME:
        start_return()

def pattern_circle_double_charge(dt):
    data = state["pattern_data"]
    data.setdefault("stage", "circle")
    data.setdefault("angle", 0.0)
    data.setdefault("time", 0.0)
    data.setdefault("charges", 0)

    data["time"] += dt

    if data["stage"] == "circle":
        data["angle"] += CIRCLE_ANG_SPEED * dt
        target = CIRCLE_CENTER + pygame.Vector2(
            math.cos(data["angle"]),
            math.sin(data["angle"])
        ) * CIRCLE_RADIUS

        state["boss_pos"] = move_towards(state["boss_pos"], target, BOSS_MOVE_SPEED, dt)

        if data["time"] >= CIRCLE_TIME:
            data["stage"] = "charge"
            data["time"] = 0.0
            d = state["player_pos"] - state["boss_pos"]
            data["dir"] = d.normalize() if d.length() else pygame.Vector2(0, 1)

    else:
        state["boss_pos"] += data["dir"] * BOSS_CHARGE_SPEED * dt

        if data["time"] >= CHARGE_TIME:
            data["charges"] += 1
            data["time"] = 0.0
            if data["charges"] >= 2:
                start_return()
            else:
                data["stage"] = "circle"

PATTERNS = [
    pattern_projectile_rain,
    pattern_direct_charge,
    pattern_circle_double_charge,
]

# =====================================================
# MAIN LOOP
# =====================================================
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # -------------------------------------------------
    # If game over, stop updating gameplay (but keep drawing)
    # -------------------------------------------------
    if not game_over:

        # ---------------- PLAYER MOVEMENT ----------------
        if not state["sword_active"]:  # <-- movement lock during attack
            move = pygame.Vector2(
                keys[pygame.K_d] - keys[pygame.K_a],
                keys[pygame.K_s] - keys[pygame.K_w],
            )

            if move.length():
                state["facing"] = move.normalize()
                state["player_pos"] += state["facing"] * PLAYER_SPEED * dt


        state["player_pos"] += state["player_vel"] * dt
        state["player_vel"] *= 0.85

        state["player_pos"].x = clamp(state["player_pos"].x, PLAYER_RADIUS, WIDTH - PLAYER_RADIUS)
        state["player_pos"].y = clamp(state["player_pos"].y, PLAYER_RADIUS, HEIGHT - PLAYER_RADIUS)

        if state["invuln"] > 0:
            state["invuln"] -= dt

        # ---------------- SWORD (PRESS ONCE, NO HOLD-TO-REPEAT, UNINTERRUPTIBLE) ----------------
        space_down = keys[pygame.K_SPACE]
        space_pressed_this_frame = space_down and (not state["space_was_down"])

        # Only start a new swing if:
        # 1) Space was PRESSED this frame (not held)
        # 2) Sword is NOT already swinging
        if space_pressed_this_frame and (not state["sword_active"]):
            state["sword_active"] = True
            state["sword_timer"] = SWORD_TIME
            state["sword_hit_this_swing"] = False
            # Play random swing sound
            random.choice(attack_sounds).play()

        # Update sword swing if active (cannot be interrupted)
        if state["sword_active"]:
            state["sword_timer"] -= dt
            progress = 1 - (state["sword_timer"] / SWORD_TIME)

            state["afterimages"].append({
                "progress": progress,
                "time": SWORD_AFTERIMAGE_TIME
            })

            if state["sword_timer"] <= 0:
                state["sword_active"] = False

        # Afterimage decay
        for a in state["afterimages"]:
            a["time"] -= dt
        state["afterimages"] = [a for a in state["afterimages"] if a["time"] > 0]

        # Update space tracking LAST (so "pressed" is computed correctly)
        state["space_was_down"] = space_down

        # ---------------- BOSS FSM ----------------
        if state["boss_state"] == "pause":
            state["pause_timer"] += dt
            state["boss_pos"] = TOP_MIDDLE.copy()
            if state["pause_timer"] >= BETWEEN_PATTERN_PAUSE:
                state["boss_state"] = "telegraph"
                state["telegraph_timer"] = 0.0

        elif state["boss_state"] == "telegraph":
            state["telegraph_timer"] += dt
            if state["telegraph_timer"] >= TELEGRAPH_TIME:
                state["boss_state"] = "attack"
                state["pattern_timer"] = 0.0
                state["pattern_data"] = {}

        elif state["boss_state"] == "attack":
            state["pattern_timer"] += dt
            PATTERNS[state["pattern_index"]](dt)
            if state["pattern_timer"] >= PATTERN_TIME:
                start_return()

        elif state["boss_state"] == "return":
            state["boss_pos"] = move_towards(
                state["boss_pos"], TOP_MIDDLE, BOSS_MOVE_SPEED, dt
            )
            if state["boss_pos"] == TOP_MIDDLE:
                state["boss_state"] = "pause"
                state["pause_timer"] = 0.0
                state["pattern_index"] = (state["pattern_index"] + 1) % len(PATTERNS)

        # ---------------- PROJECTILES ----------------
        for p in projectiles:
            p.update(dt)
        projectiles = [p for p in projectiles if p.alive()]

        # ---------------- COLLISIONS ----------------
        boss_rect = pygame.Rect(
            state["boss_pos"].x - BOSS_SIZE // 2,
            state["boss_pos"].y - BOSS_SIZE // 2,
            BOSS_SIZE,
            BOSS_SIZE
        )

        # Player touching boss
        if circle_rect_collision(state["player_pos"], PLAYER_RADIUS, boss_rect):
            damage_player(state["boss_pos"])

        # Player hit by projectile
        for p in projectiles:
            if p.rect.collidepoint(state["player_pos"]):
                damage_player(p.pos)

        # Sword → Boss (only one hit per swing)
        if state["sword_active"] and (not state["sword_hit_this_swing"]):
            progress = 1 - (state["sword_timer"] / SWORD_TIME)
            angle = -SWORD_ARC_DEG / 2 + progress * SWORD_ARC_DEG
            d = state["facing"].rotate(angle)
            tip = state["player_pos"] + d * SWORD_RANGE

            if boss_rect.collidepoint(tip):
                damage_boss(state["boss_pos"])
                state["sword_hit_this_swing"] = True

        # ---------------- BOSS DAMAGE FLASH UPDATE ----------------
        if state["boss_flashes_left"] > 0:
            state["boss_flash_timer"] += dt
            if state["boss_flash_timer"] >= state["boss_flash_interval"]:
                state["boss_flash_timer"] = 0.0

                # Toggle flash on/off
                state["boss_flash_on"] = not state["boss_flash_on"]

                # Count a flash when we finish a red "on" cycle
                if state["boss_flash_on"] is False:
                    state["boss_flashes_left"] -= 1

        # ---------------- WIN / LOSE CHECKS ----------------
        if state["boss_hp"] <= 0:
            game_over = True
            game_result = "WIN"

        if state["player_hp"] <= 0:
            game_over = True
            game_result = "LOSE"

    # =================================================
    # DRAW (always runs)
    # =================================================
    screen.fill(BG_COLOR)

    boss_rect_draw = pygame.Rect(
        state["boss_pos"].x - BOSS_SIZE // 2,
        state["boss_pos"].y - BOSS_SIZE // 2,
        BOSS_SIZE,
        BOSS_SIZE
    )

    # Boss color (telegraph + damage flash)
    boss_color = BOSS_BASE_COLOR


    # Telegraph overrides base boss color (yellow / light blue)
    if state["boss_state"] == "telegraph":
        if int(state["telegraph_timer"] / BLINK_RATE) % 2 == 0:
            boss_color = (
                BOSS_TELEGRAPH_BLUE
                if state["pattern_index"] == 0
                else BOSS_TELEGRAPH_YELLOW
            )

    # Damage flash: blink red 3 times
    if state["boss_flashes_left"] > 0 and state["boss_flash_on"]:
        boss_color = (255, 40, 40)


    pygame.draw.rect(screen, boss_color, boss_rect_draw)

    # Sword afterimages
    for a in state["afterimages"]:
        t = a["time"] / SWORD_AFTERIMAGE_TIME
        ang = -SWORD_ARC_DEG / 2 + a["progress"] * SWORD_ARC_DEG
        d = state["facing"].rotate(ang)
        pygame.draw.line(
            screen,
            (255, 255, 255, int(160 * t)),
            state["player_pos"],
            state["player_pos"] + d * SWORD_RANGE,
            3
        )

    # Active sword
    if state["sword_active"]:
        progress = 1 - (state["sword_timer"] / SWORD_TIME)
        ang = -SWORD_ARC_DEG / 2 + progress * SWORD_ARC_DEG
        d = state["facing"].rotate(ang)
        pygame.draw.line(
            screen,
            (255, 255, 255),
            state["player_pos"],
            state["player_pos"] + d * SWORD_RANGE,
            5
        )

    # Player (invuln flash)
    if state["invuln"] <= 0 or int(state["invuln"] * 10) % 2 == 0:
        pygame.draw.circle(screen, PLAYER_COLOR, state["player_pos"], PLAYER_RADIUS)


    # Projectiles
    for p in projectiles:
        p.draw(screen)

    # UI
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render(f"Player HP: {state['player_hp']}", True, UI_TEXT_COLOR), (10, 10))
    screen.blit(font.render(f"Boss HP: {state['boss_hp']}", True, UI_TEXT_COLOR), (10, 32))

    # Game Over Text
    if game_over:
        big = pygame.font.SysFont(None, 72)
        msg = "YOU WIN!" if game_result == "WIN" else "YOU LOSE!"
        text = big.render(msg, True, (240, 240, 240))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)

        small = pygame.font.SysFont(None, 28)
        sub = small.render("Close the window to exit.", True, (200, 200, 200))
        sub_rect = sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55))
        screen.blit(sub, sub_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()
