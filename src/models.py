from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Type of a zone, determining movement cost and accessibility."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


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


@dataclass
class Connection:
    """Represents a bidirectional edge between two zones."""
    zone_a: str
    zone_b: str
    max_link_capacity: int = 1


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
