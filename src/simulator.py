
"""Turn-based simulation engine for the Fly-in drone routing."""

from src.models import Drone, Graph
from src.models import ZoneState, ConnectionState
from src.pathfinder import PathFinder
from src.exceptions import ParseError
from typing import Optional


class Simulator:
    """Simulate drone movement through a graph of zones and connections."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the simulator with a graph."""
        self._graph = graph
        self._drones: list[Drone] = []
        self._turn: int = 0
        self._turn_log: list[str] = []
        self._zone_states: dict[str, ZoneState] = {
            name: ZoneState(zone=zone)
            for name, zone in graph.zones.items()
        }
        self._conn_states: dict[tuple[str, str], ConnectionState] = {
            conn.key(): ConnectionState(connection=conn)
            for conn in graph.connections
        }

    def run(self) -> list[str]:
        """Run the simulation until all drones have reached the end zone."""
        max_turns = 10
        self._setup_drones()
        print(f"Initial drone assignments: {[str(d) for d in self._drones]}")
        print(f"Path Assignments: {[{d.drone_id: d.path for d in self._drones}]}")
        while not self._all_drones_reached() and self._turn < max_turns:
            self._turn += 1
            self._turn_log.append(f"Turn {self._turn}:")
        return self._turn_log

    def get_turn_count(self) -> int:
        """Return the number of turns the simulation took."""
        return self._turn

    def _setup_drones(self) -> None:
        """Initialize drones in the start zone."""
        finder = PathFinder(self._graph)
        k = min(self._graph.nb_drones, 8)
        paths = finder.find_k_shortest_paths(
            self._graph.start_zone, self._graph.end_zone, k
        )
        if not paths:
            raise ParseError(
                0, "No path found from start to end zone"
            )
        self._drones = self._assign_paths(paths)

        start = self._graph.start_zone
        for drone in self._drones:
            self._zone_states[start].drones.add(drone.drone_id)

    def _get_zone_state(self, name: str) -> Optional[ZoneState]:
        """Return zone state by name."""
        return self._zone_states.get(name)

    def _all_drones_reached(self) -> bool:
        """Check if all drones have reached the end zone."""
        return all(drone.has_arrived() for drone in self._drones)

    def _active_drones(self) -> list[Drone]:
        """Return list of drones that have not yet reached the end zone."""
        return [drone for drone in self._drones if not drone.has_arrived()]

    def _assign_paths(self, paths: list[list[str]]) -> list[Drone]:
        """Distribute drones across available paths.

        Drones are assigned round-robin across paths, favouring
        shorter/cheaper paths. Within each path, drones are
        staggered by one turn to avoid zone conflicts.

        Args:
            paths: Ordered list of paths (cheapest first).

        Returns:
            List of Drone objects with paths and departure turns set.
        """
        drones: list[Drone] = []
        n = self._graph.nb_drones
        print(f"Assigning {n} drones across {len(paths)} paths")
        path_capacities = [self._path_capacity(p) for p in paths]
        assignments: list[list[int]] = [[] for _ in paths]

        drone_id = 1
        while drone_id <= n:
            for idx, path in enumerate(paths):
                cap = path_capacities[idx]
                assigned = len(assignments[idx])
                if assigned < cap and drone_id <= n:
                    assignments[idx].append(drone_id)
                    drone_id += 1

            if drone_id <= n and all(
                len(assignments[idx]) >= path_capacities[idx]
                for idx in range(len(paths))
            ):
                path_capacities = [c + 1 for c in path_capacities]

        for path_idx, drone_ids in enumerate(assignments):
            path = paths[path_idx]
            for slot, d_id in enumerate(drone_ids):
                drone = Drone(
                    drone_id=d_id,
                    path=path,
                    current_zone=self._graph.start_zone,
                    path_index=0,
                )
                drone.transit_turns_left = slot
                drones.append(drone)
        drones.sort(key=lambda d: d.drone_id)
        return drones

    def _path_capacity(self, path: list[str]) -> int:
        """Return the minimum link/zone capacity along a path.

        Args:
            path: Ordered list of zone names.

        Returns:
            Bottleneck capacity (minimum along the path).
        """
        cap = 999
        for i in range(len(path) - 1):
            conn = self._graph.get_connection(path[i], path[i + 1])
            if conn:
                cap = min(cap, conn.max_link_capacity)
            zone = self._graph.get_zone(path[i + 1])
            if zone and not zone.is_end:
                cap = min(cap, zone.max_drones)
        return max(1, cap)
