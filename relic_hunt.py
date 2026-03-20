"""
relic_hunt.py
-------------
Relic Hunt — a competitive mini-adventure for two local players.

Rules:
  - 10x10 grid arena placed in the Avalon realm (reused from Thang/Sonja).
  - 10 relics are scattered randomly at the start.
  - Players take turns: each turn Player 1 moves, then Player 2 moves.
  - Movement uses WASD (W=up, S=down, A=left, D=right).
  - Landing on a relic automatically collects it (added to the player's
    inventory via the Item/Inventory system from Thang/Sonja's code).
  - First player to collect 5 relics wins.
  - Uses: Realm (realm scene), Item/Inventory (relic collection tracking),
          PlayerProfile (win/loss recording).

Reuse notes (required by assignment):
  - Realm: ctx.realms / ctx.active_realm — sets the adventure in Avalon.
  - Item:  Each collected relic is an Item(name="Relic #N", rarity=RARE)
           appended to the player's inventory_snapshot via profile.update_snapshot().
  - WorldClock: not used heavily here (competitive, not timed), but ctx.clock
                is available if a future variant adds a time limit.
"""

from __future__ import annotations

import random
import re
from typing import List, Optional, Tuple, TYPE_CHECKING

from mini_adventure import MiniAdventure, GameResult
from guildquest import Item, Rarity, PlayerProfile

if TYPE_CHECKING:
    from game_context import GameContext

# ── Constants ──────────────────────────────────────────────────────────────

GRID_SIZE = 10
TOTAL_RELICS = 10
RELICS_TO_WIN = 5

# Input validation: only accept exactly one of W A S D (case-insensitive)
_VALID_INPUT = re.compile(r"^[wasdWASD]$")

# Direction deltas: (row_delta, col_delta)
_DIRECTION: dict[str, Tuple[int, int]] = {
    "W": (-1, 0),
    "S": (1, 0),
    "A": (0, -1),
    "D": (0, 1),
}


