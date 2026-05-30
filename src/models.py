
"""Data models for the Fly-in drone routing simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.exceptions import ParseError


class ZoneType(Enum):
    """Type of a zone, determining movement cost and accessibility."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @classmethod
    def from_string(cls, value: str, line_number: int) -> "ZoneType":
        """Parse a string into a ZoneType, raising ParseError if invalid."""
        try:
            return cls(value)
        except ValueError:
            valid = ", ".join(z.value for z in cls)
            raise ParseError(
                line_number,
                f"Unknown zone type {value!r}. Must be one of: {valid}"
            )


class DroneStatus(Enum):
    """Lifecycle state of a drone during simulation."""

    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


@dataclass
class Zone:
    """Represents a single node in the routing graph."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    def movement_cost(self) -> int:
        """Return turn cost to enter this zone."""
        return 2 if self.zone_type == ZoneType.RESTRICTED else 1

    def is_accessible(self) -> bool:
        """Return False if zone is blocked, True otherwise."""
        return self.zone_type != ZoneType.BLOCKED

    def __repr__(self) -> str:
        """Return readable string representation."""
        return (
            f"Zone({self.name!r}, type={self.zone_type.value}, "
            f"max={self.max_drones})"
        )


@dataclass
class Connection:
    """Represents a bidirectional edge between two zones."""

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    def key(self) -> tuple[str, str]:
        """Return canonical sorted key for deduplication."""
        a, b = sorted([self.zone_a, self.zone_b])
        return (a, b)

    def connects(self, name: str) -> bool:
        """Return True if this connection involves the named zone."""
        return name == self.zone_a or name == self.zone_b

    def other(self, name: str) -> str:
        """Return the other endpoint zone name.

        Raises:
            ValueError: If name is not an endpoint of this connection.
        """
        if name == self.zone_a:
            return self.zone_b
        if name == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"Zone '{name}' is not part of "
            f"connection '{self.zone_a}-{self.zone_b}'"
        )

    def __repr__(self) -> str:
        """Return readable string representation."""
        return (
            f"Connection({self.zone_a!r} <-> {self.zone_b!r}, "
            f"cap={self.max_link_capacity})"
        )


@dataclass
class Graph:
    """The full routing network: zones and connections."""

    zones: dict[str, Zone] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    start_zone: str = ""
    end_zone: str = ""
    nb_drones: int = 0

    def get_zone(self, name: str) -> Optional[Zone]:
        """Return zone by name, or None if not found."""
        return self.zones.get(name)

    def get_connection(
        self, zone_a: str, zone_b: str
    ) -> Optional[Connection]:
        """Return connection between two zones, or None."""
        for conn in self.connections:
            if conn.connects(zone_a) and conn.connects(zone_b):
                return conn
        return None

    def neighbors(
        self, zone_name: str
    ) -> list[tuple[Zone, Connection]]:
        """Return accessible (neighbor_zone, connection) pairs."""
        result: list[tuple[Zone, Connection]] = []
        for conn in self.connections:
            if conn.connects(zone_name):
                neighbor = self.zones.get(conn.other(zone_name))
                if neighbor and neighbor.is_accessible():
                    result.append((neighbor, conn))
        return result

    def __str__(self) -> str:
        """Return human-readable graph summary."""
        lines = [
            f"Graph: {self.nb_drones} drones | "
            f"start={self.start_zone!r} | end={self.end_zone!r}",
            f"  Zones ({len(self.zones)}):",
        ]
        for zone in self.zones.values():
            marker = ""
            if zone.is_start:
                marker = " [START]"
            elif zone.is_end:
                marker = " [END]"
            lines.append(
                f"    {zone.name}{marker}: "
                f"type={zone.zone_type.value}, "
                f"color={zone.color}, "
                f"max_drones={zone.max_drones}, "
                f"pos=({zone.x},{zone.y})"
            )
        lines.append(f"  Connections ({len(self.connections)}):")
        for conn in self.connections:
            lines.append(
                f"    {conn.zone_a} <-> {conn.zone_b} "
                f"[cap={conn.max_link_capacity}]"
            )
        return "\n".join(lines)


@dataclass
class Drone:
    """Represents a single drone being routed through the graph."""

    drone_id: int
    current_zone: str
    status: DroneStatus = DroneStatus.WAITING
    transit_turns_left: int = 0
    transit_destination: Optional[str] = None
    path: list[str] = field(default_factory=list)
    path_index: int = 0

    @property
    def label(self) -> str:
        """Return display label e.g. 'D1'."""
        return f"D{self.drone_id}"

    def has_arrived(self) -> bool:
        """Return True if drone has reached the end zone."""
        return self.status == DroneStatus.ARRIVED

    def next_zone(self) -> Optional[str]:
        """Return next planned zone in path, or None."""
        next_index = self.path_index + 1
        if self.path and next_index < len(self.path):
            return self.path[next_index]
        return None

    def __repr__(self) -> str:
        """Return readable string representation."""
        return (
            f"Drone(id={self.drone_id}, zone={self.current_zone!r}, "
            f"status={self.status.value})"
        )


@dataclass
class ZoneState:
    """Runtime occupancy state for a single zone.

    Attributes:
        zone: The zone this state tracks.
        drones: Set of drone IDs currently occupying this zone.
    """

    zone: Zone
    drones: set[int] = field(default_factory=set)

    def occupancy(self) -> int:
        """Return number of drones currently in this zone."""
        return len(self.drones)

    def has_capacity(self, incoming: int = 1) -> bool:
        """Return True if zone can accept more drones."""
        return self.occupancy() + incoming <= self.zone.max_drones


@dataclass
class ConnectionState:
    """Runtime traversal state for a single connection.

    Attributes:
        connection: The connection this state tracks.
        drones: Set of drone IDs currently traversing this connection.
    """

    connection: Connection
    drones: set[int] = field(default_factory=set)

    def occupancy(self) -> int:
        """Return number of drones currently using this connection."""
        return len(self.drones)

    def has_capacity(self, incoming: int = 1) -> bool:
        """Return True if connection can accept more drones."""
        return (
            self.occupancy() + incoming
            <= self.connection.max_link_capacity
        )
