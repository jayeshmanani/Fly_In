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
    HUD_FONT_SIZE: int = 15
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
    BG_COLOR = (18, 18, 28)
    EDGE_COLOR = (60, 60, 80)
    EDGE_CAP_COLOR = (100, 80, 40)
    LABEL_COLOR = (220, 220, 220)
    HUD_COLOR = (240, 240, 240)
    HUD_BG = (30, 30, 45)
    ARRIVED_COLOR = (50, 200, 80)
    TRANSIT_COLOR = (255, 180, 0)


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
        self._current_turn: int = 0
        self._auto_play: bool = False
        self._auto_delay: int = 800
        self._last_auto: int = 0
        self._zone_positions: dict[str, tuple[int, int]] = {}
        self._drone_positions: dict[int, str] = {}
        self._arrived: set[int] = set()
        self._cfg = GameConfig()
        pygame.init()
        self._screen = pygame.display.\
            set_mode((self._cfg.WIDTH, self._cfg.HEIGHT))
        pygame.display.set_caption("Fly-in — Drone Routing Simulation")
        self._clock = pygame.time.Clock()
        self._font = pygame.font.SysFont("monospace", self._cfg.FONT_SIZE)
        self._title_font = pygame.font.SysFont("monospace",
                                               self._cfg.TITLE_FONT_SIZE,
                                               bold=True)
        self._hud_font = pygame.font.SysFont(
            "monospace", self._cfg.HUD_FONT_SIZE)
        self._compute_layout()
        self._set_drone_pos_start()

    def run(self) -> None:
        running = True
        while running:
            self._clock.tick(self._cfg.FPS)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _draw(self) -> None:
        """Render the full frame."""
        self._screen.fill(self._cfg.BG_COLOR)

    def _set_drone_pos_start(self) -> None:
        """Place all drones at the start zone."""
        self._drone_positions = {}
        self._arrived = set()
        n = self._graph.nb_drones
        start = self._graph.start_zone
        for i in range(1, n + 1):
            self._drone_positions[i] = start

    def _compute_layout(self) -> None:
        """Map zone grid coordinates to screen pixel positions."""
        zones = self._graph.zones.values()
        if not zones:
            return

        xs = [z.x for z in zones]
        ys = [z.y for z in zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        draw_w = self._cfg.WIDTH - 2 * self._cfg.PADDING
        draw_h = self._cfg.HEIGHT - 2 * self._cfg.PADDING - 80

        for zone in zones:
            px = int(self._cfg.PADDING + (zone.x - min_x) / span_x * draw_w)
            py = int(self._cfg.PADDING + (zone.y - min_y) / span_y * draw_h)
            self._zone_positions[zone.name] = (px, py)
