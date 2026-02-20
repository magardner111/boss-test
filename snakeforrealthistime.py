# -*- coding: utf-8 -*-
"""
================================================================================
ELASTIC SNAKE BOSS - Educational Version with Amazing Comments!
================================================================================
Created on Thu Feb 12 18:27:13 2026
@author: Tyler

This program teaches you Object-Oriented Programming (OOP) while creating
a cool elastic snake boss that moves along a wavy path!

================================================================================
WHAT YOU'LL LEARN FROM THIS CODE:
================================================================================
1. CLASSES: How to bundle data and functions together (like a blueprint)
2. OBJECTS: How to create instances from classes (like building from blueprint)
3. METHODS: Functions that belong to a class (the things objects can do)
4. __init__: The "constructor" that sets up a new object
5. self: How objects refer to their own data
6. ENCAPSULATION: Keeping related data and functions together

================================================================================
HOW TO ADD MORE NODES:
================================================================================
1. Scroll down to the CONFIG section (around line 50)
2. Change NUM_NODES = 10 to whatever you want (try 20, 30, 50!)
3. Run the program - that's it!

The snake automatically:
- Creates a gradient from heavy head → light tail
- Adds HP that decreases from head → tail
- Makes the head big and tail small
- Creates physics springs between all nodes

Boss States (automatic transitions):
- idle: normal movement (0-10 seconds)
- expanded: snake stretches out (10-20 seconds)
- rigid: snake becomes stiffer (20+ seconds)

Movement States (planned for future):
- chase, patrol, stunned, enraged
"""

# ================================================================================
# IMPORTS - Libraries we need
# ================================================================================
# These are like toolboxes we're borrowing to make our game easier to build

import numpy as np    # Math library for arrays and calculations
import pygame         # Game library for graphics and window management
import math           # Standard Python math (sin, cos, distance calculations)
import sys            # System library (for exiting the program cleanly)

# =========================
# CONFIG - EASY SETTINGS FOR YOUR FRIEND
# =========================

WIDTH, HEIGHT = 1200, 1200
BACKGROUND = (15, 15, 25)
PLAYER_COLOR = (80, 200, 255)
BOSS_COLOR = (220, 120, 120)
SPRING_COLOR = (255, 180, 180)

PLAYER_SPEED = 350

# ==========================================
# CHANGE THIS NUMBER TO ADD MORE NODES!
# Try: 10, 20, 30, 50, etc.
# More nodes = longer snake boss
# ==========================================
NUM_NODES = 10

# Head and tail sizes (gradient is automatic)
NODE_RADIUS = 48  # Head size
NODE_RADIUS_TIP = 19  # Tail size (auto-calculated as 40% of head if not set)

# HP values (gradient is automatic from head to tail)
HEAD_HP = 120  # Tough head
TAIL_HP = 30   # Fragile tail

# Mass values (gradient is automatic)
HEAD_MASS = 8.0   # Heavy head
TAIL_MASS = 1.5   # Light tail for whip effect

# =========================
# QUICK START GUIDE
# =========================
# Want 20 nodes? → Set NUM_NODES = 20
# Want bigger head? → Increase NODE_RADIUS
# Want tougher boss? → Increase HEAD_HP and TAIL_HP
# Want more whip action? → Decrease TAIL_MASS
# =========================

# ================================================================================
# REGULAR FUNCTION (not part of a class)
# This creates a wavy path between two points for the boss to follow
# ================================================================================
def generate_sine_edge(p0, p1, samples=25, amplitude=1, cycles=5, y_middle=None):
    """
    Creates a sine wave path between two points.

    Think of it like drawing a wiggly line from point A to point B!

    PARAMETERS (the inputs):
    - p0: Starting point (x, y) - where the path begins
    - p1: Ending point (x, y) - where the path ends
    - samples: How many points to create along the path (more = smoother)
    - amplitude: How "tall" the waves are (bigger = more wiggly)
    - cycles: How many complete waves from start to finish
    - y_middle: Optional middle line (calculated automatically if not provided)

    RETURNS:
    - A list of (x, y) coordinates forming a wavy path

    VISUAL EXAMPLE:
    p0 ~~~^~~~v~~~^~~~ p1
       (sine wave path)
    """

    # Step 1: Extract coordinates from the points
    x0, y0 = p0  # Unpack tuple: p0 = (100, 200) → x0=100, y0=200
    x1, y1 = p1  # Same for endpoint

    # Step 2: Calculate distance and angle between points
    length = math.hypot(x1 - x0, y1 - y0)  # hypot = sqrt(dx² + dy²) = distance
    angle = math.atan2(y1 - y0, x1 - x0)   # atan2 = angle in radians

    # Step 3: Create evenly spaced points along the line
    xs = np.linspace(0, length, samples)  # Creates 'samples' numbers from 0 to length
                                           # Example: linspace(0, 100, 5) → [0, 25, 50, 75, 100]

    # Step 4: Calculate middle line for the sine wave
    if y_middle is None:
        y_middle = (y0 + y1) / 2  # Default: use the middle between start and end

    # Step 5: Create the sine wave pattern
    frequency = cycles * 2 * math.pi / length  # How "squished" the waves are
    ys = y_middle + amplitude * np.sin(frequency * xs)  # Apply sine to all points
    # This creates: [middle, middle+wave1, middle+wave2, ...]

    # Step 6: Rotate the sine wave to match the angle between p0 and p1
    # (Because our wave might not be horizontal!)
    points = []
    for x, y in zip(xs, ys):  # zip combines lists: zip([1,2], [3,4]) → [(1,3), (2,4)]
        dx = x
        dy = y - y_middle
        # Rotation math (don't worry too much about this part - it's just trigonometry)
        wx = dx * math.cos(angle) - dy * math.sin(angle) + x0
        wy = dx * math.sin(angle) + dy * math.cos(angle) + y0
        points.append((wx, wy))  # Add rotated point to our list

    return points  # Give back the list of coordinates
