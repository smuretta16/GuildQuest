"""
mini_adventure.py
-----------------
Defines the MiniAdventure interface (Strategy pattern) that ALL mini-adventures
must implement.

To add a new mini-adventure:
  1. Create a new file, e.g. my_adventure.py
  2. Import and subclass MiniAdventure
  3. Implement every method below (raise NotImplementedError if you skip one)
  4. Register it in gmae.py -> GameController._register_adventures()

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_context import GameContext
    from guildquest import PlayerProfile


class GameResult(Enum):
    """All possible outcomes a mini-adventure can produce."""
    PLAYER1_WIN = "PLAYER1_WIN"
    PLAYER2_WIN = "PLAYER2_WIN"
    TIE = "TIE"
    COOPERATIVE_WIN = "COOPERATIVE_WIN"   # both players win together
    COOPERATIVE_LOSS = "COOPERATIVE_LOSS" # both players lose together
    IN_PROGRESS = "IN_PROGRESS"           # game not finished yet


class MiniAdventure(ABC):
    """
    Abstract base class for all GMAE mini-adventures.

    The GameController always talks to mini-adventures through this interface,
    so the controller never needs to know which specific adventure is running.

    Lifecycle (called in this order by GameController):
        1. __init__   - called once when the class is instantiated
        2. init()     - called each time a new game session starts
        3. loop:
              get_state_view()  -> print state
              handle_input()    -> accept one player's move
              advance_turn()    -> move game forward
              is_over()         -> check if done
        4. get_outcome()  - called once when is_over() returns True
        5. reset()        - called if players want to replay
    """

    # ── Identity (subclasses should override these as class attributes) ────

    NAME: str = "Unnamed Adventure"
    DESCRIPTION: str = "No description provided."
    MIN_PLAYERS: int = 2
    MAX_PLAYERS: int = 2
    IS_COOPERATIVE: bool = False  # False = competitive, True = co-op

    # ── Lifecycle ──────────────────────────────────────────────────────────

    @abstractmethod
    def init(self, ctx: "GameContext", p1: "PlayerProfile", p2: "PlayerProfile") -> None:
        """
        Set up a fresh game session.

        Args:
            ctx: Shared GuildQuest systems (clock, realms, etc.)
            p1:  Player 1's profile
            p2:  Player 2's profile
        """
        ...

    @abstractmethod
    def get_instructions(self) -> str:
        """
        Return a human-readable string explaining how to play.
        Printed once before the game loop starts.
        """
        ...

    @abstractmethod
    def get_state_view(self) -> str:
        """
        Return a text snapshot of the current game state.
        Called every turn so players can see what's happening.
        Should include: board/map, scores, remaining time, objectives, etc.
        """
        ...

    @abstractmethod
    def handle_input(self, player_index: int, raw_input: str) -> str:
        """
        Process one player's action for this turn.

        Args:
            player_index: 1 or 2
            raw_input:    The raw string typed by the player (already stripped)

        Returns:
            A short feedback string to print back to the player,
            e.g. "Moved UP." or "Invalid move – use WASD."

        Security note: validate/sanitize raw_input here. Never trust it.
        """
        ...

    @abstractmethod
    def advance_turn(self) -> None:
        """
        Advance the game state by one step (e.g., move NPCs, tick timers,
        apply hazards). Called after both players have submitted input.
        """
        ...

    @abstractmethod
    def is_over(self) -> bool:
        """Return True when the game has ended (win, loss, or tie)."""
        ...

    @abstractmethod
    def get_outcome(self) -> GameResult:
        """
        Return the final result of the game.
        Only called after is_over() returns True.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset all game state so the adventure can be replayed from scratch.
        init() will be called again after reset() if players choose to replay.
        """
        ...

 
    def on_player_win(self, profile: "PlayerProfile") -> None:
        """Called by GameController to update profile stats on win."""
        profile.record_win()

    def on_player_loss(self, profile: "PlayerProfile") -> None:
        """Called by GameController to update profile stats on loss."""
        profile.record_loss()

    def on_complete(self, profile: "PlayerProfile") -> None:
        """Called for co-op completions. Updates profile accordingly."""
        profile.record_quest(self.NAME)