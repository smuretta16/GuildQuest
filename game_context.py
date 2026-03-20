"""
game_context.py
---------------
GameContext is the single object that mini-adventures receive when they are
initialized. It gives each adventure access to the shared GuildQuest systems
that were built in the individual assignments.

Mini-adventures should read from ctx but NOT replace top-level references
(e.g. don't do ctx.clock = something_else). Mutating the clock or realm data
is fine within the bounds of the adventure.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from guildquest import WorldClock, Realm, Item, Rarity


@dataclass
class GameContext:
    """
    Shared GuildQuest systems provided to every mini-adventure.

    Populated by GameController from the active GuildQuestGame instance so
    mini-adventures can reuse the realm model, world clock, and item system
    from the original individual assignments.

    Attributes:
        clock:       The live WorldClock (from Sonja/Thang's time subsystem).
                     Adventures can call ctx.clock.advance_minutes() for
                     timed mechanics.
        realms:      Dict of realm_id -> Realm (from Thang's realm model).
                     Adventures pick a realm to set the scene.
        item_pool:   A catalogue of reusable Item templates adventures can
                     copy to hand out as loot (from Thang/Sonja's item system).
        active_realm_id: The realm this adventure takes place in. Set by the
                     adventure's init() using one of the realms above.
    """

    clock: "WorldClock"
    realms: Dict[int, "Realm"]
    item_pool: Dict[str, "Item"] = field(default_factory=dict)
    active_realm_id: int = 10  # default: Avalon

    @property
    def active_realm(self) -> "Realm | None":
        """Convenience: return the Realm object for active_realm_id."""
        return self.realms.get(self.active_realm_id)

    def get_realm_by_name(self, name: str) -> "Realm | None":
        """Look up a realm by display name (case-insensitive)."""
        name_lower = name.lower()
        for realm in self.realms.values():
            if realm.name.lower() == name_lower:
                return realm
        return None