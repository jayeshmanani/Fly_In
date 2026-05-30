"""Pathfinding for the Fly-in drone routing simulation."""

import heapq
from typing import Optional
from src.models import Graph, Zone, ZoneType


class Pathfinder:
    """Finds shortest and K-shortest paths through a drone routing graph.

    Uses Dijkstra's algorithm for single shortest path and
    Yen's K-shortest paths algorithm for multiple path discovery.

    Attributes:
        _graph: The routing graph to search.
    """
    _PRIORITY_BONUS: float = 0.1

    def __init__(self, graph: Graph) -> None:
        """Initialise with the routing graph to search."""
        self._graph = graph

    def find_shortest_path(self, start: str, end: str,
                           blocked_zones: Optional[set[str]] = None,
                           blocked_edges: Optional[set[tuple[str, str]]] = None
                           ) -> Optional[list[str]]:
        """Find the lowest-cost path from start to end using Dijkstra.

        Args:
            start: Name of the starting zone.
            end: Name of the destination zone.
            blocked_zones: Zone names to treat as not passable.
            blocked_edges: (zone_a, zone_b) pairs to treat as removed.

        Returns:
            Ordered list of zone names from start to end inclusive,
            or None if no path exists.
        """
        blocked_zones = blocked_zones or set()
        blocked_edges = blocked_edges or set()

        heap: list[tuple[float, str, list[str]]] = [
            (0.0, start, [start])
        ]
        visited: set[str] = set()

        while heap:
            cost, current, path = heapq.heappop(heap)
            if current in visited:
                continue
            visited.add(current)
            if current == end:
                return path

            for neighbor, conn in self._graph.neighbors(current):
                if neighbor.name in visited:
                    continue
                if neighbor.name in blocked_zones:
                    continue
                edge = (min(current, neighbor.name),
                        max(current, neighbor.name))
                if edge in blocked_edges:
                    continue

                move_cost = self._movement_cost(neighbor)
                heapq.heappush(heap, (cost + move_cost, neighbor.name, path +
                                      [neighbor.name]))
        return None

    def _movement_cost(self, zone: Zone) -> float:
        """Return movement cost with priority bonus for pathfinding."""
        cost = float(zone.movement_cost())
        if zone.zone_type == ZoneType.PRIORITY:
            cost *= (1 - self._PRIORITY_BONUS)
        return cost
