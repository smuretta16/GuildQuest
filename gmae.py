"""
gmae.py
-------
GuildQuest Mini-Adventure Environment (GMAE) entry point.

Responsibilities:
  - Two-player profile setup (enforces exactly 2 local players).
  - MiniAdventureRegistry: holds all available mini-adventures.
  - GameController: owns the main game loop; talks to adventures only through
    the MiniAdventure interface (Strategy pattern).
  - ResultTracker: writes win/loss/quest outcomes back to PlayerProfiles and
    persists them via guildquest.save_profiles().

To add a NEW mini-adventure:
  1. Create your file (e.g. timed_raid.py) and subclass MiniAdventure.
  2. Import it here.
  3. Add one line to GameController._register_adventures():
         self.registry.register(TimedRaid())
  That's the only change needed in this file.

Run:
    python gmae.py
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Type

from guildquest import GuildQuestGame, PlayerProfile, User, save_profiles
from game_context import GameContext
from mini_adventure import MiniAdventure, GameResult

#  Import mini-adventures here 
from relic_hunt import RelicHunt
# from timed_raid import TimedRaid   ← teammates add theirs here


#  Security: safe profile name pattern 
_SAFE_NAME = re.compile(r"^[a-zA-Z0-9 _\-]{1,40}$")



# MiniAdventureRegistry


class MiniAdventureRegistry:
    """
    Holds all available mini-adventures and provides metadata for the menu.

    Mini-adventures are stored by their NAME class attribute.
    The registry never runs game logic — it just knows what exists.
    """

    def __init__(self) -> None:
        self._adventures: Dict[str, MiniAdventure] = {}

    def register(self, adventure: MiniAdventure) -> None:
        """Add a mini-adventure instance to the registry."""
        self._adventures[adventure.NAME] = adventure

    def all(self) -> List[MiniAdventure]:
        """Return all registered adventures in insertion order."""
        return list(self._adventures.values())

    def get(self, name: str) -> Optional[MiniAdventure]:
        return self._adventures.get(name)

    def count(self) -> int:
        return len(self._adventures)



# ResultTracker


class ResultTracker:
    """
    Translates a GameResult into profile stat updates and persists them.

    Called by GameController after every completed adventure so profiles
    stay in sync with outcomes automatically.
    """

    def record(
        self,
        result: GameResult,
        adventure: MiniAdventure,
        p1: PlayerProfile,
        p2: PlayerProfile,
        users: Dict[int, User],
    ) -> None:
        if result == GameResult.PLAYER1_WIN:
            adventure.on_player_win(p1)
            adventure.on_player_loss(p2)
        elif result == GameResult.PLAYER2_WIN:
            adventure.on_player_win(p2)
            adventure.on_player_loss(p1)
        elif result == GameResult.TIE:
            # Ties count as a quest completion but no win/loss
            p1.record_quest(adventure.NAME)
            p2.record_quest(adventure.NAME)
        elif result in (GameResult.COOPERATIVE_WIN, GameResult.COOPERATIVE_LOSS):
            adventure.on_complete(p1)
            adventure.on_complete(p2)

        save_profiles(users)
        print("\n✔ Results saved to profiles.")



# GameController


class GameController:
    """
    Owns the GMAE main loop.

    Enforces:
      - Exactly 2 local players.
      - Profile setup before any adventure starts.
      - Clean separation: talks to mini-adventures only via MiniAdventure API.
    """

    def __init__(self) -> None:
        self.gq = GuildQuestGame()       # the full GuildQuest backend (reused)
        self.registry = MiniAdventureRegistry()
        self.tracker = ResultTracker()
        self._register_adventures()

        # Two player profiles: set during _setup_players()
        self._p1: Optional[PlayerProfile] = None
        self._p2: Optional[PlayerProfile] = None

    #  Adventure registration 

    def _register_adventures(self) -> None:
        """
        Add every available mini-adventure here.
        Teammates: add your import at the top of this file, then add a line below.
        """
        self.registry.register(RelicHunt())
        # self.registry.register(TimedRaid())   ← example for teammates

    #  Entry point 

    def run(self) -> None:
        print("\n╔══════════════════════════════════════╗")
        print("║   GuildQuest Mini-Adventure Env.    ║")
        print("╚══════════════════════════════════════╝")

        self._setup_players()

        while True:
            choice = self._show_main_menu()
            if choice == "q":
                save_profiles(self.gq.users)
                print("Farewell, adventurers!")
                break
            adventure = self.registry.all()[choice]
            self._run_adventure(adventure)

    #  Player setup 

    def _setup_players(self) -> None:
        """
        Ensure exactly two players have profiles before play begins.
        Enforces: 2 local players, no more, no less.
        """
        print("\n── Player Setup (2 players required) ──")
        users = sorted(self.gq.users.values(), key=lambda u: u.user_id)

        print("\nExisting users:")
        for u in users:
            profile_info = f" | {u.profile.character_name}" if u.profile else " (no profile)"
            print(f"  [{u.user_id}] {u.name}{profile_info}")

        print("\nSelect or create Player 1 and Player 2.")
        self._p1 = self._get_or_create_profile("Player 1")
        self._p2 = self._get_or_create_profile("Player 2")

        print(f"\n✔ Player 1: {self._p1.character_name} ({self._p1.preferred_realm})")
        print(f"✔ Player 2: {self._p2.character_name} ({self._p2.preferred_realm})")

    def _get_or_create_profile(self, label: str) -> PlayerProfile:
        """
        Let a player pick an existing profile or create a new one.
        Validates character name for safety.
        """
        users_with_profiles = [u for u in self.gq.users.values() if u.profile]
        all_users = sorted(self.gq.users.values(), key=lambda u: u.user_id)

        print(f"\n{label}:")
        print("  1. Use existing profile")
        print("  2. Create new profile")
        pick = self._read_int("> ", 1, 2)

        if pick == 1 and users_with_profiles:
            print("  Choose user:")
            for i, u in enumerate(users_with_profiles, 1):
                print(f"    {i}. [{u.user_id}] {u.name} — {u.profile.character_name}")
            idx = self._read_int("  > ", 1, len(users_with_profiles))
            return users_with_profiles[idx - 1].profile

        # Create a new profile
        while True:
            char_name = input(f"  Character name for {label}: ").strip()
            # Security: validate name input
            if not _SAFE_NAME.match(char_name):
                print("  Name must be 1–40 characters (letters, numbers, spaces, _ -).")
                continue
            break

        realms = sorted(self.gq.realms.values(), key=lambda r: r.realm_id)
        print("  Choose preferred realm:")
        for i, r in enumerate(realms, 1):
            print(f"    {i}. {r.name}")
        ridx = self._read_int("  > ", 1, len(realms))
        preferred_realm = realms[ridx - 1].name

        # Assign to next available user slot or create a new user
        new_uid = self.gq.next_user_id
        self.gq.next_user_id += 1
        from guildquest import User
        new_user = User(new_uid, char_name)
        new_user.profile = PlayerProfile(
            character_name=char_name,
            preferred_realm=preferred_realm,
        )
        self.gq.users[new_uid] = new_user
        save_profiles(self.gq.users)
        return new_user.profile

    #  Main menu 

    def _show_main_menu(self) -> "int | str":
        """Display the mini-adventure selection menu. Returns index or 'q'."""
        adventures = self.registry.all()
        print("\n╔══════════════════════════════════════╗")
        print("║       Choose a Mini-Adventure       ║")
        print("╠══════════════════════════════════════╣")
        for i, adv in enumerate(adventures, 1):
            mode = "Co-op" if adv.IS_COOPERATIVE else "Competitive"
            print(f"║  {i}. {adv.NAME:<34}║")
            print(f"║     [{mode}] {adv.DESCRIPTION[:30]:<30}  ║")
        print("╠══════════════════════════════════════╣")
        print("║  Q. Quit                            ║")
        print("╚══════════════════════════════════════╝")

        while True:
            raw = input("> ").strip().lower()
            if raw == "q":
                return "q"
            try:
                n = int(raw)
                if 1 <= n <= len(adventures):
                    return n - 1
            except ValueError:
                pass
            print(f"Enter 1–{len(adventures)} or Q.")

    #  Adventure runner 

    def _run_adventure(self, adventure: MiniAdventure) -> None:
        """Run one full session of a mini-adventure."""

        # Build the shared GameContext from live GuildQuest data (reuse)
        ctx = GameContext(
            clock=self.gq.clock,
            realms=self.gq.realms,
        )

        # Initialise the adventure (Strategy pattern: init via interface)
        adventure.init(ctx, self._p1, self._p2)

        print(adventure.get_instructions())
        input("Press Enter to start...")

        #  Main game loop 
        while not adventure.is_over():
            print(adventure.get_state_view())

            # Determine whose input to collect this turn
            # (each adventure manages turn order internally, but we ask
            #  both players sequentially so input is never shared)
            for player_idx in (1, 2):
                if adventure.is_over():
                    break
                raw = input(f"Player {player_idx} input: ").strip()
                feedback = adventure.handle_input(player_idx, raw)
                print(f"  → {feedback}")

            adventure.advance_turn()

        #  Game over 
        print(adventure.get_state_view())
        result = adventure.get_outcome()
        self._print_outcome(result, adventure)

        # Record results into profiles
        self.tracker.record(result, adventure, self._p1, self._p2, self.gq.users)

        # Offer replay
        replay = input("\nPlay again? (y/n): ").strip().lower()
        if replay == "y":
            adventure.reset()
            self._run_adventure(adventure)

    def _print_outcome(self, result: GameResult, adventure: MiniAdventure) -> None:
        p1_name = self._p1.character_name if self._p1 else "Player 1"
        p2_name = self._p2.character_name if self._p2 else "Player 2"

        print("\n" + "═" * 40)
        print("  GAME OVER")
        print("═" * 40)
        if result == GameResult.PLAYER1_WIN:
            print(f"   {p1_name} wins!")
        elif result == GameResult.PLAYER2_WIN:
            print(f"   {p2_name} wins!")
        elif result == GameResult.TIE:
            print("   It's a tie!")
        elif result == GameResult.COOPERATIVE_WIN:
            print(f"   Both players win! Great teamwork, {p1_name} & {p2_name}!")
        elif result == GameResult.COOPERATIVE_LOSS:
            print(f"   Both players lose. Better luck next time!")
        print("═" * 40)

    #  Utilities 

    def _read_int(self, prompt: str, min_val: int, max_val: int) -> int:
        while True:
            raw = input(prompt).strip()
            try:
                val = int(raw)
                if min_val <= val <= max_val:
                    return val
            except ValueError:
                pass
            print(f"  Enter a number between {min_val} and {max_val}.")


#  Script entry point 

def main() -> None:
    controller = GameController()
    controller.run()


if __name__ == "__main__":
    main()