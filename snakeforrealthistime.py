# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 18:27:13 2026

@author: Tyler
"""
#for giant snake boss
#for shadow clone boss
#can you think of something like red rover?  assuming the snake doesn't vibrate, just people move at you in a marching line?  maybe they also encircle you and try to poke you.


#movement states
#*idle
#*chase
#*patrol
#*stunned
#*enraged

import numpy as np
import pygame
import math
import sys

# =========================
# CONFIG
# =========================

WIDTH, HEIGHT = 1200, 1200
BACKGROUND = (15, 15, 25)
PLAYER_COLOR = (80, 200, 255)
BOSS_COLOR = (220, 120, 120)
SPRING_COLOR = (255, 180, 180)

PLAYER_SPEED = 350

NUM_NODES = 10
NODE_RADIUS = 48
#==========================================================
#this is supposed to be the sin waves that the boss follows.
#==========================================================
def generate_sine_edge(p0, p1, samples=25, amplitude=1, cycles=5, y_middle=None):
    x0, y0 = p0
    x1, y1 = p1

    length = math.hypot(x1 - x0, y1 - y0)
    angle = math.atan2(y1 - y0, x1 - x0)

    xs = np.linspace(0, length, samples)
    
    # Baseline
    if y_middle is None:
        y_middle = (y0 + y1) / 2

    frequency = cycles * 2 * math.pi / length
    ys = y_middle + amplitude * np.sin(frequency * xs)

    points = []
    for x, y in zip(xs, ys):
        dx = x
        dy = y - y_middle
        wx = dx * math.cos(angle) - dy * math.sin(angle) + x0
        wy = dx * math.sin(angle) + dy * math.cos(angle) + y0  # use y0
        points.append((wx, wy))

    return points
# =========================
# CURVE FOLLOWER
# =========================
class CurveFollower:
    def __init__(self, points, speed=400):
        self.points = points
        self.speed = speed
        self.index = 0
        self.pos = list(points[0])

    def update(self, dt):
        if self.index >= len(self.points) - 1:
            return

        x, y = self.pos
        tx, ty = self.points[self.index + 1]

        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)

        if dist < 1e-3:
            self.index += 1
            return

        step = self.speed * dt
        if step >= dist:
            self.pos[0], self.pos[1] = tx, ty
            self.index += 1
        else:
            self.pos[0] += dx / dist * step
            self.pos[1] += dy / dist * step



# =========================
# ELASTIC CHAIN CLASS
# =========================


class ElasticChain:

    def __init__(self, anchor_pos):

        self.nodes = []
        self.velocities = []
        # ---- per-node mass & size gradient ----
        self.masses = []
        self.radii = []
        # ---- HP SYSTEM ----
        self.node_max_hp = []
        self.node_hp = []
        
        base_hp = 120    # head is tougher
        tip_hp = 30      # tail is fragile
        
        for i in range(NUM_NODES):
            t = 1.0 - i / (NUM_NODES - 1)  # head-heavy
            hp = int(base_hp * (1 - t) + tip_hp * t)
            self.node_max_hp.append(hp)
            self.node_hp.append(hp)
        
        self.total_hp = sum(self.node_hp)
        self.max_total_hp = self.total_hp
        
        base_mass = 8.0      # heavy root
        tip_mass = 1.5       # light tip
        
        base_radius = NODE_RADIUS
        tip_radius = int(NODE_RADIUS * 0.4)
        
        for i in range(NUM_NODES):
            t = 1.0 - i / (NUM_NODES - 1)
        
            mass = base_mass * (1 - t) + tip_mass * t
            radius = int(base_radius * (1 - t) + tip_radius * t)
        
            self.masses.append(mass)
            self.radii.append(radius)

        self.spacing_scale = 1.0

        spacing = .25

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
        # STATE MACHINE
        # -------------------------
        self.state = "idle"
        self.state_time = 0.0
        self.stiffness_scale = 1.0

    # -------------------------
    # STATE METHODS
    # -------------------------
    def _enter_idle(self):
        self.state = "idle"
        self.state_time = 0.0
        self.spacing_scale = 1.0
        self.stiffness_scale = 1.0
        self.base_stiffness = 20.0
        self.poisson_ratio = 0.4
        self.damping = 0.8

    def _enter_expanded(self):
        self.state = "expanded"
        self.state_time = 0.0
        self.spacing_scale = 5.0
        self.stiffness_scale = 0.7
        self.base_stiffness = 14.0
        self.poisson_ratio = 0.4
        self.damping = 0.85

    def _enter_rigid(self):
        self.state = "rigid"
        self.state_time = 0.0
        self.spacing_scale = 10
        self.stiffness_scale = 1.0
        self.base_stiffness = 14.0
        self.poisson_ratio = 0.8
        self.damping = 0.8
        
    # -------------------------
    # DAMAGE METHOD
    # -------------------------
        
    def damage_node(self, i, amount):
        if i < 0 or i >= NUM_NODES:
            return
        if self.node_hp[i] <= 0:
            return
    
        dmg = min(amount, self.node_hp[i])
    
        self.node_hp[i] -= dmg
        self.total_hp -= dmg
    
        if self.total_hp < 0:
            self.total_hp = 0

    # -------------------------
    # UPDATE PHYSICS
    # -------------------------
    def update(self, anchor_pos, dt):
        self.state_time += dt

        # -------------------------
        # STATE TRANSITIONS
        # -------------------------
        if self.state == "idle" and self.state_time > 10.0:
            self._enter_expanded()
        elif self.state == "expanded" and self.state_time > 20.0:
            self._enter_rigid()

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

            rest = self.rest_lengths[i] * self.spacing_scale
            strain = (L - rest) / rest
            stiffness = self.base_stiffness * self.stiffness_scale * (1 + self.poisson_ratio * abs(strain))
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
            ax = forces[i][0] / self.masses[i]
            ay = forces[i][1] / self.masses[i]

            vx += ax * dt
            vy += ay * dt
            
            # -----------------------------
            # Tail whip amplification
            # -----------------------------
            # heavier nodes damp more
            # lighter nodes lose less energy (appear amplified)
            mass_ratio = self.masses[i] / max(self.masses)
            mass_ratio = max(0.2, min(1.0, mass_ratio))
            
            local_damping = self.damping ** mass_ratio
            
            vx *= local_damping
            vy *= local_damping

            x, y = self.nodes[i]
            x += vx * dt
            y += vy * dt
            self.nodes[i] = (x, y)
            self.velocities[i] = [vx, vy]

    # -------------------------
    # DRAW
    # -------------------------
    def draw(self, screen):

        base_thickness = 6  # visual rest thickness
    
        # ---- draw edges ----
        for i in range(NUM_NODES - 1):
            x0, y0 = self.nodes[i]
            x1, y1 = self.nodes[i + 1]
    
            dx = x1 - x0
            dy = y1 - y0
            L = math.hypot(dx, dy)
            rest = self.rest_lengths[i] * self.spacing_scale
    
            if rest <= 0:
                continue
    
            strain = (L - rest) / rest
    
            # -----------------------------
            # Poisson thickness response
            # -----------------------------
            # thickness ∝ 1 − ν·strain
            poisson = self.poisson_ratio
            thickness_factor = 1 - poisson * strain
    
            # clamp so it never vanishes or explodes
            thickness_factor = max(5, min(10, thickness_factor))
    
            thickness = max(40, int(base_thickness * (1 - poisson * strain)))
    
            # -----------------------------
            # Color for readability
            # -----------------------------
            if strain > 0:
                # tension → red
                hot = min(255, int(120 + 300 * strain))
                color = (255, hot, hot)
            else:
                # compression → pale / gray
                fade = max(60, int(160 + 200 * strain))
                color = (fade, fade, fade)
            # --- SAFETY CHECK ---
            if not all(map(math.isfinite, (x0, y0, x1, y1))):
                continue
            pygame.draw.line(
                screen,
                color,
                (int(x0), int(y0)),
                (int(x1), int(y1)),
                thickness
            )
    
        # ---- draw nodes ----
        for i, (x, y) in enumerate(self.nodes):
            t = i / (NUM_NODES - 1)
            color = (
                int(255 * t),
                int(100 * (1 - t)),
                int(255 * (1 - t))
                )
            pygame.draw.circle(
            screen,
            color,
            (int(x), int(y)),
            self.radii[i]
        )

               


# =========================
# MAIN
# =========================

def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("OOP Elastic Chain")
    clock = pygame.time.Clock()
    
    node_a = (100, 500)
    node_b = (700, 100)
    node_c = (300,500)
    
    sine_forward = generate_sine_edge(
        node_a,
        node_b,
        node_c,
        samples=50,
        amplitude=10,
        cycles=6
    )

    sine_backward = generate_sine_edge(
        node_b,
        node_a,
        node_c,
        samples=10,
        amplitude=-10,   # <<< KEY: inverted sine
        cycles=6
    )

    boss_path = CurveFollower(sine_forward, speed=400)
    current_path = "forward"

    boss_path = CurveFollower(sine_forward, speed=400)
    chain = ElasticChain(boss_path.pos)


    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        boss_path.update(dt)

    # --- switch paths when finished ---
        if boss_path.index >= len(boss_path.points) - 1:
            if current_path == "forward":
                boss_path = CurveFollower(sine_backward, speed=1500)
                current_path = "backward"
            else:
                boss_path = CurveFollower(sine_forward, speed=300)
                current_path = "forward"

        chain.update(tuple(boss_path.pos), dt)
        screen.fill(BACKGROUND)

        # Draw graph
        pygame.draw.circle(screen, PLAYER_COLOR, node_a, 0)
        pygame.draw.circle(screen, PLAYER_COLOR, node_b, 0)

        for p in sine_forward[::10]:
            pygame.draw.circle(screen, (80, 80, 120), (int(p[0]), int(p[1])), 0)

        chain.draw(screen)

        pygame.draw.circle(
            screen,
            BOSS_COLOR,
            (int(boss_path.pos[0]), int(boss_path.pos[1])),
            8
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()