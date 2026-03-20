from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Visibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Permission(str, Enum):
    VIEW = "VIEW"
    COLLABORATIVE = "COLLABORATIVE"


class Theme(str, Enum):
    CLASSIC = "CLASSIC"
    MODERN = "MODERN"


class TimeDisplay(str, Enum):
    WORLDCLOCK = "WORLDCLOCK"
    REALMLOCAL = "REALMLOCAL"
    BOTH = "BOTH"


class Rarity(str, Enum):
    COMMON = "COMMON"
    RARE = "RARE"
    ULTRA_RARE = "ULTRA_RARE"
    LEGENDARY = "LEGENDARY"


@dataclass(frozen=True)
class WorldTime:
    day: int
    hour: int
    minute: int

    @classmethod
    def from_total_minutes(cls, total: int) -> "WorldTime":
        if total < 0:
            total = 0
        day, rem = divmod(total, 24 * 60)
        hour, minute = divmod(rem, 60)
        return cls(day=day, hour=hour, minute=minute)

    @property
    def total_minutes(self) -> int:
        return self.day * 24 * 60 + self.hour * 60 + self.minute

    def add_minutes(self, delta: int) -> "WorldTime":
        return WorldTime.from_total_minutes(self.total_minutes + delta)

    def __str__(self) -> str:
        return f"Day {self.day}, {self.hour:02d}:{self.minute:02d}"


@dataclass
class WorldClock:
    now: WorldTime = field(default_factory=lambda: WorldTime(0, 8, 0))

    def advance_minutes(self, delta: int) -> None:
        self.now = self.now.add_minutes(delta)


@dataclass
class Realm:
    realm_id: int
    name: str
    description: str
    minute_offset: int = 0


@dataclass
class Item:
    name: str
    description: str
    rarity: Rarity


@dataclass
class Character:
    character_id: int
    name: str
    character_class: str
    level: int = 1
    inventory: List[Item] = field(default_factory=list)


@dataclass
class QuestEvent:
    event_id: int
    name: str
    start_time: WorldTime
    end_time: WorldTime
    realm_id: int


@dataclass
class Settings:
    theme: Theme = Theme.CLASSIC
    time_display: TimeDisplay = TimeDisplay.BOTH
    current_realm_id: int = 10


@dataclass
class PlayerProfile:
    """GuildQuest game identity for a player, tracked across sessions."""
    character_name: str
    preferred_realm: str
    wins: int = 0
    losses: int = 0
    quests_completed: int = 0
    achievements: List[str] = field(default_factory=list)
    quest_history: List[str] = field(default_factory=list)
    inventory_snapshot: List[Item] = field(default_factory=list)

    def record_win(self) -> None:
        self.wins += 1

    def record_loss(self) -> None:
        self.losses += 1

    def record_quest(self, quest_name: str) -> None:
        """Record a completed quest by name and bump the counter."""
        self.quest_history.append(quest_name)
        self.quests_completed += 1

    def update_snapshot(self, items: List[Item]) -> None:
        """Replace the inventory snapshot with the player's current items."""
        self.inventory_snapshot = list(items)

    def add_achievement(self, achievement: str) -> None:
        if achievement not in self.achievements:
            self.achievements.append(achievement)

    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0

    def __str__(self) -> str:
        quest_lines = (
            "\n".join(f"    - {q}" for q in self.quest_history)
            if self.quest_history else "    none"
        )
        item_lines = (
            "\n".join(f"    - {i.name} [{i.rarity.value}]" for i in self.inventory_snapshot)
            if self.inventory_snapshot else "    none"
        )
        return (
            f"  Character : {self.character_name}\n"
            f"  Realm     : {self.preferred_realm}\n"
            f"  Wins      : {self.wins}  |  Losses: {self.losses}  "
            f"|  Win Rate: {self.win_rate():.0%}\n"
            f"  Quests    : {self.quests_completed}\n"
            f"  Quest History:\n{quest_lines}\n"
            f"  Inventory Snapshot:\n{item_lines}\n"
            f"  Achievements: {', '.join(self.achievements) if self.achievements else 'none'}"
        )