class RelicHunt(MiniAdventure):
    """
    Competitive two-player relic collecting game on a 10x10 grid.

    Implements the MiniAdventure interface (Strategy pattern).
    The GameController calls these methods; it never touches internal state
    directly.
    """

    NAME = "Relic Hunt"
    DESCRIPTION = (
        "Race across the Avalon realm to collect 5 relics before your rival! "
        "Take turns moving with WASD. First to 5 relics wins."
    )
    IS_COOPERATIVE = False

    # ── Internal state (all reset by reset()) ──────────────────────────────

    def __init__(self) -> None:
        self._ctx: Optional["GameContext"] = None
        self._p1: Optional[PlayerProfile] = None
        self._p2: Optional[PlayerProfile] = None

        # Positions as (row, col)
        self._pos: List[Tuple[int, int]] = [(0, 0), (9, 9)]

        # Grid: True = relic present, False = empty
        self._grid: List[List[bool]] = []

        # Relic counts collected by each player (index 0 = p1, index 1 = p2)
        self._scores: List[int] = [0, 0]

        # Collected Item objects per player (for inventory snapshot reuse)
        self._collected: List[List[Item]] = [[], []]

        # Whose turn: 0 = p1, 1 = p2
        self._current_player: int = 0

        # Pending feedback lines to surface in get_state_view
        self._feedback: List[str] = []

        self._outcome: GameResult = GameResult.IN_PROGRESS
        self._relic_counter: int = 0  # used to name relics uniquely

    # ── MiniAdventure interface ────────────────────────────────────────────

    def init(self, ctx: "GameContext", p1: PlayerProfile, p2: PlayerProfile) -> None:
        """Set up the board, place relics, position players."""
        self._ctx = ctx
        self._p1 = p1
        self._p2 = p2

        # Use the Avalon realm from the shared context (reuse: Realm subsystem)
        avalon = ctx.get_realm_by_name("Avalon")
        if avalon:
            ctx.active_realm_id = avalon.realm_id

        self._reset_state()

    def get_instructions(self) -> str:
        return (
            "\n=== RELIC HUNT ===\n"
            f"Realm: {self._realm_name()}\n"
            "Rules:\n"
            "  • Players alternate turns.\n"
            f"  • Move with W (up) A (left) S (down) D (right).\n"
            f"  • Collect relics by stepping on them ( R ).\n"
            f"  • First to {RELICS_TO_WIN} relics wins!\n"
            f"  • 1 = Player 1 ({self._p1.character_name if self._p1 else 'P1'})\n"
            f"  • 2 = Player 2 ({self._p2.character_name if self._p2 else 'P2'})\n"
        )

    def get_state_view(self) -> str:
        lines = []

        # ── Feedback from last move ──
        if self._feedback:
            lines.extend(self._feedback)
            self._feedback.clear()

        # ── Scores ──
        p1_name = self._p1.character_name if self._p1 else "Player 1"
        p2_name = self._p2.character_name if self._p2 else "Player 2"
        lines.append(
            f"\n{p1_name}: {self._scores[0]} relics  |  "
            f"{p2_name}: {self._scores[1]} relics"
        )
        lines.append(f"Relics remaining on map: {self._count_relics()}\n")

        # ── Grid ──
        lines.append("  " + " ".join(str(c) for c in range(GRID_SIZE)))
        for r in range(GRID_SIZE):
            row_str = f"{r} "
            for c in range(GRID_SIZE):
                cell = self._cell_char(r, c)
                row_str += cell + " "
            lines.append(row_str)

        # ── Whose turn ──
        current_name = p1_name if self._current_player == 0 else p2_name
        lines.append(f"\n→ {current_name}'s turn (WASD): ")

        return "\n".join(lines)

    def handle_input(self, player_index: int, raw_input: str) -> str:
        """
        Process a move for the player whose turn it currently is.

        Security: rejects anything that isn't a single WASD character.
        Ignores input from the wrong player.
        """
        # ── Security: validate player index ──
        if player_index not in (1, 2):
            return "Invalid player index."

        # ── Enforce turn order ──
        expected = self._current_player + 1  # _current_player is 0-indexed
        if player_index != expected:
            other = 2 if player_index == 1 else 1
            return f"It's Player {other}'s turn, not yours."

        # ── Security: validate + sanitize input ──
        sanitized = raw_input.strip().upper()
        if not _VALID_INPUT.match(sanitized):
            return "Invalid input. Use W (up) A (left) S (down) D (right)."

        # ── Apply move ──
        idx = self._current_player  # 0 or 1
        dr, dc = _DIRECTION[sanitized]
        old_r, old_c = self._pos[idx]
        new_r = max(0, min(GRID_SIZE - 1, old_r + dr))
        new_c = max(0, min(GRID_SIZE - 1, old_c + dc))

        if (new_r, new_c) == self._pos[1 - idx]:
            return "Can't move there — the other player is in that cell."

        self._pos[idx] = (new_r, new_c)
        feedback = f"Player {player_index} moved {sanitized}."

        # ── Check for relic ──
        if self._grid[new_r][new_c]:
            self._grid[new_r][new_c] = False
            self._scores[idx] += 1

            # Reuse: create an Item (Item/Inventory subsystem from Thang/Sonja)
            self._relic_counter += 1
            relic = Item(
                name=f"Relic #{self._relic_counter}",
                description=f"Ancient relic found in {self._realm_name()}.",
                rarity=Rarity.RARE,
            )
            self._collected[idx].append(relic)

            # Update the player's inventory snapshot on their profile
            profile = self._p1 if idx == 0 else self._p2
            if profile:
                profile.update_snapshot(self._collected[idx])

            feedback += f" ✦ Found a relic! ({self._scores[idx]}/{RELICS_TO_WIN})"

        self._feedback.append(feedback)
        return feedback

    def advance_turn(self) -> None:
        """Switch to the other player."""
        self._current_player = 1 - self._current_player

        # Update outcome if someone has won
        if self._scores[0] >= RELICS_TO_WIN:
            self._outcome = GameResult.PLAYER1_WIN
        elif self._scores[1] >= RELICS_TO_WIN:
            self._outcome = GameResult.PLAYER2_WIN

    def is_over(self) -> bool:
        return self._outcome != GameResult.IN_PROGRESS

    def get_outcome(self) -> GameResult:
        return self._outcome

    def reset(self) -> None:
        """Wipe all game state; init() will be called again for a new session."""
        self._reset_state()
        self._outcome = GameResult.IN_PROGRESS
        self._feedback.clear()

    # ── Private helpers ────────────────────────────────────────────────────

    def _reset_state(self) -> None:
        """Initialize / re-initialize board state."""
        self._pos = [(0, 0), (9, 9)]
        self._scores = [0, 0]
        self._collected = [[], []]
        self._current_player = 0
        self._feedback = []
        self._outcome = GameResult.IN_PROGRESS
        self._grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._place_relics()

    def _place_relics(self) -> None:
        """Randomly scatter TOTAL_RELICS relics, avoiding player start positions."""
        occupied = {(0, 0), (9, 9)}
        placed = 0
        while placed < TOTAL_RELICS:
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            if (r, c) not in occupied and not self._grid[r][c]:
                self._grid[r][c] = True
                placed += 1

    def _count_relics(self) -> int:
        return sum(cell for row in self._grid for cell in row)

    def _cell_char(self, row: int, col: int) -> str:
        """Return the display character for a single grid cell."""
        if self._pos[0] == (row, col) and self._pos[1] == (row, col):
            return "!"  # collision (shouldn't happen but safety fallback)
        if self._pos[0] == (row, col):
            return "1"
        if self._pos[1] == (row, col):
            return "2"
        if self._grid[row][col]:
            return "R"
        return "."

    def _realm_name(self) -> str:
        if self._ctx:
            realm = self._ctx.active_realm
            if realm:
                return realm.name
        return "Unknown Realm"