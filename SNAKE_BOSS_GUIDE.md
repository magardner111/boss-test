# Elastic Snake Boss - Easy Configuration Guide

## Quick Start: Adding More Nodes

Want to make the snake longer or shorter? **Just change one number!**

Open `snakeforrealthistime.py` and find this section (around line 40):

```python
# ==========================================
# CHANGE THIS NUMBER TO ADD MORE NODES!
# Try: 10, 20, 30, 50, etc.
# More nodes = longer snake boss
# ==========================================
NUM_NODES = 10
```

Change `10` to any number you want:
- **10 nodes** = short snake (default)
- **20 nodes** = medium snake
- **50 nodes** = long snake
- **100 nodes** = VERY long snake (might be slow)

That's it! The snake automatically adjusts everything else.

---

## All Customization Options

All settings are in the **CONFIG** section at the top of the file:

### Size Settings
```python
NODE_RADIUS = 48        # How big the head is
NODE_RADIUS_TIP = 19    # How big the tail is
```

### HP (Health Points)
```python
HEAD_HP = 120  # Head health (tough)
TAIL_HP = 30   # Tail health (weak)
```
The snake automatically creates a gradient from head to tail.

### Physics Settings
```python
HEAD_MASS = 8.0   # Heavy head (stable)
TAIL_MASS = 1.5   # Light tail (whippy!)
```
- **Heavier tail** = less whip action
- **Lighter tail** = more whip action

---

## What Gets Generated Automatically

When you set `NUM_NODES = 20`, the program automatically creates:
- ✅ 20 connected nodes in a chain
- ✅ Physics springs between each node
- ✅ Smooth size gradient (big → small)
- ✅ HP gradient (120 HP → 30 HP)
- ✅ Mass gradient (heavy → light)
- ✅ Color gradient (purple → orange)

You don't have to do anything else!

---

## How the Snake Boss Works

### Movement States
The boss has 3 automatic states:
1. **Idle** (0-10 seconds): Normal movement
2. **Expanded** (10-20 seconds): Snake stretches out
3. **Rigid** (20+ seconds): Snake becomes stiff

### Path Following (Multi-Waypoint System!)
The snake follows a wavy path through multiple waypoints:
```python
waypoints = [
    (100, 500),    # Waypoint 0: Left-middle
    (700, 100),    # Waypoint 1: Upper-right
    (1000, 800),   # Waypoint 2: Lower-right
    (400, 900),    # Waypoint 3: Bottom-center
]
```

**How to add more waypoints:**
1. Just add more `(x, y)` coordinates to the list!
2. Snake travels: 0 → 1 → 2 → 3 → 0 (loops forever)
3. Minimum 2 waypoints, no maximum!

**Path settings:**
```python
PATH_SAMPLES = 50      # Smoothness (higher = smoother)
PATH_AMPLITUDE = 10    # Waviness (higher = more wiggly)
PATH_CYCLES = 6        # Number of waves per segment
PATH_SPEED = 400       # Movement speed (pixels/second)
```

---

## Example Configurations

### Tiny Fast Snake
```python
NUM_NODES = 5
HEAD_MASS = 2.0
TAIL_MASS = 0.5
```

### Long Heavy Snake
```python
NUM_NODES = 50
HEAD_MASS = 15.0
TAIL_MASS = 3.0
```

### Super Whippy Snake
```python
NUM_NODES = 30
HEAD_MASS = 10.0
TAIL_MASS = 0.5  # Very light tail!
```

---

## Path Configuration Examples

### Simple Circle (4 waypoints)
```python
waypoints = [
    (300, 300),   # Top-left
    (900, 300),   # Top-right
    (900, 900),   # Bottom-right
    (300, 900),   # Bottom-left
]
```

### Zigzag Pattern (5 waypoints)
```python
waypoints = [
    (100, 200),
    (1100, 400),
    (100, 600),
    (1100, 800),
    (100, 1000),
]
```

### Star Pattern (5 waypoints)
```python
waypoints = [
    (600, 100),    # Top point
    (900, 900),    # Bottom-right
    (200, 400),    # Left
    (1000, 400),   # Right
    (300, 900),    # Bottom-left
]
```

### Complex Tour (8 waypoints)
```python
waypoints = [
    (200, 200),
    (1000, 200),
    (1000, 500),
    (600, 600),
    (1000, 800),
    (600, 1000),
    (200, 800),
    (200, 500),
]
```

**Tips for designing paths:**
- Spread waypoints evenly for smooth motion
- Use 4-8 waypoints for interesting patterns
- Keep within window bounds (0-1200)
- Test different amplitudes and speeds!

---

## Troubleshooting

**Q: The snake is too slow!**
A: Reduce `NUM_NODES` or increase the computer's specs

**Q: The snake flies apart!**
A: The physics might be unstable. Try:
- Reducing `NUM_NODES`
- Increasing `base_stiffness` in the ElasticChain class

**Q: The snake is too stiff!**
A: Decrease `base_stiffness` (default: 20.0) in line 174

**Q: I want the snake to move differently!**
A: Change the path points `node_a` and `node_b` in the main() function

---

## What Was Fixed

The original code was crashing because:
- ❌ `generate_sine_edge()` was called with 3 arguments instead of 2
- ❌ `node_c` parameter didn't exist in the function

Now it's fixed! ✅

---

Enjoy your elastic snake boss! 🐍
