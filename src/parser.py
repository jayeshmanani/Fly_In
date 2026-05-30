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
        """Initialize with line number and error description.

        Args:
            line_number: 1-based line index in the source file.
            message: Description of the parsing error.
        """
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


class MapParser:
    """Parses a drone routing map file into a Graph object.

    Each instance is single-use: call parse() once per file.
    Internal state tracks what has been seen so far to catch
    duplicates and ordering violations as the file is read line
    by line.

    Attributes:
        _graph: The Graph being built.
        _seen_connections: Canonical keys of already-parsed connections.
        _found_nb_drones: Whether the nb_drones directive was seen.
        _start_count: Number of start_hub lines encountered.
        _end_count: Number of end_hub lines encountered.
    """

    def __init__(self) -> None:
        """Initialise a fresh parser with an empty graph."""
        self._graph: Graph = Graph()
        self._seen_connections: set[tuple[str, str]] = set()
        self._found_nb_drones: bool = False
        self._start_count: int = 0
        self._end_count: int = 0

        self._handlers = {
            "start_hub:": self._handle_start_hub,
            "end_hub:": self._handle_end_hub,
            "hub:": self._handle_hub,
            "connection:": self._handle_connection,
        }

    def parse(self, filepath: str) -> Graph:
        """Parse a map file and return the resulting Graph.

        Args:
            filepath: Path to the .txt map file.

        Returns:
            A fully populated Graph object.

        Raises:
            FileNotFoundError: If the file does not exist.
            ParseError: On any syntax, structure, or reference error.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file not found: {filepath!r}")

        for line_number, raw_line in enumerate(lines, start=1):
            self._parse_line(raw_line, line_number)
        self._validate()
        return self._graph

    def _validate(self) -> None:
        if not self._found_nb_drones:
            raise ParseError(0, "Missing 'nb_drones' definition")

    def _parse_line(self, raw_line: str, line_number: int) -> None:
        """Strip and route a single raw line to the correct handler.

        Args:
            raw_line: Unprocessed line from the file.
            line_number: 1-based line index for error messages.

        Raises:
            ParseError: If the line prefix is not recognised, or if
                nb_drones has not yet been seen.
        """
        line = raw_line.strip()

        if not line or line.startswith("#"):
            return

        if line.startswith("nb_drones:"):
            self._handle_nb_drones(line, line_number)
            return

        if not self._found_nb_drones:
            raise ParseError(
                line_number,
                "First non-comment line must be 'nb_drones: <n>'",
            )
        return

        # for prefix, handler in self._handlers.items():
        #     if line.startswith(prefix):
        #         handler(line, line_number)
        #         return
        # raise ParseError(line_number, f"Unrecognised line format: {line!r}")

    def _handle_nb_drones(self, line: str, line_number: int) -> None:
        if self._found_nb_drones:
            raise ParseError(
                line_number,
                "Duplicate 'nb_drones' definition"
            )
        value = line[len("nb_drones:"):].strip()
        self._graph.nb_drones = self._parse_positive_int(
            value,
            "nb_drones",
            line_number
        )
        self._found_nb_drones = True

    def _handle_start_hub(self, line: str, line_number: int) -> None:
        return None

    def _handle_end_hub(self, line: str, line_number: int) -> None:
        return None

    def _handle_hub(self, line: str, line_number: int) -> None:
        return None

    def _handle_connection(self, line: str, line_number: int) -> None:
        return None

    def _parse_positive_int(
        self,
        value: str,
        field_name: str,
        line_number: int,
    ) -> int:
        """Parse a string as a positive integer.

        Args:
            value: String to parse.
            field_name: Human-readable field name for error messages.
            line_number: Source line index for error reporting.

        Returns:
            Parsed integer greater than zero.

        Raises:
            ParseError: If value is not a valid positive integer.
        """
        try:
            n = int(value)
        except ValueError:
            raise ParseError(
                line_number,
                f"'{field_name}' must be an integer, got {value!r}"
            )
        if n <= 0:
            raise ParseError(
                line_number,
                f"'{field_name}' must be positive, got {n}"
            )
        return n