@dataclass
class User:
    user_id: int
    name: str
    settings: Settings = field(default_factory=Settings)
    profile: Optional[PlayerProfile] = None


@dataclass
class Campaign:
    campaign_id: int
    owner_user_id: int
    name: str
    visibility: Visibility = Visibility.PRIVATE
    archived: bool = False
    event_ids: List[int] = field(default_factory=list)
    shares: Dict[int, Permission] = field(default_factory=dict)


PROFILES_FILE = "profiles.json"


def save_profiles(users: Dict[int, "User"], path: str = PROFILES_FILE) -> None:
    """Persist all player profiles to a JSON text file.

    Only users who have a profile are written. The file is keyed by user_id
    so it survives re-ordering or user deletion.
    """
    data: Dict[str, dict] = {}
    for user in users.values():
        if user.profile is not None:
            p = user.profile
            data[str(user.user_id)] = {
                "username": user.name,
                "character_name": p.character_name,
                "preferred_realm": p.preferred_realm,
                "wins": p.wins,
                "losses": p.losses,
                "quests_completed": p.quests_completed,
                "achievements": p.achievements,
                "quest_history": p.quest_history,
                "inventory_snapshot": [
                    {"name": i.name, "description": i.description, "rarity": i.rarity.value}
                    for i in p.inventory_snapshot
                ],
            }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_profiles(users: Dict[int, "User"], path: str = PROFILES_FILE) -> None:
    """Load player profiles from a JSON text file into the matching User objects.

    Users whose id is not in the file are left with profile=None.
    Missing or corrupt files are silently ignored so the app still starts.
    """
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, dict] = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    for uid_str, entry in data.items():
        try:
            uid = int(uid_str)
        except ValueError:
            continue
        if uid not in users:
            continue
        raw_items = entry.get("inventory_snapshot", [])
        snapshot = [
            Item(
                name=it.get("name", ""),
                description=it.get("description", ""),
                rarity=Rarity(it.get("rarity", Rarity.COMMON.value)),
            )
            for it in raw_items
            if isinstance(it, dict)
        ]
        users[uid].profile = PlayerProfile(
            character_name=entry.get("character_name", "Unknown"),
            preferred_realm=entry.get("preferred_realm", "Avalon"),
            wins=int(entry.get("wins", 0)),
            losses=int(entry.get("losses", 0)),
            quests_completed=int(entry.get("quests_completed", 0)),
            achievements=list(entry.get("achievements", [])),
            quest_history=list(entry.get("quest_history", [])),
            inventory_snapshot=snapshot,
        )


