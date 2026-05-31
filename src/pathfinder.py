"""Pathfinding for the Fly-in drone routing simulation."""

import heapq
from typing import Optional
from src.models import Graph, Zone, ZoneType


class PathFinder:
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

    def _movement_cost(self, zone: Zone) -> float:
        """Return movement cost with priority bonus for pathfinding."""
        cost = float(zone.movement_cost())
        if zone.zone_type == ZoneType.PRIORITY:
            cost *= (1 - self._PRIORITY_BONUS)
        return cost

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

    def find_k_shortest_paths(
        self,
        start: str,
        end: str,
        k: int,
    ) -> list[list[str]]:
        """Find up to K shortest paths using Yen's algorithm.

        Each successive path is the shortest path that differs from
        all previously found paths in at least one edge or zone.

        Args:
            start: Name of the starting zone.
            end: Name of the destination zone.
            k: Maximum number of paths to return.

        Returns:
            List of paths (each a list of zone names), ordered by cost.
            May return fewer than K paths if the graph has fewer.
        """
        first = self.find_shortest_path(start, end)
        if first is None:
            return []
        all_paths: list[list[str]] = [first]
        candidates: list[tuple[float, list[str]]] = []

        for _ in range(k-1):
            base_path = all_paths[-1]
            for spur_idx in range(len(base_path) - 1):
                spur_node = base_path[spur_idx]
                root_path = base_path[:spur_idx + 1]

                blocked_edges: set[tuple[str, str]] = set()
                blocked_zones: set[str] = set()

                for prev_path in all_paths:
                    if (len(prev_path) > spur_idx and
                            prev_path[: spur_idx + 1] == root_path):
                        edge = (min(prev_path[spur_idx],
                                    prev_path[spur_idx + 1]),
                                max(prev_path[spur_idx],
                                    prev_path[spur_idx + 1]))
                        blocked_edges.add(edge)
                for node in root_path[:-1]:
                    blocked_zones.add(node)
                spur_path = self.find_shortest_path(
                    spur_node, end, blocked_zones, blocked_edges)
                if spur_path is not None:
                    full_path = root_path[:-1] + spur_path
                    if full_path not in [c for _, c in candidates]:
                        cost = self.path_cost(full_path)
                        heapq.heappush(candidates, (cost, full_path))
            if not candidates:
                break
            _, next_path = heapq.heappop(candidates)
            all_paths.append(next_path)
        return all_paths

    def path_cost(self, path: list[str]) -> float:
        """Calculate total movement cost of a path."""
        total = 0.0
        for zone_name in path[1:]:
            zone = self._graph.get_zone(zone_name)
            if zone:
                total += self._movement_cost(zone)
        return total