# ================================================================================
# YOUR FIRST CLASS! - CurveFollower
# ================================================================================
# A CLASS is like a blueprint for creating objects.
# Think of it like a recipe: the recipe is the class, the cake you bake is the object!
#
# WHY USE CLASSES?
# Instead of having separate variables like:
#   boss_points, boss_speed, boss_index, boss_pos
# We bundle them together in ONE object:
#   boss.points, boss.speed, boss.index, boss.pos
#
# This keeps related data organized and easier to manage!
# ================================================================================

class CurveFollower:
    """
    This class makes an object that can follow a curved path smoothly.

    ANALOGY: Think of this like a train following tracks!
    - The train (object) has a position and speed
    - The tracks (points) tell it where to go
    - It moves smoothly from one point to the next

    REAL-WORLD USE: Our boss follows this path to move in interesting patterns
    """

    # ============================================================================
    # __init__ is the CONSTRUCTOR (the "builder" method)
    # ============================================================================
    # This runs ONCE when you create a new CurveFollower object
    # Example: my_follower = CurveFollower(path_points, speed=500)
    #
    # WHAT IS "self"?
    # - "self" refers to THIS SPECIFIC OBJECT (like saying "me" or "my")
    # - self.speed means "MY speed" (this object's speed)
    # - It's how the object stores its own data
    # ============================================================================

    def __init__(self, points, speed=400):
        """
        Initialize (set up) a new CurveFollower object.

        PARAMETERS:
        - self: The object itself (Python adds this automatically)
        - points: List of (x,y) coordinates to follow
        - speed: How fast to move (pixels per second)
        """
        # Save the path this follower will travel
        self.points = points  # "self.points" means "THIS object's points"

        # Save the speed
        self.speed = speed  # "THIS object's speed"

        # Track which point we're currently moving toward
        self.index = 0  # Start at point 0

        # Current position (copy the first point)
        self.pos = list(points[0])  # list() makes a copy so we can modify it
        # Why list()? Because tuples like (100, 200) can't be changed,
        # but lists like [100, 200] can be updated as we move!

    # ============================================================================
    # update is a METHOD (a function that belongs to this class)
    # ============================================================================
    # Methods are like actions the object can perform
    # Example: my_follower.update(0.016) means "move forward a tiny bit"
    # ============================================================================

    def update(self, dt):
        """
        Move along the path toward the next point.

        PARAMETERS:
        - self: The object itself (always first parameter in methods!)
        - dt: "delta time" = time since last update (in seconds)
              Example: if running at 60 FPS, dt ≈ 0.0166 seconds

        This method gets called every frame to smoothly move the follower.
        """

        # Check if we've reached the end of the path
        if self.index >= len(self.points) - 1:
            return  # Stop moving if we're at the last point

        # Get our current position
        x, y = self.pos  # Unpack: self.pos = [150, 200] → x=150, y=200

        # Get the target point we're moving toward
        tx, ty = self.points[self.index + 1]  # "t" for "target"

        # Calculate direction to target
        dx = tx - x  # Horizontal distance to target
        dy = ty - y  # Vertical distance to target
        dist = math.hypot(dx, dy)  # Total distance using Pythagorean theorem

        # If we're basically at the target, move to next point
        if dist < 1e-3:  # 1e-3 means 0.001 (very small number)
            self.index += 1  # Advance to next point in path
            return

        # Calculate how far we can move this frame
        step = self.speed * dt  # Example: 400 pixels/sec * 0.0166 sec = 6.6 pixels

        # Check if we'll reach the target this frame
        if step >= dist:
            # We'll overshoot, so just move directly to target
            self.pos[0], self.pos[1] = tx, ty
            self.index += 1  # Move to next point
        else:
            # Move partway toward target
            # We move in the direction (dx, dy) but normalized (made length 1)
            self.pos[0] += dx / dist * step  # Move X by the right amount
            self.pos[1] += dy / dist * step  # Move Y by the right amount
            # Why "/ dist"? To normalize: if dx=30 and dist=50,
            # then dx/dist = 0.6, which is the X direction component



# ================================================================================
# THE BIG CLASS! - ElasticChain (The Snake Boss)
# ================================================================================
# This is our most complex class! It handles:
# - Multiple connected nodes (the snake segments)
# - Physics simulation (springs, forces, movement)
# - Health system (damage tracking)
# - Visual appearance (colors, sizes)
# - State management (idle, expanded, rigid modes)
#
# WHY IS THIS CLASS SO USEFUL?
# Imagine trying to manage 50 nodes without a class:
#   node0_x, node0_y, node0_vx, node0_vy, node0_hp, node0_mass, node0_radius...
#   node1_x, node1_y, node1_vx, node1_vy, node1_hp, node1_mass, node1_radius...
#   ... (times 50!)
#
# With a class, we just do: snake.nodes, snake.velocities, snake.hp
# ALL organized in one object! Much cleaner!
#
# VISUAL DIAGRAM:
#   Node0 ===spring=== Node1 ===spring=== Node2 ===spring=== ... ===spring=== Node9
#   (head)                                                                      (tail)
#    Big                                                                         Small
#   Heavy                                                                        Light
#   120 HP                                                                       30 HP
# ================================================================================

