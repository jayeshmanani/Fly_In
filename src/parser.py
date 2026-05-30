import re
from typing import Optional
from src.models import Graph, Zone, Connection, ZoneType
from src.exceptions import ParseError


class MapParser:
    """Parses a drone routing map file into a Graph. Single-use per file."""

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

    def _parse_line(self, raw_line: str, line_number: int) -> None:
        """Route a single raw line to the correct handler."""
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

        for prefix, handler in self._handlers.items():
            if line.startswith(prefix):
                handler(line, line_number)
                return
        raise ParseError(line_number, f"Unrecognised line format: {line!r}")

    def _handle_nb_drones(self, line: str, line_number: int) -> None:
        """Handle a nb_drones directive line."""
        if self._found_nb_drones:
            raise ParseError(line_number, "Duplicate 'nb_drones' definition")
        value = line[len("nb_drones:"):].strip()
        self._graph.nb_drones = self._parse_positive_int(
            value, "nb_drones", line_number
        )
        self._found_nb_drones = True

    def _handle_start_hub(self, line: str, line_number: int) -> None:
        """Handle a start_hub zone definition line."""
        if self._start_count:
            raise ParseError(line_number, "Multiple 'start_hub' definitions")
        rest = line[len("start_hub:"):].strip()
        zone = self._parse_hub_line(
            rest, line_number, is_start=True, is_end=False
        )
        self._add_zone(zone, line_number)
        self._graph.start_zone = zone.name
        self._start_count += 1

    def _handle_end_hub(self, line: str, line_number: int) -> None:
        return None

    def _handle_hub(self, line: str, line_number: int) -> None:
        return None

    def _handle_connection(self, line: str, line_number: int) -> None:
        return None

    def _parse_hub_line(
        self, rest: str, line_number: int, is_start: bool, is_end: bool
    ) -> Zone:
        """Parse '<name> <x> <y> [metadata]' into a Zone."""
        meta, rest = self._extract_metadata(rest, line_number)
        parts = rest.split()
        if len(parts) != 3:
            raise ParseError(
                line_number, f"Hub expects '<name> <x> <y>', got {rest!r}"
            )
        name, x_str, y_str = parts
        if "-" in name:
            raise ParseError(
                line_number, f"Zone name {name!r} must not contain dashes"
            )
        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise ParseError(
                line_number,
                f"Coordinates must be integers, "
                f"got x={x_str!r} y={y_str!r}"
            )
        zone_type = ZoneType.NORMAL
        if "zone" in meta:
            zone_type = ZoneType.from_string(meta["zone"], line_number)
        max_drones = 999999 if (is_start or is_end) else 1
        if "max_drones" in meta:
            max_drones = self._parse_positive_int(
                meta["max_drones"], "max_drones", line_number
            )
        color: Optional[str] = meta.get("color")
        return Zone(
            name=name, x=x, y=y, zone_type=zone_type,
            color=color, max_drones=max_drones,
            is_start=is_start, is_end=is_end,
        )

    def _validate(self) -> None:
        """Ensure all mandatory sections were present."""
        if not self._found_nb_drones:
            raise ParseError(0, "Missing 'nb_drones' definition")
        if self._start_count == 0:
            raise ParseError(0, "Missing 'start_hub' definition")
        # if self._end_count == 0:
        #     raise ParseError(0, "Missing 'end_hub' definition")

    def _add_zone(self, zone: Zone, line_number: int) -> None:
        """Insert zone into graph, raising on duplicate names."""
        if zone.name in self._graph.zones:
            raise ParseError(line_number, f"Duplicate zone name {zone.name!r}")
        self._graph.zones[zone.name] = zone

    def _parse_positive_int(
        self,
        value: str,
        field_name: str,
        line_number: int,
    ) -> int:
        """Parse string as a positive integer."""
        try:
            n = int(value)
        except ValueError:
            raise ParseError(
                line_number,
                f"'{field_name}' must be an integer, "
                f"got {value!r}"
            )
        if n <= 0:
            raise ParseError(
                line_number, f"'{field_name}' must be positive, got {n}"
            )
        return n

    def _extract_metadata(
        self, text: str, line_number: int
    ) -> tuple[dict[str, str], str]:
        """Strip trailing [key=value ...] block, return (meta, rest)."""
        meta: dict[str, str] = {}
        match = re.search(r"\[.*\]$", text.strip())
        if match:
            meta = self._parse_metadata(match.group(0), line_number)
            text = text[: match.start()].strip()
        return meta, text

    def _parse_metadata(self, raw: str, line_number: int) -> dict[str, str]:
        """Parse '[key=value ...]' block into a dict."""
        if not raw.startswith("[") or not raw.endswith("]"):
            raise ParseError(line_number, f"Invalid metadata block: {raw!r}")
        meta: dict[str, str] = {}
        for token in raw[1:-1].strip().split():
            if "=" not in token:
                raise ParseError(
                    line_number, f"Metadata token missing '=': {token!r}"
                )
            key, _, value = token.partition("=")
            if not key or not value:
                raise ParseError(
                    line_number, f"Malformed metadata token: {token!r}"
                )
            meta[key.strip()] = value.strip()
        return meta
