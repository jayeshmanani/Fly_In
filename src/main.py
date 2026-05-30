import sys
from src.parser import MapParser
from src.exceptions import ParseError


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


if __name__ == "__main__":
    main()
