import sys
from src.pathfinder import Pathfinder
from src.parser import MapParser
from src.exceptions import ParseError
from src.simulator import Simulator


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
    print(graph)
    print()

    finder = Pathfinder(graph)
    paths = finder.find_shortest_path(graph.start_zone, graph.end_zone)
    print(f"Shortest paths: {paths}")
    print()

    try:
        sim = Simulator(graph)
        turn_log = sim.run()
    except ParseError as e:
        print(f"Simulation error: {e}", file=sys.stderr)
        sys.exit(1)

    for line in turn_log:
        print(line)

    print()
    print(f"Completed in {sim.get_turn_count()} turns.")


if __name__ == "__main__":
    main()