class ElasticChain:
    """
    The snake boss! A chain of connected nodes with elastic physics.

    Each node is connected to the next by an invisible "spring".
    When you pull the head, the body follows with realistic physics!

    PHYSICS CONCEPTS:
    - Springs: Like rubber bands connecting the nodes
    - Mass: Heavier nodes move slower, lighter nodes move faster
    - Damping: Friction that slows things down
    - Forces: Springs pull/push nodes to keep them connected
    """

    # ============================================================================
    # __init__ = CONSTRUCTOR (The setup method)
    # ============================================================================
    # This runs ONCE when you create a new ElasticChain
    # Example: my_snake = ElasticChain((400, 300))
    # ============================================================================

    def __init__(self, anchor_pos):
        """
        Build a new elastic snake!

        PARAMETERS:
        - anchor_pos: Where to place the snake's tail initially (x, y)

        This method creates all the nodes, sets their properties, and
        connects them with springs.
        """

        # ========================================================================
        # STEP 1: Create empty lists to store data for each node
        # ========================================================================
        # We use LISTS because we have multiple nodes (10 by default)
        # Lists are like containers: my_list = [item1, item2, item3]

        self.nodes = []       # Will store positions: [(x0,y0), (x1,y1), ...]
        self.velocities = []  # Will store speeds: [[vx0,vy0], [vx1,vy1], ...]

        # Each node has different properties (gradients from head to tail):
        self.masses = []      # Weight of each node [8.0, 7.3, 6.6, ..., 1.5]
        self.radii = []       # Visual size [48, 45, 42, ..., 19]

        # HP (Health Points) system - each node can take damage!
        self.node_max_hp = [] # Maximum HP each node can have
        self.node_hp = []     # Current HP (starts at maximum)

        # ========================================================================
        # STEP 2: Calculate HP for each node (gradient from head to tail)
        # ========================================================================
        # GRADIENT means smoothly changing from one value to another
        # Head (node 0): tough (120 HP)
        # Middle nodes: medium HP
        # Tail (last node): fragile (30 HP)

        for i in range(NUM_NODES):
            # Calculate gradient position: t goes from 0 (head) to 1 (tail)
            # Example with 10 nodes:
            #   i=0: t = 1.0 - 0/9 = 1.0 (head)
            #   i=5: t = 1.0 - 5/9 = 0.44 (middle)
            #   i=9: t = 1.0 - 9/9 = 0.0 (tail)
            t = 1.0 - i / (NUM_NODES - 1) if NUM_NODES > 1 else 0

            # Linear interpolation (lerp): blend between two values
            # Formula: result = start * (1-t) + end * t
            # When t=1 (head): hp = HEAD_HP * 1 + TAIL_HP * 0 = 120
            # When t=0 (tail): hp = HEAD_HP * 0 + TAIL_HP * 1 = 30
            hp = int(HEAD_HP * (1 - t) + TAIL_HP * t)

            self.node_max_hp.append(hp)  # Save maximum HP
            self.node_hp.append(hp)      # Current HP starts at max

        # Calculate total HP for the whole snake
        self.total_hp = sum(self.node_hp)  # sum([120, 107, ..., 30]) = total
        self.max_total_hp = self.total_hp   # Remember starting total

        # ========================================================================
        # STEP 3: Create mass gradient (heavy head → light tail)
        # ========================================================================
        # WHY? Heavy head = stable, light tail = whips around dramatically!
        base_mass = HEAD_MASS   # 8.0 for head
        tip_mass = TAIL_MASS    # 1.5 for tail

        # ========================================================================
        # STEP 4: Create size gradient (big head → small tail)
        # ========================================================================
        # The head should look bigger and more intimidating!
        base_radius = NODE_RADIUS  # 48 pixels for head
        tip_radius = int(NODE_RADIUS * 0.4) if 'NODE_RADIUS_TIP' not in globals() else NODE_RADIUS_TIP

        # Loop through all nodes and calculate their mass and size
        for i in range(NUM_NODES):
            t = 1.0 - i / (NUM_NODES - 1)  # Same gradient calculation as HP

            # Blend between head and tail values
            mass = base_mass * (1 - t) + tip_mass * t
            radius = int(base_radius * (1 - t) + tip_radius * t)

            self.masses.append(mass)    # Save this node's mass
            self.radii.append(radius)   # Save this node's visual size

        # ========================================================================
        # STEP 5: Create initial positions for all nodes
        # ========================================================================
        self.spacing_scale = 1.0  # Can be changed later to stretch/compress snake

        spacing = .25  # How far apart nodes start (very small = compact)

        # Place nodes in a horizontal line
        for i in range(NUM_NODES):
            # Start from anchor and spread left
            x = anchor_pos[0] - spacing * (NUM_NODES - i)
            y = anchor_pos[1]
            self.nodes.append((x, y))           # Add position
            self.velocities.append([0.0, 0.0])  # Start not moving

        # ========================================================================
        # STEP 6: Calculate rest lengths (natural spring lengths)
        # ========================================================================
        # Each spring connecting two nodes has a "rest length" = how long it
        # "wants" to be. If stretched or compressed, it pulls back to this length!

        self.rest_lengths = []
        for i in range(NUM_NODES - 1):  # One less spring than nodes
            # Calculate distance between this node and next node
            dx = self.nodes[i + 1][0] - self.nodes[i][0]
            dy = self.nodes[i + 1][1] - self.nodes[i][1]
            self.rest_lengths.append(math.hypot(dx, dy))  # Save distance

        # ========================================================================
        # STEP 7: Set physics parameters
        # ========================================================================
        self.base_stiffness = 20.0  # How "tight" the springs are (higher = stiffer)
        self.poisson_ratio = 0.4    # Physics: affects thickness when stretched
        self.damping = 0.8          # Friction: how quickly motion slows down (0-1)
        self.mass = 5.0             # Legacy parameter (individual masses used now)

        # ========================================================================
        # STEP 8: Initialize state machine
        # ========================================================================
        # STATE MACHINE: the snake can be in different "modes" that change behavior
        self.state = "idle"           # Current mode: "idle", "expanded", or "rigid"
        self.state_time = 0.0         # How long we've been in this state
        self.stiffness_scale = 1.0    # Multiplier for spring stiffness

    # ============================================================================
    # STATE TRANSITION METHODS
    # ============================================================================
    # These methods change the snake's behavior mode
    # Think of it like a boss having different "phases" in a video game!
    #
    # Each state has different physics properties that make the snake move
    # and look different. The state automatically transitions over time.
    #
    # NAMING CONVENTION: Methods starting with _ (underscore) are "private"
    # This means they're meant to be used inside the class, not from outside
    # ============================================================================

    def _enter_idle(self):
        """
        Enter the IDLE state - normal relaxed movement.

        This is the starting state. The snake moves smoothly with:
        - Normal spacing between nodes
        - Medium stiffness (not too loose, not too tight)
        - Standard damping (friction)

        VISUAL: The snake looks natural and flows smoothly
        """
        self.state = "idle"              # Set state name
        self.state_time = 0.0            # Reset timer (how long in this state)

        # Physics parameters for idle state
        self.spacing_scale = 1.0         # Normal spacing (100% of rest length)
        self.stiffness_scale = 1.0       # Normal spring stiffness multiplier
        self.base_stiffness = 20.0       # How tight the springs are
        self.poisson_ratio = 0.4         # Material property (medium thickness change)
        self.damping = 0.8               # Energy loss (0=no friction, 1=instant stop)

    def _enter_expanded(self):
        """
        Enter the EXPANDED state - snake stretches out dramatically!

        After 10 seconds of idle, the snake expands. Changes:
        - Spacing increases 5× (snake stretches way out!)
        - Springs become looser (less stiff)
        - Slightly more damping (moves more smoothly)

        VISUAL: The snake elongates and becomes more flexible/wobbly
        GAMEPLAY: This could make the boss more vulnerable (spread out)
        """
        self.state = "expanded"          # Set state name
        self.state_time = 0.0            # Reset timer

        # Physics parameters for expanded state
        self.spacing_scale = 5.0         # 5× spacing = MUCH longer snake!
        self.stiffness_scale = 0.7       # 70% stiffness = looser/floppier
        self.base_stiffness = 14.0       # Lower base stiffness
        self.poisson_ratio = 0.4         # Same material property
        self.damping = 0.85              # Slightly more damping (smoother movement)

    def _enter_rigid(self):
        """
        Enter the RIGID state - snake becomes stiff and stretched!

        After 20 seconds total, the snake becomes rigid. Changes:
        - Spacing increases 10× (extremely stretched!)
        - Springs are normal stiffness (but stretched far)
        - Higher Poisson ratio (dramatic thickness changes)

        VISUAL: The snake looks tense and stretched tight
        GAMEPLAY: This could be a "danger phase" where it's harder to dodge
        """
        self.state = "rigid"             # Set state name
        self.state_time = 0.0            # Reset timer

        # Physics parameters for rigid state
        self.spacing_scale = 10          # 10× spacing = VERY stretched!
        self.stiffness_scale = 1.0       # Normal stiffness multiplier
        self.base_stiffness = 14.0       # Lower base (but stretched far = still tense)
        self.poisson_ratio = 0.8         # High Poisson = thickness changes a lot
        self.damping = 0.8               # Normal damping

    # ============================================================================
    # DAMAGE METHOD - Health system (for future combat features)
    # ============================================================================
    # This method handles damaging individual nodes of the snake
    # Each node has its own HP, and you can target specific segments!
    #
    # GAME DESIGN NOTE:
    # - Head has high HP (tough to destroy)
    # - Tail has low HP (vulnerable)
    # - Player could strategically target weak points!
    # ============================================================================

    def damage_node(self, i, amount):
        """
        Apply damage to a specific node of the snake.

        PARAMETERS:
        - i: Index of the node to damage (0=head, NUM_NODES-1=tail)
        - amount: How much damage to apply (HP to subtract)

        RETURNS:
        - Nothing (modifies self.node_hp and self.total_hp in place)

        USAGE EXAMPLE:
        chain.damage_node(0, 10)  # Deal 10 damage to the head
        chain.damage_node(9, 50)  # Deal 50 damage to the tail (overkill if HP<50)

        NOTE: This method is set up for future features but not currently used
        """

        # ========================================================================
        # Validation checks
        # ========================================================================

        # Check if node index is valid (must be 0 to NUM_NODES-1)
        if i < 0 or i >= NUM_NODES:
            return  # Invalid index, do nothing
            # Example: If NUM_NODES=10, valid indices are 0-9

        # Check if node is already dead (HP already at 0)
        if self.node_hp[i] <= 0:
            return  # Already dead, can't damage it more

        # ========================================================================
        # Calculate and apply damage
        # ========================================================================

        # Don't deal more damage than the node has HP
        # Example: Node has 30 HP, amount=50 → actual damage = min(50, 30) = 30
        dmg = min(amount, self.node_hp[i])

        # Subtract damage from this node's HP
        self.node_hp[i] -= dmg

        # Subtract damage from total HP (sum of all nodes)
        self.total_hp -= dmg

        # Ensure total HP never goes below 0 (prevent negative HP)
        if self.total_hp < 0:
            self.total_hp = 0

        # ========================================================================
        # Future enhancements could add:
        # ========================================================================
        # - Visual effects when damaged (flash red, particle effects)
        # - Remove nodes when HP reaches 0 (snake gets shorter!)
        # - Different behavior based on damage (enrage when low HP)
        # - Sound effects for damage
        # - Damage numbers floating up from the hit location

    # ============================================================================
    # UPDATE PHYSICS - The heart of the simulation!
    # ============================================================================
    # This method runs every frame to update the snake's position and movement
    # Think of it like a flip-book animation - each frame we:
    #   1. Calculate forces (springs pulling/pushing)
    #   2. Update velocities (how fast things move)
    #   3. Update positions (where things are)
    # ============================================================================

    def update(self, anchor_pos, dt):
        """
        Update the snake's physics simulation for one frame.

        PARAMETERS:
        - anchor_pos: Where the tail should be attached (follows the path)
        - dt: Delta time - how much time has passed since last frame (seconds)

        WHAT THIS METHOD DOES:
        1. Updates state timer (for automatic state changes)
        2. Checks if we should transition to a new state
        3. Pins the tail to the anchor point
        4. Calculates spring forces between all nodes
        5. Updates velocities and positions using physics
        """

        # ========================================================================
        # STEP 1: Update state timer
        # ========================================================================
        # Track how long we've been in the current state
        self.state_time += dt  # Add elapsed time (example: 0.016 seconds per frame)

        # ========================================================================
        # STEP 2: Check for automatic state transitions
        # ========================================================================
        # The snake automatically changes behavior over time!
        # This creates varied, interesting movement patterns

        if self.state == "idle" and self.state_time > 10.0:
            # After 10 seconds of idle, switch to expanded
            self._enter_expanded()
        elif self.state == "expanded" and self.state_time > 20.0:
            # After 20 seconds total, switch to rigid
            self._enter_rigid()

        # ========================================================================
        # STEP 3: Pin the tail to the anchor point
        # ========================================================================
        # "Kinematic" means this node is controlled directly, not by physics
        # The last node (tail) follows the path - it's our anchor point

        self.nodes[-1] = anchor_pos           # Set tail position ([-1] = last item)
        self.velocities[-1] = [0.0, 0.0]      # Tail has no velocity (it's pinned!)

        # ========================================================================
        # STEP 4: Create empty force list
        # ========================================================================
        # Forces are pushes/pulls that will affect each node
        # Start with zero force on each node, then add spring forces

        forces = [[0.0, 0.0] for _ in range(NUM_NODES)]
        # This creates: [[0,0], [0,0], [0,0], ...] one for each node
        # Each [0,0] represents force in X and Y directions

        # ========================================================================
        # STEP 5: Calculate spring forces between connected nodes
        # ========================================================================
        # SPRING PHYSICS EXPLANATION:
        # Imagine a rubber band connecting two nodes:
        # - If stretched → pulls nodes together
        # - If compressed → pushes nodes apart
        # - The further from "rest length", the stronger the force!
        #
        # Formula: Force = stiffness × distance_from_rest
        # Direction: Always toward equilibrium (rest length)

        for i in range(NUM_NODES - 1):  # For each spring (one less than nodes)
            # ----------------------------------------------------------------
            # Get positions of the two nodes this spring connects
            # ----------------------------------------------------------------
            x0, y0 = self.nodes[i]      # Current node position
            x1, y1 = self.nodes[i + 1]  # Next node position

            # ----------------------------------------------------------------
            # Calculate current distance between nodes
            # ----------------------------------------------------------------
            dx = x1 - x0                    # Horizontal distance
            dy = y1 - y0                    # Vertical distance
            L = math.hypot(dx, dy)          # Total distance (Pythagorean theorem)

            if L == 0:
                continue  # Skip if nodes are at exact same position (avoid divide by zero)

            # ----------------------------------------------------------------
            # Calculate how stretched/compressed the spring is
            # ----------------------------------------------------------------
            rest = self.rest_lengths[i] * self.spacing_scale  # Desired length
            strain = (L - rest) / rest  # Strain = how far from rest (as percentage)

            # Example: If L=120 and rest=100:
            #   strain = (120-100)/100 = 0.2 (20% stretched)
            # Example: If L=80 and rest=100:
            #   strain = (80-100)/100 = -0.2 (20% compressed)

            # ----------------------------------------------------------------
            # Calculate spring stiffness (can change based on strain!)
            # ----------------------------------------------------------------
            # Poisson effect: real materials get stiffer when stretched
            stiffness = self.base_stiffness * self.stiffness_scale * (1 + self.poisson_ratio * abs(strain))

            # ----------------------------------------------------------------
            # Calculate force magnitude using Hooke's Law: F = k × Δx
            # ----------------------------------------------------------------
            F = stiffness * (L - rest)  # Force magnitude
            # If stretched (L > rest): F is positive (pulling)
            # If compressed (L < rest): F is negative (pushing)

            # ----------------------------------------------------------------
            # Convert force magnitude to X and Y components
            # ----------------------------------------------------------------
            # We need to apply force in the direction connecting the nodes
            fx = F * dx / L  # Force in X direction (normalized by distance)
            fy = F * dy / L  # Force in Y direction (normalized by distance)

            # Why divide by L? To normalize the direction vector!
            # Example: if dx=30 and L=50, then dx/L = 0.6 (60% in X direction)

            # ----------------------------------------------------------------
            # Apply equal and opposite forces (Newton's 3rd Law!)
            # ----------------------------------------------------------------
            # "For every action, there is an equal and opposite reaction"
            forces[i][0] += fx      # Node i gets pulled in +X direction
            forces[i][1] += fy      # Node i gets pulled in +Y direction
            forces[i + 1][0] -= fx  # Node i+1 gets pulled in -X direction (opposite!)
            forces[i + 1][1] -= fy  # Node i+1 gets pulled in -Y direction

        # ========================================================================
        # STEP 6: Update positions using physics integration
        # ========================================================================
        # PHYSICS INTEGRATION EXPLANATION:
        # This is how we turn forces into movement! Three-step process:
        #   1. Force → Acceleration (F = ma, so a = F/m)
        #   2. Acceleration → Velocity (velocity changes based on acceleration)
        #   3. Velocity → Position (position changes based on velocity)
        #
        # Example: A heavy node with force=100 and mass=10
        #   → acceleration = 100/10 = 10 units/sec²
        #   → if dt=0.016 sec, velocity changes by 10×0.016 = 0.16 units/sec
        #   → if velocity=5, position changes by 5×0.016 = 0.08 units

        for i in range(NUM_NODES - 1):  # Update all nodes except the pinned tail
            # ----------------------------------------------------------------
            # Get current velocity
            # ----------------------------------------------------------------
            vx, vy = self.velocities[i]  # Current speed in X and Y

            # ----------------------------------------------------------------
            # Calculate acceleration from force (F = ma → a = F/m)
            # ----------------------------------------------------------------
            ax = forces[i][0] / self.masses[i]  # Acceleration X = Force X / mass
            ay = forces[i][1] / self.masses[i]  # Acceleration Y = Force Y / mass

            # Heavier nodes (larger mass) accelerate slower with same force!
            # Example: mass=8, force=160 → acceleration=20
            # Example: mass=2, force=160 → acceleration=80 (much faster!)

            # ----------------------------------------------------------------
            # Update velocity (add acceleration × time)
            # ----------------------------------------------------------------
            vx += ax * dt  # New velocity = old velocity + (acceleration × time)
            vy += ay * dt

            # Example: If vx=100, ax=50, dt=0.016:
            #   vx_new = 100 + (50 × 0.016) = 100.8

            # ----------------------------------------------------------------
            # TAIL WHIP AMPLIFICATION - Cool physics trick!
            # ----------------------------------------------------------------
            # CONCEPT: In real whips, the tip moves MUCH faster than the handle!
            # WHY? Energy is conserved, but mass decreases toward the tip
            #
            # We simulate this by applying LESS damping to lighter nodes:
            # - Heavy head: loses lots of energy (high damping)
            # - Light tail: keeps more energy (low damping) → WHIP EFFECT!

            # Calculate what fraction of max mass this node has
            mass_ratio = self.masses[i] / max(self.masses)
            # Example: head with mass=8, max=8 → ratio=1.0 (100% of max)
            # Example: tail with mass=2, max=8 → ratio=0.25 (25% of max)

            mass_ratio = max(0.2, min(1.0, mass_ratio))  # Clamp between 0.2 and 1.0

            # Apply less damping to lighter nodes
            # If damping=0.8 and mass_ratio=1.0: local_damping = 0.8^1.0 = 0.8 (heavy)
            # If damping=0.8 and mass_ratio=0.25: local_damping = 0.8^0.25 = 0.945 (light)
            # Lighter nodes keep more velocity → whip effect!
            local_damping = self.damping ** mass_ratio

            # Apply damping (friction/energy loss)
            vx *= local_damping  # Reduce X velocity
            vy *= local_damping  # Reduce Y velocity

            # ----------------------------------------------------------------
            # Update position (add velocity × time)
            # ----------------------------------------------------------------
            x, y = self.nodes[i]  # Get current position
            x += vx * dt  # New X = old X + (velocity X × time)
            y += vy * dt  # New Y = old Y + (velocity Y × time)

            # Example: If x=100, vx=50, dt=0.016:
            #   x_new = 100 + (50 × 0.016) = 100.8

            # ----------------------------------------------------------------
            # Save updated position and velocity
            # ----------------------------------------------------------------
            self.nodes[i] = (x, y)        # Update position
            self.velocities[i] = [vx, vy]  # Update velocity

    # ============================================================================
    # DRAW METHOD - Visualize the snake!
    # ============================================================================
    # This method draws the snake on screen every frame
    # We draw in two passes:
    #   1. Draw the "springs" (connections between nodes)
    #   2. Draw the nodes (circles) on top
    # ============================================================================

    def draw(self, screen):
        """
        Draw the elastic snake boss on the screen.

        PARAMETERS:
        - screen: The pygame display surface to draw on

        VISUAL STRUCTURE:
        Springs (lines) show the connections and tension/compression
        Nodes (circles) show the actual body segments
        """

        base_thickness = 6  # Starting thickness for spring visualization

        # ========================================================================
        # PASS 1: Draw the springs (connections between nodes)
        # ========================================================================
        # Springs are drawn as lines whose color and thickness change based on
        # whether they're stretched (tension) or compressed

        for i in range(NUM_NODES - 1):  # One spring for each pair of nodes
            # ----------------------------------------------------------------
            # Get the two nodes this spring connects
            # ----------------------------------------------------------------
            x0, y0 = self.nodes[i]      # First node position
            x1, y1 = self.nodes[i + 1]  # Second node position

            # ----------------------------------------------------------------
            # Calculate spring length and strain
            # ----------------------------------------------------------------
            dx = x1 - x0                # Horizontal distance
            dy = y1 - y0                # Vertical distance
            L = math.hypot(dx, dy)      # Current length (actual distance)
            rest = self.rest_lengths[i] * self.spacing_scale  # Rest length (desired)

            if rest <= 0:
                continue  # Skip if rest length is invalid

            # Calculate strain (how stretched/compressed)
            strain = (L - rest) / rest  # Positive = stretched, negative = compressed
            # Example: L=120, rest=100 → strain = 0.2 (20% stretched)

            # ----------------------------------------------------------------
            # Calculate visual thickness using Poisson effect
            # ----------------------------------------------------------------
            # POISSON EFFECT: Real materials get thinner when stretched!
            # - Stretch a rubber band → it gets longer AND thinner
            # - Compress it → it gets shorter AND thicker
            #
            # Formula: thickness_factor = 1 - ν × strain
            # Where ν (nu) is the Poisson ratio (material property)

            poisson = self.poisson_ratio
            thickness_factor = 1 - poisson * strain

            # Clamp the factor so thickness never becomes too small or huge
            thickness_factor = max(5, min(10, thickness_factor))

            # Calculate final thickness
            thickness = max(40, int(base_thickness * (1 - poisson * strain)))

            # ----------------------------------------------------------------
            # Choose color based on tension/compression
            # ----------------------------------------------------------------
            # This gives visual feedback about the physics state!
            # - RED = tension (stretched)
            # - GRAY = compression (squished)

            if strain > 0:
                # TENSION (stretched) → Show as RED/PINK
                # More stretch = brighter/hotter red
                hot = min(255, int(120 + 300 * strain))  # Calculate brightness
                color = (255, hot, hot)  # RGB: full red, variable green/blue
                # Example: strain=0.1 → hot=150 → color=(255, 150, 150) pink
                # Example: strain=0.4 → hot=240 → color=(255, 240, 240) bright pink
            else:
                # COMPRESSION (squished) → Show as GRAY
                # More compression = darker gray
                fade = max(60, int(160 + 200 * strain))  # Calculate darkness
                color = (fade, fade, fade)  # Gray = equal RGB values
                # Example: strain=-0.2 → fade=120 → color=(120,120,120) dark gray
                # Example: strain=-0.5 → fade=60 → color=(60,60,60) very dark

            # ----------------------------------------------------------------
            # Safety check: Ensure positions are valid numbers
            # ----------------------------------------------------------------
            # Sometimes physics can produce NaN (Not a Number) or Infinity
            # This prevents crashes if that happens
            if not all(map(math.isfinite, (x0, y0, x1, y1))):
                continue  # Skip drawing this spring if positions are invalid

            # ----------------------------------------------------------------
            # Draw the spring as a line
            # ----------------------------------------------------------------
            pygame.draw.line(
                screen,                      # Where to draw
                color,                       # What color (red/gray)
                (int(x0), int(y0)),         # Start point
                (int(x1), int(y1)),         # End point
                thickness                    # How thick the line is
            )
            # Note: int() converts floats to integers (pygame needs whole pixels!)

        # ========================================================================
        # PASS 2: Draw the nodes (body segments)
        # ========================================================================
        # Nodes are drawn as circles with a gradient color from head to tail
        # - Head: Purple/blue (tough, important)
        # - Middle: Blend of colors
        # - Tail: Orange/red (vulnerable)

        for i, (x, y) in enumerate(self.nodes):
            # enumerate gives us: i=index (0,1,2...) and (x,y)=position
            # Example: enumerate([(10,20), (30,40)]) → (0,(10,20)), (1,(30,40))

            # ----------------------------------------------------------------
            # Calculate gradient position (0.0 at head → 1.0 at tail)
            # ----------------------------------------------------------------
            t = i / (NUM_NODES - 1)  # Normalize index to 0.0-1.0 range
            # Example with 10 nodes:
            #   i=0: t=0/9=0.0 (head)
            #   i=5: t=5/9=0.55 (middle)
            #   i=9: t=9/9=1.0 (tail)

            # ----------------------------------------------------------------
            # Create gradient color using interpolation
            # ----------------------------------------------------------------
            # RGB = (Red, Green, Blue) where each is 0-255
            # We blend between two color schemes:
            #   Head (t=0): (0, 100, 255) → bluish purple
            #   Tail (t=1): (255, 100, 0) → orange/red

            color = (
                int(255 * t),           # Red: 0 at head → 255 at tail
                int(100 * (1 - t)),     # Green: stays around 100
                int(255 * (1 - t))      # Blue: 255 at head → 0 at tail
            )
            # Example at head (t=0): (0, 100, 255) = blue/purple
            # Example at middle (t=0.5): (127, 50, 127) = purple/pink
            # Example at tail (t=1): (255, 0, 0) = red

            # ----------------------------------------------------------------
            # Draw the node as a circle
            # ----------------------------------------------------------------
            pygame.draw.circle(
                screen,              # Where to draw
                color,               # What color (gradient)
                (int(x), int(y)),   # Center position
                self.radii[i]       # Radius (size) - gets smaller toward tail!
            )
            # Remember: self.radii was set up in __init__ with a gradient
            # Head has big radius (48), tail has small radius (19)

               


