"""Pygame visualizer for the Fly-in drone routing simulation."""

from typing import Optional
import pygame
from src.models import Graph


class GameConfig:
    """Configuration constants for the visualizer."""

    WIDTH: int = 1280
    HEIGHT: int = 720
    PADDING: int = 80
    FPS: int = 60
    ZONE_RADIUS: int = 28
    DRONE_RADIUS: int = 10
    FONT_SIZE: int = 13
    TITLE_FONT_SIZE: int = 18
    NAMED_COLORS: dict[str, tuple[int, int, int]] = {
        "red":     (200, 60, 60),
        "green":   (60, 180, 60),
        "blue":    (60, 100, 200),
        "yellow":  (210, 190, 40),
        "orange":  (210, 120, 30),
        "cyan":    (40, 200, 200),
        "purple":  (140, 60, 180),
        "gray":    (120, 120, 120),
        "grey":    (120, 120, 120),
        "white":   (230, 230, 230),
        "black":   (40, 40, 40),
        "brown":   (140, 90, 50),
        "pink":    (220, 130, 160),
        "lime":    (130, 210, 50),
        "magenta": (200, 60, 180),
        "gold":    (210, 170, 30),
        "violet":  (140, 80, 200),
        "crimson": (180, 30, 50),
        "maroon":  (120, 30, 30),
        "darkred": (140, 20, 20),
        "rainbow": (100, 180, 220),
    }
    ZONE_DEF_COLORS: dict[str, tuple[int, int, int]] = {
        "normal":     (70, 90, 140),
        "restricted": (160, 60, 60),
        "priority":   (50, 140, 120),
        "blocked":    (50, 50, 50),
        "start":      (60, 160, 60),
        "end":        (200, 160, 30),
    }


class Visualizer:
    """Pygame-based step-by-step visualizer for drone simulations.

    Renders the graph with colored zones and animated drone positions.
    Supports manual stepping and auto-play modes.

    Controls:
        SPACE / RIGHT  — next turn
        LEFT           — previous turn
        A              — toggle auto-play
        R              — restart
        Q / ESC        — quit

    Attributes:
        _graph: The routing graph.
        _turn_log: List of turn strings from the simulator.
        _screen: Pygame display surface.
        _zone_positions: Screen pixel positions per zone name.
    """

    def __init__(self, graph: Graph, turn_log: list[str]) -> None:
        """Initialize the visualizer with a graph and turn log."""
        self._graph = graph
        self._turn_log = turn_log
        self._screen: Optional[pygame.Surface] = None
        self._zone_positions: dict[str, tuple[int, int]] = {}

    def run(self) -> None:
        pass
