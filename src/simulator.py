
"""Turn-based simulation engine for the Fly-in drone routing."""

from src.models import Drone, Graph


class Simulator:
    """Simulate drone movement through a graph of zones and connections."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the simulator with a graph."""
        self._graph = graph
        self._drones: list[Drone] = []
        self._turn: int = 0
        self._turn_log: list[str] = []

    def _all_drones_reached(self) -> bool:
        """Check if all drones have reached the end zone."""
        return all(drone.has_arrived() for drone in self._drones)

    def run(self) -> list[str]:
        """Run the simulation until all drones have reached the end zone."""
        max_turns = 1000
        while not self._all_drones_reached() and self._turn < max_turns:
            self._turn += 1
            self._turn_log.append(f"Turn {self._turn}:")
        return self._turn_log

    def get_turn_count(self) -> int:
        """Return the number of turns the simulation took."""
        return self._turn