class GuildQuestGame:
    def __init__(self) -> None:
        self.clock = WorldClock()
        self.users: Dict[int, User] = {}
        self.realms: Dict[int, Realm] = {}
        self.campaigns: Dict[int, Campaign] = {}
        self.events: Dict[int, QuestEvent] = {}
        self.characters: Dict[int, Character] = {}

        self.active_user_id: int = 1
        self.next_user_id = 3
        self.next_realm_id = 12
        self.next_campaign_id = 102
        self.next_event_id = 1002
        self.next_character_id = 1

        self.seed_data()
        load_profiles(self.users)

    def seed_data(self) -> None:
        # ── Users ──────────────────────────────────────────────────────────
        self.users[1] = User(1, "User[1]")
        self.users[2] = User(2, "User[2]")

        # ── Realms ─────────────────────────────────────────────────────────
        self.realms[10]  = Realm(10,  "Avalon",           "The verdant main continent, seat of the Adventurers Guild.",       0)
        self.realms[11]  = Realm(11,  "Lunar Outpost",    "A fortified moon station; cold, silent, and full of secrets.",   120)
        self.realms[12]  = Realm(12,  "Shadowfen",        "A murky swamp realm where light barely penetrates the canopy.",   -60)
        self.realms[13]  = Realm(13,  "Ironspire",        "A towering mountain citadel forged by ancient dwarven clans.",    180)
        self.realms[14]  = Realm(14,  "Emberveil",        "A volcanic archipelago of fire and floating obsidian islands.",    240)
        self.realms[15]  = Realm(15,  "Crystaldeep",      "An underwater cavern realm lit by bioluminescent coral.",         -120)
        self.realms[16]  = Realm(16,  "Thornwood",        "A vast enchanted forest patrolled by ancient guardian spirits.",   30)
        self.realms[17]  = Realm(17,  "The Ashen Wastes", "A post-apocalyptic desert blasted by forgotten sorcery.",         -90)
        self.realms[18]  = Realm(18,  "Skyreach",         "Cloud cities suspended by enormous arcane levitation stones.",    300)
        self.realms[19]  = Realm(19,  "Tidehollow",       "A coastal labyrinth of sea caves and smuggler dens.",              45)
        self.next_realm_id = 20

        # ── Campaigns ──────────────────────────────────────────────────────
        starter  = Campaign(100, 1, "Starter Campaign",       Visibility.PRIVATE)
        public   = Campaign(101, 2, "Public One-Shot",         Visibility.PUBLIC)
        arc2     = Campaign(102, 1, "The Lunar Conspiracy",    Visibility.PRIVATE)
        arc3     = Campaign(102, 2, "Emberveil Expedition",    Visibility.PUBLIC)
        self.campaigns[100] = starter
        self.campaigns[101] = public
        self.campaigns[102] = arc2
        self.campaigns[103] = arc3
        self.next_campaign_id = 104

        # ── Quest Events ───────────────────────────────────────────────────
        events = [
            QuestEvent(1000, "Meet the Guildmaster",         WorldTime(0,  9,  0), WorldTime(0, 10,  0), 10),
            QuestEvent(1001, "Dock at Lunar Outpost",         WorldTime(0, 18, 30), WorldTime(0, 20,  0), 11),
            QuestEvent(1002, "Shadowfen Recon",               WorldTime(1,  6,  0), WorldTime(1,  9,  0), 12),
            QuestEvent(1003, "Dwarven Forge Heist",           WorldTime(1, 14,  0), WorldTime(1, 18,  0), 13),
            QuestEvent(1004, "Emberveil Rescue Mission",      WorldTime(2,  8,  0), WorldTime(2, 12,  0), 14),
            QuestEvent(1005, "Crystaldeep Dive",              WorldTime(2, 15,  0), WorldTime(2, 19,  0), 15),
            QuestEvent(1006, "Thornwood Patrol",              WorldTime(3,  7, 30), WorldTime(3, 11, 30), 16),
            QuestEvent(1007, "Ashen Wastes Survial Run",      WorldTime(3, 13,  0), WorldTime(3, 17,  0), 17),
            QuestEvent(1008, "Skyreach Summit Breach",        WorldTime(4, 10,  0), WorldTime(4, 14,  0), 18),
            QuestEvent(1009, "Tidehollow Smuggler Sting",     WorldTime(4, 20,  0), WorldTime(4, 23,  0), 19),
        ]
        for e in events:
            self.events[e.event_id] = e
        starter.event_ids.extend([1000, 1001, 1002])
        public.event_ids.extend([1003, 1004])
        arc2.event_ids.extend([1005, 1006, 1007])
        arc3.event_ids.extend([1008, 1009])
        self.next_event_id = 1010

        # ── Characters ─────────────────────────────────────────────────────
        char1 = Character(1, "Aldric",   "Warrior",  level=5)
        char2 = Character(2, "Seraphel", "Mage",     level=4)
        char3 = Character(3, "Vex",      "Rogue",    level=6)
        char4 = Character(4, "Brynn",    "Cleric",   level=3)

        char1.inventory = [
            Item("Ironclad Shield",   "A dwarven-forged tower shield.",      Rarity.RARE),
            Item("Battleaxe",         "Heavy double-bladed axe.",            Rarity.COMMON),
        ]
        char2.inventory = [
            Item("Arcane Tome",       "Enhances spell power by 20%.",        Rarity.ULTRA_RARE),
            Item("Mana Crystal",      "Restores 50 mana on use.",            Rarity.RARE),
        ]
        char3.inventory = [
            Item("Shadow Cloak",      "Grants brief invisibility.",          Rarity.LEGENDARY),
            Item("Poisoned Dagger",   "Applies venom on hit.",               Rarity.RARE),
        ]
        char4.inventory = [
            Item("Holy Relic",        "Repels undead creatures.",            Rarity.ULTRA_RARE),
            Item("Healing Potion",    "Restores 100 HP.",                    Rarity.COMMON),
        ]
        for ch in (char1, char2, char3, char4):
            self.characters[ch.character_id] = ch
        self.next_character_id = 5

    def read_int(self, prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        while True:
            raw = input(prompt).strip()
            try:
                value = int(raw)
            except ValueError:
                print("Please enter a valid number.")
                continue
            if min_val is not None and value < min_val:
                print(f"Please enter >= {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Please enter <= {max_val}.")
                continue
            return value

    def read_choice(self, prompt: str, options: List[str]) -> str:
        option_map = {str(i + 1): option for i, option in enumerate(options)}
        while True:
            print(prompt)
            for i, option in enumerate(options, start=1):
                print(f"{i}. {option}")
            pick = input("> ").strip()
            if pick in option_map:
                return option_map[pick]
            print("Invalid choice.")

    @property
    def active_user(self) -> User:
        return self.users[self.active_user_id]

    def campaign_access(self, campaign: Campaign) -> tuple[bool, bool, bool]:
        user_id = self.active_user_id
        if campaign.owner_user_id == user_id:
            return True, True, True

        permission = campaign.shares.get(user_id)
        if permission == Permission.COLLABORATIVE:
            return True, True, False
        if permission == Permission.VIEW:
            return True, False, False
        if campaign.visibility == Visibility.PUBLIC:
            return True, False, False
        return False, False, False

    def format_time_for_user(self, time: WorldTime, realm_id: int) -> str:
        pref = self.active_user.settings.time_display
        world_text = str(time)
        realm = self.realms.get(realm_id)
        if realm is None:
            return world_text

        realm_text = str(time.add_minutes(realm.minute_offset)) + f" ({realm.name})"
        if pref == TimeDisplay.WORLDCLOCK:
            return world_text
        if pref == TimeDisplay.REALMLOCAL:
            return realm_text
        return f"{world_text} | local {realm_text}"

    def list_visible_campaigns(self) -> List[Campaign]:
        out = []
        for c in self.campaigns.values():
            can_view, _, _ = self.campaign_access(c)
            if can_view and not c.archived:
                out.append(c)
        return sorted(out, key=lambda c: c.campaign_id)

    def select_campaign(self, require_edit: bool = False) -> Optional[Campaign]:
        campaigns = self.list_visible_campaigns()
        if not campaigns:
            print("No campaigns available.")
            return None

        print("Select campaign:")
        for idx, c in enumerate(campaigns, start=1):
            can_view, can_edit, is_owner = self.campaign_access(c)
            role = "owner" if is_owner else ("editor" if can_edit else "viewer")
            print(f"{idx}. [{c.campaign_id}] {c.name} ({c.visibility}, {role})")

        pick = self.read_int("Choose campaign: ", 1, len(campaigns))
        campaign = campaigns[pick - 1]
        _, can_edit, _ = self.campaign_access(campaign)
        if require_edit and not can_edit:
            print("You do not have edit access to this campaign.")
            return None
        return campaign

    def create_campaign(self) -> None:
        name = input("Campaign name: ").strip()
        if not name:
            print("Name is required.")
            return
        vis = self.read_choice("Visibility", ["PUBLIC", "PRIVATE"])

        campaign = Campaign(
            campaign_id=self.next_campaign_id,
            owner_user_id=self.active_user_id,
            name=name,
            visibility=Visibility[vis],
        )
        self.campaigns[campaign.campaign_id] = campaign
        self.next_campaign_id += 1
        print(f"Campaign created with id {campaign.campaign_id}.")

    def add_realm(self) -> None:
        name = input("Realm name: ").strip()
        desc = input("Realm description: ").strip()
        offset = self.read_int("Realm time offset (minutes): ")
        realm = Realm(self.next_realm_id, name, desc, offset)
        self.realms[realm.realm_id] = realm
        self.next_realm_id += 1
        print(f"Realm created: [{realm.realm_id}] {realm.name}")

    def choose_realm(self) -> Optional[Realm]:
        if not self.realms:
            print("No realms available.")
            return None
        realms = sorted(self.realms.values(), key=lambda r: r.realm_id)
        print("Select realm:")
        for idx, realm in enumerate(realms, start=1):
            print(f"{idx}. [{realm.realm_id}] {realm.name} (offset {realm.minute_offset:+}m)")
        pick = self.read_int("Choose realm: ", 1, len(realms))
        return realms[pick - 1]

    def add_quest_event(self) -> None:
        campaign = self.select_campaign(require_edit=True)
        if campaign is None:
            return
        realm = self.choose_realm()
        if realm is None:
            return

        name = input("Quest name: ").strip()
        if not name:
            print("Quest name is required.")
            return

        day = self.read_int("Start day: ", 0)
        hour = self.read_int("Start hour (0-23): ", 0, 23)
        minute = self.read_int("Start minute (0-59): ", 0, 59)
        duration = self.read_int("Duration (minutes): ", 1)

        start = WorldTime(day, hour, minute)
        end = start.add_minutes(duration)
        event = QuestEvent(self.next_event_id, name, start, end, realm.realm_id)
        self.events[event.event_id] = event
        campaign.event_ids.append(event.event_id)
        self.next_event_id += 1
        print(f"Quest event added: [{event.event_id}] {event.name}")

    def view_campaign_events(self) -> None:
        campaign = self.select_campaign(require_edit=False)
        if campaign is None:
            return
        self.print_events(campaign)

    def print_events(self, campaign: Campaign, within_minutes: Optional[int] = None) -> None:
        if not campaign.event_ids:
            print("No events in this campaign.")
            return

        now_total = self.clock.now.total_minutes
        events = []
        for eid in campaign.event_ids:
            event = self.events.get(eid)
            if event is None:
                continue
            if within_minutes is not None:
                if event.start_time.total_minutes < now_total:
                    continue
                if event.start_time.total_minutes > now_total + within_minutes:
                    continue
            events.append(event)

        if not events:
            print("No events in the selected time range.")
            return

        events.sort(key=lambda e: e.start_time.total_minutes)
        print(f"Events for [{campaign.campaign_id}] {campaign.name}:")
        for e in events:
            start_txt = self.format_time_for_user(e.start_time, e.realm_id)
            end_txt = self.format_time_for_user(e.end_time, e.realm_id)
            realm_name = self.realms[e.realm_id].name if e.realm_id in self.realms else "Unknown"
            print(f"- [{e.event_id}] {e.name}")
            print(f"  Realm: {realm_name}")
            print(f"  Start: {start_txt}")
            print(f"  End:   {end_txt}")

    def delete_campaign(self) -> None:
        campaign = self.select_campaign(require_edit=True)
        if campaign is None:
            return
        _, _, is_owner = self.campaign_access(campaign)
        if not is_owner:
            print("Only owner can delete a campaign.")
            return

        confirm = input(f"Delete campaign '{campaign.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Delete canceled.")
            return

        for eid in campaign.event_ids:
            self.events.pop(eid, None)
        self.campaigns.pop(campaign.campaign_id, None)
        print("Campaign deleted.")

    def add_character(self) -> None:
        name = input("Character name: ").strip()
        char_class = input("Character class: ").strip()
        if not name or not char_class:
            print("Name and class are required.")
            return

        c = Character(self.next_character_id, name, char_class)
        self.characters[c.character_id] = c
        self.next_character_id += 1
        print(f"Character created: [{c.character_id}] {c.name} ({c.character_class})")

    def select_character(self) -> Optional[Character]:
        chars = sorted(self.characters.values(), key=lambda c: c.character_id)
        if not chars:
            print("No characters available.")
            return None

        print("Select character:")
        for idx, c in enumerate(chars, start=1):
            print(f"{idx}. [{c.character_id}] {c.name} ({c.character_class})")

        pick = self.read_int("Choose character: ", 1, len(chars))
        return chars[pick - 1]

    def add_item_to_character(self) -> None:
        character = self.select_character()
        if character is None:
            return

        name = input("Item name: ").strip()
        desc = input("Item description: ").strip()
        rarity = self.read_choice("Rarity", ["COMMON", "RARE", "ULTRA_RARE", "LEGENDARY"])
        item = Item(name=name, description=desc, rarity=Rarity[rarity])
        character.inventory.append(item)
        print(f"Item added to {character.name}.")

    def view_characters(self) -> None:
        if not self.characters:
            print("No characters available.")
            return

        for c in sorted(self.characters.values(), key=lambda c: c.character_id):
            print(f"Character [{c.character_id}] {c.name}")
            print(f"  Class: {c.character_class}")
            print(f"  Level: {c.level}")
            print("  Items:")
            if not c.inventory:
                print("    (empty)")
            else:
                for item in c.inventory:
                    print(f"    - {item.name} [{item.rarity}] :: {item.description}")

    def share_campaign(self) -> None:
        campaign = self.select_campaign(require_edit=False)
        if campaign is None:
            return
        _, _, is_owner = self.campaign_access(campaign)
        if not is_owner:
            print("Only owner can share a campaign.")
            return

        others = [u for u in self.users.values() if u.user_id != self.active_user_id]
        if not others:
            print("No other users available.")
            return

        print("Share with user:")
        for idx, u in enumerate(others, start=1):
            print(f"{idx}. [{u.user_id}] {u.name}")
        pick = self.read_int("Choose user: ", 1, len(others))
        target = others[pick - 1]

        perm = self.read_choice("Permission", ["VIEW", "COLLABORATIVE"])
        campaign.shares[target.user_id] = Permission[perm]
        print(f"Campaign shared with {target.name} as {perm}.")

    def profile_menu(self) -> None:
        user = self.active_user
        while True:
            print(f"\nProfile — {user.name}")
            if user.profile:
                print(user.profile)
            else:
                print("  (no profile set up yet)")
            print("1. Create / edit profile")
            print("2. View profile")
            print("0. Back")
            pick = self.read_int("> ", 0, 2)
            if pick == 0:
                return
            if pick == 1:
                char_name = input("Character name: ").strip()
                if not char_name:
                    print("Character name is required.")
                    continue
                realm = self.choose_realm()
                preferred = realm.name if realm else "Avalon"
                if user.profile is None:
                    user.profile = PlayerProfile(
                        character_name=char_name,
                        preferred_realm=preferred,
                    )
                else:
                    user.profile.character_name = char_name
                    user.profile.preferred_realm = preferred
                save_profiles(self.users)
                print("Profile saved.")
            elif pick == 2:
                if user.profile:
                    print(user.profile)
                else:
                    print("No profile found. Create one first.")

    def settings_menu(self) -> None:
        settings = self.active_user.settings
        while True:
            print("\nSettings")
            print(f"1. Theme: {settings.theme}")
            print(f"2. Time display: {settings.time_display}")
            current = self.realms.get(settings.current_realm_id)
            realm_name = current.name if current else "Unknown"
            print(f"3. Current realm: {realm_name}")
            print("0. Back")
            pick = self.read_int("> ", 0, 3)
            if pick == 0:
                return
            if pick == 1:
                theme = self.read_choice("Theme", ["CLASSIC", "MODERN"])
                settings.theme = Theme[theme]
            elif pick == 2:
                td = self.read_choice("Time display", ["WORLDCLOCK", "REALMLOCAL", "BOTH"])
                settings.time_display = TimeDisplay[td]
            elif pick == 3:
                realm = self.choose_realm()
                if realm is not None:
                    settings.current_realm_id = realm.realm_id

    def view_menu(self) -> None:
        campaign = self.select_campaign(require_edit=False)
        if campaign is None:
            return

        span = self.read_choice("View range", ["DAY", "WEEK", "MONTH", "YEAR", "ALL"])
        mapping = {
            "DAY": 24 * 60,
            "WEEK": 7 * 24 * 60,
            "MONTH": 30 * 24 * 60,
            "YEAR": 365 * 24 * 60,
            "ALL": None,
        }
        self.print_events(campaign, mapping[span])

    def advance_world_time(self) -> None:
        print(f"Current world time: {self.clock.now}")
        mins = self.read_int("Advance minutes: ", 1)
        self.clock.advance_minutes(mins)
        print(f"New world time: {self.clock.now}")

    def user_menu(self) -> None:
        while True:
            print("\nUsers")
            for user in sorted(self.users.values(), key=lambda u: u.user_id):
                marker = "*" if user.user_id == self.active_user_id else " "
                print(f"{marker} [{user.user_id}] {user.name}")
            print("1. Switch active user")
            print("2. Create user")
            print("0. Back")
            pick = self.read_int("> ", 0, 2)
            if pick == 0:
                return
            if pick == 1:
                uid = self.read_int("Enter user id: ")
                if uid in self.users:
                    self.active_user_id = uid
                    print(f"Active user switched to {self.users[uid].name}")
                else:
                    print("User not found.")
            else:
                name = input("New user name: ").strip()
                if not name:
                    print("Name is required.")
                    continue
                user = User(self.next_user_id, name)
                self.users[user.user_id] = user
                self.next_user_id += 1
                print(f"User created: [{user.user_id}] {user.name}")

    def main_loop(self) -> None:
        while True:
            print("\n=== GuildQuest (Merged Python Edition) ===")
            print(f"Active user: {self.active_user.name} | World time: {self.clock.now}")
            print("1. Users")
            print("2. Create campaign")
            print("3. Add quest event")
            print("4. View campaign events")
            print("5. Add realm")
            print("6. Add character")
            print("7. Add item to character")
            print("8. View characters")
            print("9. Delete campaign")
            print("10. Views (day/week/month/year)")
            print("11. Share campaign")
            print("12. Settings")
            print("13. Advance world time")
            print("14. Player profile")
            print("0. Exit")

            choice = self.read_int("> ", 0, 14)
            if choice == 0:
                save_profiles(self.users)
                print("Goodbye.")
                return
            if choice == 1:
                self.user_menu()
            elif choice == 2:
                self.create_campaign()
            elif choice == 3:
                self.add_quest_event()
            elif choice == 4:
                self.view_campaign_events()
            elif choice == 5:
                self.add_realm()
            elif choice == 6:
                self.add_character()
            elif choice == 7:
                self.add_item_to_character()
            elif choice == 8:
                self.view_characters()
            elif choice == 9:
                self.delete_campaign()
            elif choice == 10:
                self.view_menu()
            elif choice == 11:
                self.share_campaign()
            elif choice == 12:
                self.settings_menu()
            elif choice == 13:
                self.advance_world_time()
            elif choice == 14:
                self.profile_menu()


def main() -> None:
    game = GuildQuestGame()
    game.main_loop()


if __name__ == "__main__":
    main()