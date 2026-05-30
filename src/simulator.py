
"""Turn-based simulation engine for the Fly-in drone routing."""

from src.models import Drone, Graph
from src.models import ZoneState, ConnectionState


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
        while not self._all_drones_reached() and self._turn < max_turns:
            self._turn += 1
            self._turn_log.append(f"Turn {self._turn}:")
        return self._turn_log

    def get_turn_count(self) -> int:
        """Return the number of turns the simulation took."""
        return self._turn

    def _setup_drones(self) -> None:
        """Initialize drones in the start zone."""
        for i in range(1, self._graph.nb_drones + 1):
            drone = Drone(drone_id=i, current_zone=self._graph.start_zone)
            self._drones.append(drone)
            self._zone_states[self._graph.start_zone].drones.add(
                drone.drone_id)

    def _all_drones_reached(self) -> bool:
        """Check if all drones have reached the end zone."""
        return all(drone.has_arrived() for drone in self._drones)

    def _active_drones(self) -> list[Drone]:
        """Return list of drones that have not yet reached the end zone."""
        return [drone for drone in self._drones if not drone.has_arrived()]
