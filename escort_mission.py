"""
escort_mission.py
-----------------
Escort Across the Realm — a co-op real-time mini-adventure using Pygame.

Two players work together to escort an NPC carrier to the goal while
avoiding hazards. If the carrier's health reaches 0, both players lose.

Reuse notes (required by assignment):
  - Realm: The adventure is set in the Shadowfen realm (from ctx.realms).
            Realm name is shown in the window title and HUD.
  - QuestEvent / WorldClock: Each hazard hit advances the world clock by
            10 minutes (time cost of being hit), tying gameplay to Sonja/Thang's
            time subsystem.
  - Item: When players succeed, a LEGENDARY "Escort Medal" Item is added to
            both players' inventory snapshots via profile.update_snapshot().
  - PlayerProfile: Win/loss recorded via the MiniAdventure hooks.

Controls (real-time, both players simultaneously):
  Player 1 (Carrier P): A/D to move, W to jump
  Player 2 (Partner W): LEFT/RIGHT to move, UP to jump
  R — restart
  Esc — quit / close window

Based on starter code by teammate.
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
import tempfile
from typing import Optional, TYPE_CHECKING

from mini_adventure import MiniAdventure, GameResult
from guildquest import Item, Rarity, PlayerProfile

if TYPE_CHECKING:
    from game_context import GameContext

# Check pygame availability once at import time
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


# ── Game constants (from starter code) ────────────────────────────────────

SCREEN_W = 960
SCREEN_H = 540
FPS      = 60

COLOR_BG       = (22,  20,  24)
COLOR_PLATFORM = (72,  64,  58)
COLOR_WALL     = (60,  60,  70)
COLOR_GOAL     = (80,  180, 120)
COLOR_HAZARD   = (200, 70,  70)
COLOR_FIRE     = (255, 140, 60)
COLOR_WATER    = (80,  160, 255)
COLOR_TEXT     = (235, 235, 235)
COLOR_NPC      = (240, 220, 90)
COLOR_DIM      = (160, 160, 160)
COLOR_LEVER    = (120, 200, 140)

GRAVITY    = 0.6
MOVE_SPEED = 3.8
JUMP_SPEED = -11.5

MAX_HEALTH = 3


# ── Player physics object ─────────────────────────────────────────────────

class _Player:
    def __init__(self, x, y, color, label):
        self.rect     = pygame.Rect(x, y, 28, 36)
        self.color    = color
        self.label    = label
        self.vel_y    = 0.0
        self.on_ground = False

    def move(self, dx, solids):
        self.rect.x += dx
        for s in solids:
            if self.rect.colliderect(s):
                if dx > 0: self.rect.right = s.left
                elif dx < 0: self.rect.left  = s.right

    def apply_gravity(self, solids):
        self.vel_y    += GRAVITY
        self.rect.y   += int(self.vel_y)
        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vel_y > 0:
                    self.rect.bottom = s.top
                    self.vel_y       = 0
                    self.on_ground   = True
                elif self.vel_y < 0:
                    self.rect.top = s.bottom
                    self.vel_y    = 0


# ── Inner game logic (from starter code, lightly extended) ───────────────

class _EscortGame:
    def __init__(self, realm_name: str = "Shadowfen"):
        self.realm_name = realm_name
        self.clock_penalty = 0   # total minutes added to world clock from hits
        self.reset()

    def reset(self):
        self.carrier = _Player(60,  420, COLOR_FIRE,  "P1")
        self.partner = _Player(110, 420, COLOR_WATER, "P2")
        self.health  = MAX_HEALTH
        self.outcome = GameResult.IN_PROGRESS
        self.message = (
            f"Escort the NPC carrier (P) to the goal (G) in {self.realm_name}!"
        )
        self.clock_penalty = 0

        def layout_set() -> dict:
            base = [
                pygame.Rect(0,   500, 960, 40),   # floor
                pygame.Rect(0,   0,   20,  540),  # left wall
                pygame.Rect(940, 0,   20,  540),  # right wall
                pygame.Rect(0,   0,   960, 20),   # ceiling
            ]

            layouts = []

            layouts.append({
                "platforms": base + [
                    pygame.Rect(80,  430, 220, 18),
                    pygame.Rect(320, 390, 220, 18),
                    pygame.Rect(560, 350, 220, 18),
                    pygame.Rect(120, 320, 180, 18),
                    pygame.Rect(360, 300, 160, 18),
                    pygame.Rect(600, 280, 200, 18),
                    pygame.Rect(200, 240, 180, 18),
                    pygame.Rect(460, 220, 180, 18),
                    pygame.Rect(720, 200, 180, 18),
                    pygame.Rect(120, 170, 200, 18),
                    pygame.Rect(380, 160, 200, 18),
                    pygame.Rect(640, 140, 200, 18),
                ],
                "walls": [
                    pygame.Rect(520, 360, 16, 140),
                    pygame.Rect(680, 220, 16, 280),
                ],
                "hazards": [
                    pygame.Rect(360, 482, 70, 18),
                    pygame.Rect(520, 482, 70, 18),
                    pygame.Rect(640, 482, 70, 18),
                    pygame.Rect(420, 340, 60, 16),
                    pygame.Rect(760, 182, 60, 16),
                ],
                "goal": pygame.Rect(880, 110, 40, 40),
                "lever": pygame.Rect(140, 120, 40, 40),
            })

            layouts.append({
                "platforms": base + [
                    pygame.Rect(70,  420, 200, 18),
                    pygame.Rect(290, 380, 200, 18),
                    pygame.Rect(520, 340, 200, 18),
                    pygame.Rect(180, 300, 180, 18),
                    pygame.Rect(430, 270, 180, 18),
                    pygame.Rect(680, 250, 180, 18),
                    pygame.Rect(120, 210, 200, 18),
                    pygame.Rect(380, 190, 200, 18),
                    pygame.Rect(640, 170, 200, 18),
                ],
                "walls": [
                    pygame.Rect(460, 340, 16, 160),
                    pygame.Rect(740, 220, 16, 280),
                ],
                "hazards": [
                    pygame.Rect(300, 482, 70, 18),
                    pygame.Rect(470, 482, 70, 18),
                    pygame.Rect(630, 482, 70, 18),
                    pygame.Rect(500, 320, 60, 16),
                ],
                "goal": pygame.Rect(880, 150, 40, 40),
                "lever": pygame.Rect(120, 90, 40, 40),
            })

            layouts.append({
                "platforms": base + [
                    pygame.Rect(90,  430, 220, 18),
                    pygame.Rect(340, 400, 220, 18),
                    pygame.Rect(600, 360, 220, 18),
                    pygame.Rect(140, 320, 180, 18),
                    pygame.Rect(380, 300, 160, 18),
                    pygame.Rect(620, 280, 200, 18),
                    pygame.Rect(220, 240, 180, 18),
                    pygame.Rect(480, 220, 180, 18),
                    pygame.Rect(740, 200, 180, 18),
                ],
                "walls": [
                    pygame.Rect(560, 340, 16, 160),
                    pygame.Rect(700, 260, 16, 240),
                ],
                "hazards": [
                    pygame.Rect(360, 482, 70, 18),
                    pygame.Rect(520, 482, 70, 18),
                    pygame.Rect(640, 482, 70, 18),
                    pygame.Rect(420, 330, 60, 16),
                ],
                "goal": pygame.Rect(880, 120, 40, 40),
                "lever": pygame.Rect(160, 120, 40, 40),
            })

            return random.choice(layouts)

        layout = layout_set()
        self.platforms = layout["platforms"]
        self.walls = layout["walls"]
        self.hazards = layout["hazards"]
        self.goal = layout["goal"]
        self.lever_zone = layout["lever"]

        # Tall blocker that cannot be jumped over; only P2 can remove it.
        self.blocker = pygame.Rect(820, 20, 60, 480)
        self.blocker_removed = False
        self.walls.append(self.blocker)

    @property
    def solids(self):
        if self.blocker_removed:
            return self.platforms + [w for w in self.walls if w is not self.blocker]
        return self.platforms + self.walls

    def update(self, keys) -> str:
        """Process one frame. Returns a feedback string (empty if nothing notable)."""
        if self.outcome != GameResult.IN_PROGRESS:
            return ""

        dx_c = dx_p = 0
        if keys[pygame.K_a]:     dx_c -= MOVE_SPEED
        if keys[pygame.K_d]:     dx_c += MOVE_SPEED
        if keys[pygame.K_LEFT]:  dx_p -= MOVE_SPEED
        if keys[pygame.K_RIGHT]: dx_p += MOVE_SPEED

        self.carrier.move(dx_c, self.solids)
        self.partner.move(dx_p, self.solids)

        if keys[pygame.K_w]  and self.carrier.on_ground: self.carrier.vel_y = JUMP_SPEED
        if keys[pygame.K_UP] and self.partner.on_ground:  self.partner.vel_y = JUMP_SPEED

        self.carrier.apply_gravity(self.solids)
        self.partner.apply_gravity(self.solids)

        # Partner-only action: remove blocker when P2 reaches the lever area.
        if self.partner.rect.colliderect(self.lever_zone):
            self.blocker_removed = True

        # ── Goal check ──────────────────────────────────────────────
        if self.carrier.rect.colliderect(self.goal):
            self.outcome = GameResult.COOPERATIVE_WIN
            self.message = "🏆 Escort succeeded! Both players WIN!"
            return "win"

        # ── Hazard check ────────────────────────────────────────────
        for hz in self.hazards:
            if self.carrier.rect.colliderect(hz):
                self.health -= 1
                self.clock_penalty += 10   # 10 min world-clock cost per hit
                self.carrier.rect.topleft = (60, 420)
                self.carrier.vel_y = 0
                if self.health <= 0:
                    self.outcome = GameResult.COOPERATIVE_LOSS
                    self.message = "💀 Escort failed! Both players LOSE."
                    return "loss"
                else:
                    self.message = f"Carrier hit a hazard! Health: {self.health}/{MAX_HEALTH}"
                    return "hit"
        return ""

    def draw(self, screen, font, small, p1_name: str, p2_name: str):
        screen.fill(COLOR_BG)

        for plat in self.platforms: pygame.draw.rect(screen, COLOR_PLATFORM, plat)
        for wall in self.walls:
            if wall is self.blocker and self.blocker_removed:
                continue
            pygame.draw.rect(screen, COLOR_WALL, wall)
        for hz   in self.hazards:   pygame.draw.rect(screen, COLOR_HAZARD,   hz)
        pygame.draw.rect(screen, COLOR_LEVER, self.lever_zone)
        pygame.draw.rect(screen, COLOR_GOAL, self.goal)

        pygame.draw.rect(screen, self.carrier.color, self.carrier.rect)
        pygame.draw.rect(screen, self.partner.color, self.partner.rect)

        # NPC dot above carrier
        npc_x = self.carrier.rect.centerx
        npc_y = self.carrier.rect.top - 12
        pygame.draw.circle(screen, COLOR_NPC, (npc_x, npc_y), 8)

        # Labels
        for player, lbl in ((self.carrier, "P1"), (self.partner, "P2")):
            t = small.render(lbl, True, COLOR_TEXT)
            screen.blit(t, (player.rect.x + 4, player.rect.y + 8))
        screen.blit(small.render("G", True, COLOR_TEXT),
                    (self.goal.x+12, self.goal.y+8))

        # Health hearts
        hearts = "❤ " * self.health + "🖤 " * (MAX_HEALTH - self.health)

        # HUD lines
        hud = [
            f"Realm: {self.realm_name}   NPC Health: {self.health}/{MAX_HEALTH}",
            f"P1 ({p1_name}): A D W-jump    P2 ({p2_name}): ← → ↑-jump    R=Restart  Esc=Quit",
            "Legend:  P1=Carrier  P2=Partner  G=Goal  Green=Lever  Red=Hazard  ●=NPC",
        ]
        for i, line in enumerate(hud):
            screen.blit(small.render(line, True, COLOR_DIM), (20, 12 + i*20))

        # Main message at bottom
        msg_surf = font.render(self.message, True, COLOR_TEXT)
        screen.blit(msg_surf, (20, SCREEN_H - 34))


# ── MiniAdventure wrapper ─────────────────────────────────────────────────

class EscortMission(MiniAdventure):
    """
    Co-op real-time platformer: escort an NPC carrier to the goal.

    Implements MiniAdventure interface so the GameController and GUI
    can treat it exactly like any other adventure.

    Note: This adventure is REAL-TIME (runs its own pygame loop inside
    run_pygame_session()), which is called by the GUI launcher. The
    standard turn-based handle_input/advance_turn interface is implemented
    for CLI compatibility but the GUI uses the pygame window directly.
    """

    NAME        = "Escort Across the Realm"
    DESCRIPTION = (
        "Co-op!  Escort the NPC carrier to safety while dodging hazards. "
        "Player 1: A D W   Player 2: ← → ↑"
    )
    IS_COOPERATIVE = True

    def __init__(self):
        self._ctx:     Optional["GameContext"] = None
        self._p1:      Optional[PlayerProfile]  = None
        self._p2:      Optional[PlayerProfile]  = None
        self._outcome: GameResult = GameResult.IN_PROGRESS
        self._realm_name: str = "Shadowfen"

    # ── MiniAdventure interface ────────────────────────────────────

    def init(self, ctx: "GameContext", p1: PlayerProfile, p2: PlayerProfile) -> None:
        self._ctx = ctx
        self._p1  = p1
        self._p2  = p2
        self._outcome = GameResult.IN_PROGRESS

        # Reuse: pick Shadowfen realm from ctx if available
        realm = ctx.get_realm_by_name("Shadowfen")
        if realm:
            ctx.active_realm_id = realm.realm_id
            self._realm_name = realm.name
        else:
            self._realm_name = "The Realm"

    def get_instructions(self) -> str:
        return (
            f"\n=== ESCORT ACROSS THE REALM ===\n"
            f"Realm: {self._realm_name}\n"
            "Rules:\n"
            "  • Co-op! Both players must work together.\n"
            "  • Player 1 (orange P) is the Carrier — escort them to the Goal (G).\n"
            "  • Player 2 (blue W)   is the Partner — help navigate safely.\n"
            f"  • Carrier has {MAX_HEALTH} health. Each hazard hit costs 1 health.\n"
            "  • Reach the goal before health runs out — or both players LOSE.\n\n"
            "Controls:\n"
            "  Player 1: A (left)  D (right)  W (jump)\n"
            "  Player 2: ← (left)  → (right)  ↑ (jump)\n"
            "  R = restart   Esc = quit\n"
        )

    def get_state_view(self) -> str:
        return (
            f"Escort Mission — {self._realm_name}\n"
            f"Outcome: {self._outcome.value}\n"
            "(Game runs in a separate Pygame window.)\n"
        )

    def handle_input(self, player_index: int, raw_input: str) -> str:
        # Turn-based input not used in real-time mode;
        # provided for CLI/interface compatibility only.
        return "(Escort Mission runs in real-time via Pygame window.)"

    def advance_turn(self) -> None:
        pass  # real-time; no discrete turns

    def is_over(self) -> bool:
        return self._outcome != GameResult.IN_PROGRESS

    def get_outcome(self) -> GameResult:
        return self._outcome

    def reset(self) -> None:
        self._outcome = GameResult.IN_PROGRESS

    # ── Pygame session (called by GUI) ─────────────────────────────

    def run_pygame_session(self) -> GameResult:
        """
        Run the full real-time pygame game loop.
        Blocks until the player quits or wins/loses.
        Returns the final GameResult and updates profiles.
        """
        if not PYGAME_AVAILABLE:
            print("ERROR: pygame is not installed. Run:  pip install pygame")
            return GameResult.IN_PROGRESS

        pygame.init()
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        p1n = self._p1.character_name if self._p1 else "Player 1"
        p2n = self._p2.character_name if self._p2 else "Player 2"
        pygame.display.set_caption(
            f"GuildQuest — Escort Across the Realm  ({p1n} & {p2n})"
        )
        clock_pg = pygame.time.Clock()
        font  = pygame.font.SysFont("arial", 22)
        small = pygame.font.SysFont("arial", 16)

        game = _EscortGame(realm_name=self._realm_name)
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        game.reset()

            keys = pygame.key.get_pressed()
            feedback = game.update(keys)

            game.draw(screen, font, small, p1n, p2n)
            pygame.display.flip()
            clock_pg.tick(FPS)

            # Stop looping once there's a result (let players see win/loss screen briefly)
            if game.outcome != GameResult.IN_PROGRESS:
                self._outcome = game.outcome
                # Advance world clock by penalty minutes (reuse WorldClock subsystem)
                if self._ctx and game.clock_penalty > 0:
                    self._ctx.clock.advance_minutes(game.clock_penalty)
                # Show result for 2.5 seconds then close
                pygame.time.wait(2500)
                running = False

        pygame.quit()

        # ── Record results ──────────────────────────────────────────
        if self._outcome == GameResult.COOPERATIVE_WIN:
            if self._p1: self.on_complete(self._p1)
            if self._p2: self.on_complete(self._p2)
            # Reuse: grant a Legendary item to both players (Item subsystem)
            medal = Item(
                name="Escort Medal",
                description=f"Awarded for successfully escorting the NPC in {self._realm_name}.",
                rarity=Rarity.LEGENDARY,
            )
            if self._p1:
                snapshot = list(self._p1.inventory_snapshot) + [medal]
                self._p1.update_snapshot(snapshot)
            if self._p2:
                snapshot = list(self._p2.inventory_snapshot) + [medal]
                self._p2.update_snapshot(snapshot)
        elif self._outcome == GameResult.COOPERATIVE_LOSS:
            if self._p1: self.on_player_loss(self._p1)
            if self._p2: self.on_player_loss(self._p2)

        return self._outcome
