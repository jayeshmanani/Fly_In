*This project has been created as part of the 42 curriculum by jmanani.*

# Fly-in - Drone Routing Simulation

## Description

Fly-in is a turn-based drone routing simulation written in Python. Given a graph of connected zones, the program routes a fleet of drones from a start hub to an end hub in the fewest possible simulation turns, while respecting zone capacities, connection capacities, zone types, and movement constraints.

The system handles:
- Multiple simultaneous drone movements per turn
- Zone capacity limits (`max_drones`) and connection capacity limits (`max_link_capacity`)
- Four zone types: `normal`, `restricted`, `priority`, and `blocked`
- 2-turn transit mechanics for restricted zones
- Dynamic rerouting when drones are blocked by congestion
- Step-by-step Pygame visualization of the simulation

## Instructions

### Installation

```bash
make install
```

### Running a simulation

```bash
make run MAP=maps/easy/01_linear_path.txt
```

This will:
1. Parse the map file and print the graph summary
2. Run the simulation and print turn-by-turn drone movements
3. Open the Pygame visualizer for interactive playback

### Visualizer controls

| Key | Action |
|-----|--------|
| `SPACE` / `→` | Next turn |
| `←` | Previous turn |
| `A` | Toggle auto-play |
| `R` | Restart |
| `Q` / `ESC` | Quit |

### Linting

```bash
make lint
```

### Other commands

```bash
make debug MAP=maps/easy/01_linear_path.txt   # run with pdb debugger
make clean                                      # remove __pycache__ and .mypy_cache
```

### Map file format

```
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: zone1 1 0 [zone=normal color=blue max_drones=2]
end_hub: goal 2 0 [color=red]

connection: start-zone1 [max_link_capacity=2]
connection: zone1-goal
```

## Project Structure

```
fly-in/
├── src/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── models.py        # Zone, Connection, Graph, Drone dataclasses
│   ├── exceptions.py    # ParseError
│   ├── parser.py        # MapParser class
│   ├── pathfinder.py    # PathFinder: Dijkstra + Yen's K-shortest paths (extra path than just one shortest)
│   ├── simulator.py     # Simulator: turn-based engine
│   └── visualizer.py    # Pygame visualizer
├── maps/
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── challenger/
├── Makefile
├── pyproject.toml
├── README.md
├── uv.lock
└── .gitignore
```

## Algorithm

### Pathfinding - Dijkstra + Yen's K-Shortest Paths

The pathfinder uses **Dijkstra's algorithm** to find the lowest-cost path through the graph. Zone movement costs are:

| Zone type | Cost |
|-----------|------|
| `normal` | 1.0 |
| `priority` | 0.9 (preferred) |
| `restricted` | 2.0 |
| `blocked` | impassable |

Priority zones get a small cost bonus (`-0.1`) so Dijkstra naturally prefers them over normal zones when paths are otherwise equal, without changing the simulation turn cost.

For distributing multiple drones, **Yen's K-Shortest Paths** algorithm finds up to K distinct paths by iteratively running Dijkstra while blocking previously found paths. This gives the scheduler a pool of routes to spread drones across.

### Simulation - Turn-Based Scheduler

Each simulation turn runs in two phases:

1. **Transit arrivals** - drones in 2-turn restricted transit must arrive, regardless of destination zone capacity (per spec).
2. **Movement** - remaining waiting drones attempt to move one step along their path. Drones closest to the goal move first to clear bottlenecks.

Key mechanics:
- Drones moving **out** of a zone free capacity for that same turn
- Connection capacity (`max_link_capacity`) is checked before each move
- When a drone's next zone is full, **dynamic rerouting** recalculates a new path from the drone's current position, avoiding currently-congested zones
- A deadlock detector triggers a forced reroute if no drone moves for 5 consecutive turns

### Drone Assignment

Drones are distributed across available paths round-robin, respecting the bottleneck capacity of each path (minimum zone/connection capacity along the route). Drones on the same path are **staggered** by one turn each to prevent pile-ups at bottlenecks.

## Performance

All maps solved well within benchmarks:

| Map | Drones | Target | Result |
|-----|--------|--------|--------|
| Easy 1 - Linear Path | 2 | ≤ 6 | **4** |
| Easy 2 - Simple Fork | 4 | ≤ 8 | **4** |
| Easy 3 - Basic Capacity | 4 | ≤ 6 | **6** |
| Medium 1 - Dead End Trap | 5 | ≤ 12 | **8** |
| Medium 2 - Circular Loop | 6 | ≤ 15 | **10** |
| Medium 3 - Priority Puzzle | 5 | ≤ 12 | **6** |
| Hard 1 - Maze Nightmare | 8 | ≤ 30 | **13** |
| Hard 2 - Capacity Hell | 12 | ≤ 35 | **13** |
| Hard 3 - Ultimate challenge | 15 | ≤ 45 | **27** |

## Simulation Output Format

Each line represents one turn. Movements are space-separated in the format `D<ID>-<zone>`. Drones in transit to a restricted zone are shown as `D<ID>-<zone_a>-<zone_b>`. Drones that do not move are omitted.

```
D1-maze_a1 D2-maze_a1
D1-maze_a2 D2-maze_b1 D3-maze_a1
D1-maze_c2 D2-maze_b2 D3-maze_a2
...
```

## Visualization

The Pygame visualizer renders the graph with:
- Zones as colored circles using map metadata colors
- Restricted zones with a outer ring, priority zones with a cyan ring
- Connection thickness proportional to `max_link_capacity`
- Drones as small labeled circles, arranged in a ring when sharing a zone
- In-transit drones shown at the midpoint of their connection
- HUD (Heads-Up-Display) showing turn count, drones arrived, and playback mode
- Zone type legend in the bottom-right corner

## Resources

- [Dijkstra's Algorithm - Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Yen's K-Shortest Paths - Wikipedia](https://en.wikipedia.org/wiki/Yen%27s_algorithm)
- [Python heapq documentation](https://docs.python.org/3/library/heapq.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [Pygame-CE documentation](https://pyga.me/docs/)

### AI Usage

AI was used throughout this project for:
- **Debugging** - identifying logic bugs such as the restricted zone double-move issue and simulator deadlocks
- **Understanding concepts** - explaining Dijkstra's algorithm, Yen's K-shortest paths, and turn-based simulation design
- **Code explanations** - clarifying how specific methods and design patterns work (e.g. circular import resolution, OOP parser design)
- **README generation** - drafting and structuring this document
- **Research** - exploring pathfinding algorithm trade-offs and Python typing best practices, and how pygame can be used