# ================================================================================
# MAIN FUNCTION - Where the program starts!
# ================================================================================
# This is the entry point of our game. When you run the program, this function
# executes and creates the game window, sets up the snake boss, and runs the
# main game loop.
#
# GAME LOOP CONCEPT:
# Most games use a "game loop" that repeats over and over:
#   1. Handle input (keyboard, mouse, window events)
#   2. Update game state (move things, run physics)
#   3. Draw everything to screen
#   4. Wait a tiny bit to maintain consistent frame rate
#   [Repeat forever until user closes window]
# ================================================================================

def main():
    """
    The main function that runs the elastic snake boss visualization.

    WHAT THIS FUNCTION DOES:
    1. Initialize pygame and create window
    2. Set up the snake boss and its movement path
    3. Run the game loop (update and draw each frame)
    4. Handle user closing the window
    """

    # ============================================================================
    # STEP 1: Validate configuration
    # ============================================================================
    # Safety check to prevent crashes
    if NUM_NODES < 2:
        print("ERROR: NUM_NODES must be at least 2!")
        print("You can't have a chain with less than 2 nodes!")
        sys.exit(1)  # Exit the program with error code

    # ============================================================================
    # STEP 2: Initialize Pygame
    # ============================================================================
    # Pygame is a library for making games in Python
    # We need to initialize it before using any of its features

    pygame.init()  # Start up all pygame modules (graphics, sound, etc.)

    # Create the game window
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    # This creates a window that's WIDTH×HEIGHT pixels (1200×1200 by default)
    # "screen" is like a canvas we'll draw on

    # Set the window title (text in the title bar)
    pygame.display.set_caption(f"Elastic Snake Boss - {NUM_NODES} Nodes")
    # f-string inserts the NUM_NODES value into the text

    # Create a clock to control frame rate
    clock = pygame.time.Clock()
    # The clock helps us run at a consistent speed (60 FPS = 60 frames per second)

    # ============================================================================
    # STEP 3: Print startup information
    # ============================================================================
    # Let the user know the program started successfully
    print(f"=== Snake Boss Started ===")
    print(f"Number of nodes: {NUM_NODES}")
    print(f"Total HP: {HEAD_HP * NUM_NODES // 2} (approx)")  # // = integer division
    print(f"Controls: Watch the snake move!")
    print(f"==========================")

    # ============================================================================
    # STEP 4: Create the movement path
    # ============================================================================
    # The snake boss follows a wavy sine path back and forth between two points
    # Think of it like a train going back and forth on wavy tracks!

    # Define the two endpoints of the path
    node_a = (100, 500)   # Start point (x=100, y=500) - left side
    node_b = (700, 100)   # End point (x=700, y=100) - upper right

    # Create the forward path (A → B) with a wavy pattern
    sine_forward = generate_sine_edge(
        node_a,           # Starting position
        node_b,           # Ending position
        samples=50,       # How many points along the path (more = smoother)
        amplitude=10,     # How "tall" the waves are
        cycles=6          # How many complete waves from start to end
    )
    # This returns a list of (x, y) coordinates: [(x0,y0), (x1,y1), (x2,y2), ...]

    # Create the backward path (B → A) with waves going the opposite direction
    sine_backward = generate_sine_edge(
        node_b,           # Start from B this time
        node_a,           # Go back to A
        samples=50,       # Same smoothness
        amplitude=-10,    # Negative amplitude = waves flip upside down!
        cycles=6          # Same number of waves
    )

    # ============================================================================
    # STEP 5: Create game objects
    # ============================================================================
    # Now we create instances (objects) from our classes!
    # Remember: Classes are blueprints, objects are the actual things we build

    # Create a CurveFollower object that will move along the forward path
    boss_path = CurveFollower(sine_forward, speed=400)
    # This creates a "train" that follows the "tracks" at 400 pixels/second

    current_path = "forward"  # Track which direction we're going

    # Create the ElasticChain object (the snake boss!)
    chain = ElasticChain(boss_path.pos)
    # The snake's tail starts at wherever the path follower is currently positioned

    # ============================================================================
    # STEP 6: THE GAME LOOP!
    # ============================================================================
    # This loop runs over and over until the user closes the window
    # Each iteration = one "frame" of the animation
    # At 60 FPS, this loop runs 60 times per second!

    running = True  # Flag to control the loop
    while running:  # Keep looping while running is True
        # ========================================================================
        # 6A: Calculate delta time (time since last frame)
        # ========================================================================
        dt = clock.tick(60) / 1000.0
        # clock.tick(60) does two things:
        #   1. Waits to maintain 60 FPS (frames per second)
        #   2. Returns milliseconds since last frame
        # We divide by 1000 to convert milliseconds → seconds
        # Example: If running at 60 FPS, dt ≈ 0.0166 seconds (16.6 ms)

        # ========================================================================
        # 6B: Handle events (user input)
        # ========================================================================
        # Events are things that happen: mouse clicks, key presses, window close
        for event in pygame.event.get():  # Get all events that happened this frame
            if event.type == pygame.QUIT:  # Did user click the X button?
                running = False  # Set flag to False → loop will exit

        # ========================================================================
        # 6C: Update the path follower
        # ========================================================================
        boss_path.update(dt)  # Move along the path a bit
        # This moves the "anchor point" that the snake's tail follows

        # ========================================================================
        # 6D: Check if we reached the end of path - if so, switch directions!
        # ========================================================================
        if boss_path.index >= len(boss_path.points) - 1:
            # We've reached the last point in the current path
            if current_path == "forward":
                # We just finished going A → B, now go back B → A
                boss_path = CurveFollower(sine_backward, speed=1500)  # Faster return!
                current_path = "backward"
            else:
                # We just finished going B → A, now go forward A → B again
                boss_path = CurveFollower(sine_forward, speed=300)  # Slower forward
                current_path = "forward"
            # This creates a continuous back-and-forth motion!

        # ========================================================================
        # 6E: Update the snake physics
        # ========================================================================
        chain.update(tuple(boss_path.pos), dt)
        # tuple(boss_path.pos) converts the position to a tuple (x, y)
        # This runs the physics simulation for one frame (springs, forces, etc.)

        # ========================================================================
        # 6F: Clear the screen
        # ========================================================================
        screen.fill(BACKGROUND)
        # Fill the entire screen with the background color (dark blue-ish)
        # This "erases" the previous frame so we can draw the new one
        # Without this, everything would smear across the screen!

        # ========================================================================
        # 6G: Draw the path visualization (optional - helps see the path)
        # ========================================================================
        # Draw dots to show where the path goes

        # Draw endpoint markers (currently invisible with radius 0)
        pygame.draw.circle(screen, PLAYER_COLOR, node_a, 0)
        pygame.draw.circle(screen, PLAYER_COLOR, node_b, 0)

        # Draw sample points along the path (every 10th point)
        for p in sine_forward[::10]:  # [::10] means "every 10th element"
            pygame.draw.circle(screen, (80, 80, 120), (int(p[0]), int(p[1])), 0)

        # ========================================================================
        # 6H: Draw the snake boss
        # ========================================================================
        chain.draw(screen)
        # This calls the draw() method we defined in the ElasticChain class
        # It draws all the springs and nodes!

        # ========================================================================
        # 6I: Draw the anchor point (where the path follower is)
        # ========================================================================
        pygame.draw.circle(
            screen,                                    # Where to draw
            BOSS_COLOR,                                # Color (reddish)
            (int(boss_path.pos[0]), int(boss_path.pos[1])),  # Position
            8                                          # Radius (small dot)
        )
        # This shows where the tail is being pulled to

        # ========================================================================
        # 6J: Update the display
        # ========================================================================
        pygame.display.flip()
        # "flip" means "show everything we just drew"
        # Pygame uses "double buffering": we draw to an invisible buffer,
        # then flip it to visible all at once (prevents flickering!)

    # ============================================================================
    # STEP 7: Clean up and exit
    # ============================================================================
    # When the loop exits (user closed window), clean up properly
    pygame.quit()  # Shut down pygame
    sys.exit()     # Exit the program

if __name__ == "__main__":
    main()