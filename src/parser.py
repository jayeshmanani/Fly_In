# import re
# from typing import Optional
from src.models import Graph
# Connection, Zone, ZoneType


class ParseError(Exception):
    """
    Raised when a map file contains invalid syntax or structure.

    Attributes:
        line_number: The 1-based line number where the error occurred.
        message: Human-readable description of what went wrong.
    """

    def __init__(self, line_number: int, message: str) -> None:
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


def parse_map(filepath: str) -> Graph:
    """Parse a drone routing map file and return a Graph.

    The first non-comment, non-blank line must be 'nb_drones: <n>'.
    Exactly one start_hub and one end_hub must be defined.

    Args:
        filepath: Path to the .txt map file.

    Returns:
        A fully populated Graph object.

    Raises:
        ParseError: On any syntax, structure, or reference error.
        FileNotFoundError: If the file does not exist.
    """
    graph = Graph()
    # seen_connections: set[tuple[str, str]] = set()
    # found_nb_drones = False
    # start_count = 0
    # end_count = 0

    return graph
