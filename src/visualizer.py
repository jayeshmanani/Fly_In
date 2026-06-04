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
        self._auto_delay: int = 1500
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
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key(event.key)

            if self._auto_play and now - self._last_auto > self._auto_delay:
                if self._current_turn < len(self._turn_log):
                    self._step_forward()
                    self._last_auto = now
                else:
                    self._auto_play = False
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _handle_key(self, key: int) -> bool:
        """Handle a key press. Returns False if the app should quit."""
        if key in (pygame.K_q, pygame.K_ESCAPE):
            return False
        if key == pygame.K_r:
            self._current_turn = 0
            self._auto_play = False
            self._set_drone_pos_start()
        if key in (pygame.K_SPACE, pygame.K_RIGHT):
            if self._current_turn < len(self._turn_log):
                self._step_forward()
        if key == pygame.K_LEFT:
            if self._current_turn > 0:
                self._step_backward()
        if key == pygame.K_a:
            self._auto_play = not self._auto_play
            self._last_auto = pygame.time.get_ticks()
        return True

    def _step_forward(self) -> None:
        """Advance one turn and update drone positions."""
        if self._current_turn >= len(self._turn_log):
            return
        line = self._turn_log[self._current_turn]
        self._apply_turn(line)
        print(f"Turn {self._current_turn + 1}: {line}")
        self._current_turn += 1

    def _step_backward(self) -> None:
        """Rewind to the previous state by replaying from scratch."""
        target = self._current_turn - 1
        self._set_drone_pos_start()
        self._current_turn = 0
        for _ in range(target):
            if self._current_turn < len(self._turn_log):
                line = self._turn_log[self._current_turn]
                self._apply_turn(line)
                self._current_turn += 1

    def _apply_turn(self, line: str) -> None:
        """Parse a turn log line and update drone positions.

        Args:
            line: E.g. 'D1-goal D2-waypoint1'.
        """
        end_zone = self._graph.end_zone
        for token in line.split():
            parts = token.split("-", 1)
            if len(parts) != 2:
                continue
            drone_label, destination = parts
            try:
                drone_id = int(drone_label[1:])
            except ValueError:
                continue
            if destination in self._graph.zones:
                self._drone_positions[drone_id] = destination
                if destination == end_zone:
                    self._arrived.add(drone_id)
            else:
                self._drone_positions[drone_id] = f"~{destination}"

    def _draw(self) -> None:
        """Render the full frame."""
        self._screen.fill(self._cfg.BG_COLOR)
        self._draw_edges()
        self._draw_zones()
        self._draw_drones()
        self._draw_hud()
        self._draw_legend()

    def _draw_drones(self) -> None:
        """Draw all active drones at their current positions."""
        groups: dict[str, list[int]] = {}
        for drone_id, location in self._drone_positions.items():
            # if drone_id not in self._arrived:
            groups.setdefault(location, []).append(drone_id)
        for location, drone_ids in groups.items():
            base_pos = self._resolve_position(location)
            if base_pos is None:
                continue
            count = len(drone_ids)
            for i, drone_id in enumerate(sorted(drone_ids)):
                offset = self._drone_offset(i, count)
                dx = base_pos[0] + offset[0]
                dy = base_pos[1] + offset[1]
                color = self._drone_color(drone_id)
                in_transit = location.startswith("~")
                border = self._cfg.TRANSIT_COLOR if in_transit else (
                    255, 255, 255)
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

    def _resolve_position(
            self, location: str
    ) -> Optional[tuple[int, int]]:
        """Position on the edge between two zones, or at a zone center."""
        if location.startswith("~"):
            conn_str = location[1:]
            parts = conn_str.split("-", 1)
            if len(parts) == 2:
                pos_a = self._zone_positions.get(parts[0])
                pos_b = self._zone_positions.get(parts[1])
                if pos_a and pos_b:
                    return (
                        (pos_a[0] + pos_b[0]) // 2,
                        (pos_a[1] + pos_b[1]) // 2,
                    )
            return None
        return self._zone_positions.get(location)

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

        span_x = max_x - min_x
        span_y = max_y - min_y

        draw_w = self._cfg.WIDTH - 2 * self._cfg.PADDING
        draw_h = self._cfg.HEIGHT - 2 * self._cfg.PADDING - 200

        for zone in zones:
            if span_x == 0:
                px = self._cfg.WIDTH // 2
            else:
                px = int(self._cfg.PADDING +
                         (zone.x - min_x) / span_x * draw_w)
            if span_y == 0:
                py = (self._cfg.HEIGHT - 60) // 2
            else:
                py = int(self._cfg.PADDING +
                         (zone.y - min_y) / span_y * draw_h)

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

    def _draw_hud(self) -> None:
        """Draw the heads-up display bar at the bottom."""
        hud_y = self._cfg.HEIGHT - 60
        pygame.draw.rect(
            self._screen, self._cfg.HUD_BG, (0, hud_y, self._cfg.WIDTH, 60)
        )

        total_turns = len(self._turn_log)
        status = "AUTO" if self._auto_play else "STEP"
        arrived = len(self._arrived)
        n = self._graph.nb_drones

        lines = [
            f"Turn: {self._current_turn}/{total_turns}  "
            f"Drones: {arrived}/{n} arrived  "
            f"Mode: {status}",
            "SPACE/→ next  ←  prev  A auto-play  R restart  Q quit",
        ]

        for i, text in enumerate(lines):
            surf = self._hud_font.render(text, True, self._cfg.HUD_COLOR)
            self._screen.blit(surf, (16, hud_y + 8 + i * 20))

    def _draw_legend(self) -> None:
        legend_colors: dict[str, list[tuple[int, int, int]]] = {}

        for zone in self._graph.zones.values():
            key = "Start" if zone.is_start else "End"\
                  if zone.is_end else zone.zone_type.value.title()
            color = self._resolve_color(
                zone.color, zone.zone_type, zone.is_start, zone.is_end)

            if color not in legend_colors.setdefault(key, []):
                legend_colors[key].append(color)

        x, y = self._cfg.WIDTH - 200, self._cfg.HEIGHT - 120
        bg_height = len(legend_colors) * 22 + 8
        pygame.draw.rect(
            self._screen,
            (50, 50, 50),
            (x - 10, y - 10, 200, bg_height),
            border_radius=5
        )
        for label, colors in legend_colors.items():
            for i, color in enumerate(colors[:3]):
                pygame.draw.circle(self._screen, color, (x + i * 20, y + 6), 5)

            self._screen.blit(self._font.render(
                label, True, self._cfg.LABEL_COLOR), (x + 75, y))
            y += 22
