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
