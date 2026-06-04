
"""Turn-based simulation engine for the Fly-in drone routing."""

from src.models import (Drone, Graph, ZoneState,
                        ConnectionState, DroneStatus, ZoneType,
                        Connection, Zone)
from src.pathfinder import PathFinder
from src.exceptions import ParseError
from typing import Optional


class Simulator:
    """Simulate drone movement through a graph of zones and connections."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the simulator with a graph."""
        self._graph = graph
        self._drones: list[Drone] = []
        self._finder: PathFinder = PathFinder(graph)
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
        max_turns = 100
        self._setup_drones()
        while not self._all_drones_reached() and self._turn < max_turns:
            self._turn += 1
            moves = self._advance_turn()
            if moves:
                self._turn_log.append(" ".join(moves))
                stale = 0
            else:
                stale += 1
                if stale >= 5:
                    self._force_reroute_all()
                    stale = 0
        return self._turn_log

    def _force_reroute_all(self) -> None:
        """Force reroute all stuck drones when deadlock detected."""
        for drone in self._active_drones():
            if drone.status != DroneStatus.WAITING:
                continue
            end = self._graph.end_zone
            new_path = self._finder.find_shortest_path(
                drone.current_zone, end
            )
            if new_path and len(new_path) >= 2:
                history = drone.path[: drone.path_index + 1]
                drone.path = history + new_path[1:]
                drone.path_index = len(history) - 1

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

    def _advance_turn(self) -> list[str]:
        moves: list[str] = []
        just_arrived: set[int] = set()
        for drone in self._active_drones():
            if drone.status == DroneStatus.IN_TRANSIT:
                drone.transit_turns_left -= 1
                if drone.transit_turns_left == 0:
                    result = self._arrive_from_transit(drone)
                    if result:
                        moves.append(result)
                        just_arrived.add(drone.drone_id)
        waiting = [
            d for d in self._active_drones()
            if d.status == DroneStatus.WAITING
            and d.drone_id not in just_arrived
        ]
        waiting.sort(key=lambda d: self._steps_remaining(d))
        for drone in waiting:
            if drone.transit_turns_left > 0:
                drone.transit_turns_left -= 1
                continue
            result = self._try_move_drone(drone)
            if result:
                moves.append(result)
        moves.sort(key=lambda x: int(x.split("-")[0][1]))
        return moves

    def _steps_remaining(self, drone: Drone) -> int:
        """Return how many steps remain in drone's current path."""
        if not drone.path:
            return 999
        return len(drone.path) - drone.path_index - 1

    def _arrive_from_transit(self, drone: Drone) -> Optional[str]:
        dest_name = drone.transit_destination
        if dest_name is None:
            return None

        zone_state = self._zone_states.get(dest_name)
        if zone_state is None:
            return None

        conn = self._graph.get_connection(drone.current_zone, dest_name)
        if conn is None:
            for c_state in self._conn_states.values():
                if drone.drone_id in c_state.drones:
                    c_state.drones.discard(drone.drone_id)
                    break
        else:
            self._conn_states[conn.key()].drones.discard(drone.drone_id)

        zone_state.drones.add(drone.drone_id)
        drone.current_zone = dest_name
        drone.path_index += 1
        drone.status = DroneStatus.WAITING
        drone.transit_destination = None

        if dest_name == self._graph.end_zone:
            drone.status = DroneStatus.ARRIVED
            zone_state.drones.discard(drone.drone_id)
        return f"{drone.label}-{dest_name}"

    def _try_move_drone(self, drone: Drone) -> Optional[str]:
        next_name = drone.next_zone()
        if next_name is None:
            return None
        next_zone = self._graph.get_zone(next_name)
        if next_zone is None:
            return None

        conn = self._graph.get_connection(drone.current_zone, next_name)
        if conn is None:
            return None

        conn_state = self._conn_states.get(conn.key())
        zone_state = self._zone_states.get(next_name)

        if conn_state is None and zone_state is None:
            return None
        if conn_state and not conn_state.has_capacity():
            return None
        if next_zone.zone_type == ZoneType.RESTRICTED:
            return self._start_transit(drone, conn, next_zone)
        if zone_state and not zone_state.has_capacity():
            return None
        return self._execute_move(drone, conn, next_zone)

    def _start_transit(
        self, drone: Drone, conn: Connection, dest: Zone
    ) -> Optional[str]:
        conn_state = self._conn_states.get(conn.key())
        if conn_state is None or not conn_state.has_capacity():
            return None
        self._zone_states[drone.current_zone].drones.discard(
            drone.drone_id
        )
        conn_state.drones.add(drone.drone_id)

        drone.status = DroneStatus.IN_TRANSIT
        drone.transit_turns_left = 1
        drone.transit_destination = dest.name

        conn_name = f"{conn.zone_a}-{conn.zone_b}"
        return f"{drone.label}-{conn_name}"

    def _execute_move(
        self, drone: Drone, conn: Connection, dest: Zone
    ) -> str:
        self._zone_states[drone.current_zone].drones.discard(
            drone.drone_id
        )

        conn_state = self._conn_states[conn.key()]
        conn_state.drones.add(drone.drone_id)

        dest_state = self._zone_states[dest.name]
        dest_state.drones.add(drone.drone_id)

        conn_state.drones.discard(drone.drone_id)

        drone.current_zone = dest.name
        drone.path_index += 1
        drone.status = DroneStatus.WAITING

        if dest.name == self._graph.end_zone:
            drone.status = DroneStatus.ARRIVED
            dest_state.drones.discard(drone.drone_id)

        return f"{drone.label}-{dest.name}"
