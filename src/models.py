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
                f"Unknown zone type {value!r}. Must be one of: {valid}")


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
        """Return a canonical (sorted) key for deduplication.

        Returns:
            Tuple of zone names in alphabetical order.
        """
        a, b = sorted([self.zone_a, self.zone_b])
        return (a, b)

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

    def __repr__(self) -> str:
        """Return readable string representation."""
        return (
            f"Drone(id={self.drone_id}, zone={self.current_zone!r}, "
            f"status={self.status.value})"
        )
