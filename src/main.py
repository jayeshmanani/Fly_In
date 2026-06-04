import sys
from src.parser import MapParser
from src.exceptions import ParseError
from src.simulator import Simulator
from src.visualizer import Visualizer


def main() -> None:
    """Parse a drone map file and print its graph summary.

    Usage:
        python3 -m src.main <path_to_map_file>
    """
    if len(sys.argv) != 2:
        print("Usage: python3 -m src.main <map_file>", file=sys.stderr)
        print("make run MAP=<path_to_map_file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        graph = MapParser().parse(filepath)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        sim = Simulator(graph)
        turn_log = sim.run()
    except ParseError as e:
        print(f"Simulation error: {e}", file=sys.stderr)
        sys.exit(1)

    for line_num, line in enumerate(turn_log):
        print(f"Turn {line_num + 1}: {line}")
    print()
    print("Launching visualizer... (Q or ESC to quit)")

    viz = Visualizer(graph, turn_log)
    viz.run()
    print()
    print(f"Completed in {sim.get_turn_count()} turns.")


if __name__ == "__main__":
    main()
