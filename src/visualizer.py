"""Pygame visualizer for the Fly-in drone routing simulation."""

import pygame
import math
from typing import Optional
from src.models import Graph, ZoneType


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
    DRONE_PALETTE: list[tuple[int, int, int]] = [
        (255, 80, 80), (80, 200, 80), (80, 120, 255),
        (255, 200,   0), (255, 120, 200), (0, 220, 220),
        (255, 160, 40), (180, 80, 255), (120, 255, 160),
        (255, 80, 160), (80, 255, 220), (200, 200, 80),
        (255, 140, 100), (100, 180, 255), (200, 255, 80),
        (255, 80, 220), (80, 200, 160), (220, 140, 255),
        (255, 220, 120), (120, 255, 200), (255, 100, 100),
        (100, 255, 100), (100, 100, 255), (255, 255, 100),
        (255, 100, 255),
    ]


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

            import time
            time.sleep(5)
            break
        pygame.quit()

    def _draw(self) -> None:
        """Render the full frame."""
        self._screen.fill(self._cfg.BG_COLOR)
        self._draw_edges()
        self._draw_zones()
        self._draw_drones()

    def _draw_drones(self) -> None:
        """Draw all active drones at their current positions."""
        groups: dict[str, list[int]] = {}
        for drone_id, location in self._drone_positions.items():
            if drone_id not in self._arrived:
                groups.setdefault(location, []).append(drone_id)
        for location, drone_ids in groups.items():
            base_pos = self._zone_positions.get(location)
            if base_pos is None:
                continue
            count = len(drone_ids)
            for i, drone_id in enumerate(sorted(drone_ids)):
                offset = self._drone_offset(i, count)
                dx = base_pos[0] + offset[0]
                dy = base_pos[1] + offset[1]
                color = self._drone_color(drone_id)
                border = (255, 255, 255)
                pygame.draw.circle(
                    self._screen, color, (dx, dy), self._cfg.DRONE_RADIUS
                )
                pygame.draw.circle(
                    self._screen, border, (dx, dy), self._cfg.DRONE_RADIUS, 2
                )
                label = self._font.render(
                    f"D{drone_id}", True, (10, 10, 10)
                )
                lx = dx - label.get_width() // 2
                ly = dy - label.get_height() // 2
                self._screen.blit(label, (lx, ly))

    def _draw_zones(self) -> None:
        """Draw each zone as a coloured circle with label."""
        for name, zone in self._graph.zones.items():
            pos = self._zone_positions.get(name)
            if pos is None:
                continue

            color = self._resolve_color(
                zone.color, zone.zone_type, zone.is_start, zone.is_end
            )

            if zone.zone_type == ZoneType.RESTRICTED:
                if not zone.color:
                    color = (200, 80, 80)
                pygame.draw.circle(
                    self._screen, color, pos, self._cfg.ZONE_RADIUS + 4, 2
                )
            elif zone.zone_type == ZoneType.PRIORITY:
                if not zone.color:
                    color = (80, 220, 180)
                pygame.draw.circle(
                    self._screen, color, pos, self._cfg.ZONE_RADIUS + 4, 2
                )

            pygame.draw.circle(self._screen, color, pos, self._cfg.ZONE_RADIUS)
            pygame.draw.circle(
                self._screen, self._cfg.LABEL_COLOR, pos,
                self._cfg.ZONE_RADIUS, 1
            )

            label = self._font.render(name, True, self._cfg.LABEL_COLOR)
            lx = pos[0] - label.get_width() // 2
            ly = pos[1] + self._cfg.ZONE_RADIUS + 4
            self._screen.blit(label, (lx, ly))

            if zone.max_drones > 1 and zone.max_drones < 999999:
                cap_surf = self._font.render(
                    f"[{zone.max_drones}]", True, (180, 180, 100)
                )
                cx = pos[0] - cap_surf.get_width() // 2
                cy = pos[1] - self._cfg.ZONE_RADIUS - 14
                self._screen.blit(cap_surf, (cx, cy))

    def _draw_edges(self) -> None:
        """Draw connection lines between zones."""
        for conn in self._graph.connections:
            pos_a = self._zone_positions.get(conn.zone_a)
            pos_b = self._zone_positions.get(conn.zone_b)
            if pos_a is None or pos_b is None:
                continue
            cap = conn.max_link_capacity > 1
            color = self._cfg.EDGE_CAP_COLOR if cap else self._cfg.EDGE_COLOR
            width = 1 + conn.max_link_capacity
            pygame.draw.line(self._screen, color, pos_a, pos_b, width)

            if conn.max_link_capacity > 1:
                mid = (
                    (pos_a[0] + pos_b[0]) // 2,
                    (pos_a[1] + pos_b[1]) // 2,
                )
                surf = self._font.render(
                    f"×{conn.max_link_capacity}", True,
                    self._cfg.EDGE_CAP_COLOR
                )
                self._screen.blit(surf, (mid[0] - 8, mid[1] - 8))

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

    def _drone_offset(
        self, index: int, total: int
    ) -> tuple[int, int]:
        """Compute a small offset so multiple drones don't overlap at same loc.

        Args:
            index: This drone's position in the group.
            total: Total drones in the group.

        Returns:
            (dx, dy) pixel offset from zone center.
        """
        if total == 1:
            return (0, 0)
        angle = (2 * math.pi * index) / total
        r = self._cfg.ZONE_RADIUS - self._cfg.DRONE_RADIUS - 2
        return (int(r * math.cos(angle)), int(r * math.sin(angle)))

    def _drone_color(self, drone_id: int) -> tuple[int, int, int]:
        """Return a distinct colour for a drone by ID."""
        return self._cfg.DRONE_PALETTE[
            (drone_id - 1) % len(self._cfg.DRONE_PALETTE)
        ]

    def _resolve_color(self,
                       color_str: Optional[str],
                       zone_type: ZoneType,
                       is_start: bool,
                       is_end: bool,
                       ) -> tuple[int, int, int]:
        """Return an RGB tuple for a zone based on metadata and type."""
        if color_str:
            named = self._cfg.NAMED_COLORS.get(color_str.lower())
            if named:
                return named
        if is_start:
            return self._cfg.ZONE_DEF_COLORS["start"]
        if is_end:
            return self._cfg.ZONE_DEF_COLORS["end"]
        return self._cfg.ZONE_DEF_COLORS.get(zone_type.value,
                                             self._cfg.
                                             ZONE_DEF_COLORS["normal"])
