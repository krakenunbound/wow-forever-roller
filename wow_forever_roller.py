#!/usr/bin/env python3
"""WoW Forever character forge — stream-ready sequential roller.

Roll order: Faction -> Race (by faction) -> Gender -> Class (by faction/race).
Combos match Forever launch as of 2026-09-17 (Icy Veins / Warcraft Tavern).
"""

from __future__ import annotations

import math
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np
import pygame

ROOT = Path(__file__).resolve().parent
ASSET = ROOT / "assets"
SHOTS = ROOT / "shots"

# ---------------------------------------------------------------------------
# Forever launch matrix (2026-09-17)
# ---------------------------------------------------------------------------
RACES = {
    "Alliance": ["Human", "Dwarf", "Night Elf", "Gnome", "Skyborne"],
    "Horde": ["Orc", "Undead", "Tauren", "Troll", "Skyborne"],
}
CLASSES = {
    ("Alliance", "Human"): ["Warrior", "Hunter", "Mage", "Rogue", "Priest", "Warlock", "Paladin"],
    ("Alliance", "Dwarf"): ["Warrior", "Hunter", "Rogue", "Priest", "Paladin", "Shaman"],
    ("Alliance", "Night Elf"): ["Warrior", "Hunter", "Rogue", "Priest", "Druid"],
    ("Alliance", "Gnome"): ["Warrior", "Mage", "Rogue", "Priest", "Warlock"],
    ("Alliance", "Skyborne"): ["Warrior", "Hunter", "Mage", "Rogue", "Druid"],
    ("Horde", "Orc"): ["Warrior", "Hunter", "Mage", "Rogue", "Warlock", "Shaman"],
    ("Horde", "Undead"): ["Warrior", "Mage", "Rogue", "Priest", "Warlock", "Paladin"],
    ("Horde", "Tauren"): ["Warrior", "Hunter", "Druid", "Shaman"],
    ("Horde", "Troll"): ["Warrior", "Hunter", "Mage", "Rogue", "Priest", "Warlock", "Shaman"],
    ("Horde", "Skyborne"): ["Warrior", "Hunter", "Rogue", "Druid", "Shaman"],
}
GENDERS = ["Male", "Female"]
NEW_COMBOS = {
    ("Alliance", "Human", "Hunter"),
    ("Alliance", "Gnome", "Priest"),
    ("Alliance", "Dwarf", "Shaman"),
    ("Horde", "Orc", "Mage"),
    ("Horde", "Troll", "Warlock"),
    ("Horde", "Undead", "Paladin"),
}
CLASS_COLOR = {
    "Warrior": (199, 156, 110),
    "Paladin": (245, 140, 186),
    "Hunter": (171, 212, 115),
    "Rogue": (255, 245, 105),
    "Priest": (255, 255, 255),
    "Shaman": (0, 112, 222),
    "Mage": (105, 204, 240),
    "Warlock": (148, 130, 201),
    "Druid": (255, 125, 10),
}
RACE_FILE = {
    "Human": "human.jpg",
    "Dwarf": "dwarf.jpg",
    "Night Elf": "nightelf.jpg",
    "Gnome": "gnome.jpg",
    "Skyborne": "skyborne.jpg",
    "Orc": "orc.jpg",
    "Undead": "undead.jpg",
    "Tauren": "tauren.jpg",
    "Troll": "troll.jpg",
}

# Barber options — race-flavored, including Forever Skyborne notes.
LOOKS = {
    "Human": {
        "hair": ["Squire Crop", "Long Waves", "Merchant Bob", "Battle Braid", "Widow's Peak"],
        "color": [("Ash Blond", (210, 190, 140)), ("Chestnut", (92, 52, 28)), ("Raven", (24, 20, 22)), ("Auburn", (140, 52, 28)), ("Silver", (186, 190, 198))],
        "eyes": [("Blue", (80, 140, 210)), ("Hazel", (140, 120, 60)), ("Green", (70, 140, 80)), ("Brown", (86, 52, 32))],
        "mark": ["None", "Scarred brow", "Court stubble", "Lion paint"],
    },
    "Dwarf": {
        "hair": ["Forge Braids", "Wild Mane", "Shaved Sides", "Crown Plait", "Anvil Knot"],
        "color": [("Auburn", (150, 60, 28)), ("Coal", (28, 24, 22)), ("Copper", (176, 90, 36)), ("Snow", (210, 210, 214))],
        "eyes": [("Amber", (200, 140, 50)), ("Slate", (90, 110, 130)), ("Green", (70, 130, 80))],
        "mark": ["None", "Soot streaks", "Rune tattoos", "Battle nicks"],
    },
    "Night Elf": {
        "hair": ["Moonfall", "Temple Veil", "Hunter Tail", "Leaf Crown", "Wildvine"],
        "color": [("Teal", (40, 90, 90)), ("Violet", (70, 40, 110)), ("Silver", (190, 195, 210)), ("Night", (20, 24, 40))],
        "eyes": [("Silver glow", (200, 220, 255)), ("Gold glow", (230, 200, 90)), ("Moonwhite", (230, 235, 255))],
        "mark": ["None", "Facial tattoos", "Whisper marks", "Leaf paint"],
    },
    "Gnome": {
        "hair": ["Spark Plug", "Tinker Tuft", "Goggle-crushed", "Lab Bob", "Static Shock"],
        "color": [("Pink", (220, 120, 150)), ("Green", (80, 160, 90)), ("Blond", (220, 200, 110)), ("White", (230, 230, 235))],
        "eyes": [("Green", (80, 170, 90)), ("Blue", (80, 140, 210)), ("Violet", (150, 90, 200))],
        "mark": ["None", "Oil smudge", "Gear tattoo", "Burn specks"],
    },
    "Skyborne": {
        "hair": ["Feather Crest", "Storm Sweep", "Cloud Veil", "Gale Braids", "Zephyr Fall"],
        "color": [("Silver-white", (210, 220, 230)), ("Storm gray", (90, 105, 125)), ("Sky azure", (90, 160, 210))],
        "eyes": [("Ice blue", (150, 210, 255)), ("Tempest gold", (240, 200, 70)), ("Void purple", (140, 90, 210))],
        "mark": ["Wind runes", "Cloud markings", "Ley scars", "None"],
    },
    "Orc": {
        "hair": ["Topknot", "War Braids", "Shaved Mohawk", "Wolf Mane", "Blackrock Crop"],
        "color": [("Black", (18, 16, 16)), ("Brown", (70, 42, 28)), ("Gray", (110, 110, 115)), ("Red-tint", (120, 40, 30))],
        "eyes": [("Amber", (210, 140, 40)), ("Red", (190, 40, 30)), ("Brown", (90, 50, 30))],
        "mark": ["None", "Tusk rings", "Clan scars", "Blackrock paint"],
    },
    "Undead": {
        "hair": ["Grave Locks", "Rot Bob", "Torn Banner", "Balding Crown", "Lordaeron Fall"],
        "color": [("Bone", (200, 195, 175)), ("Slime", (90, 130, 70)), ("Raven", (30, 28, 32)), ("Putrid", (120, 140, 70))],
        "eyes": [("Yellow glow", (230, 210, 70)), ("Soul blue", (80, 180, 220)), ("Dim orange", (210, 110, 40))],
        "mark": ["None", "Jaw stitch", "Plague veins", "Lordaeron crest"],
    },
    "Tauren": {
        "hair": ["Totem Braids", "Mesa Mane", "Feather Knot", "Thunder Crop", "Elder Fall"],
        "color": [("Earth brown", (90, 55, 30)), ("Dun", (150, 110, 70)), ("Black", (28, 22, 18)), ("Painted white", (210, 205, 190))],
        "eyes": [("Dark", (40, 30, 20)), ("Amber", (190, 130, 40)), ("Green", (70, 120, 60))],
        "mark": ["None", "Spirit paint", "Horn wraps", "Sunwalk glyphs"],
    },
    "Troll": {
        "hair": ["Red Mohawk", "Hex Braids", "Skull Knot", "Jungle Fall", "Darkspear Crest"],
        "color": [("Crimson", (170, 30, 30)), ("Indigo", (50, 40, 90)), ("Bone-white", (220, 215, 200)), ("Jungle green", (40, 90, 50))],
        "eyes": [("Gold", (230, 190, 50)), ("Red", (200, 40, 30)), ("Violet", (150, 70, 190))],
        "mark": ["None", "Face paint", "Tusk notches", "Hex scars"],
    },
}


def roll_look(race, avoid=None):
    spec = LOOKS[race]
    key = None
    look = None
    for _ in range(10):
        look = {
            "hair": random.choice(spec["hair"]),
            "color": random.choice(spec["color"]),
            "eyes": random.choice(spec["eyes"]),
            "mark": random.choice(spec["mark"]),
            "seed": random.randrange(1, 10**9),
        }
        key = (look["hair"], look["color"][0], look["eyes"][0], look["mark"])
        if not avoid or key != (avoid["hair"], avoid["color"][0], avoid["eyes"][0], avoid["mark"]):
            return look
    return look


def look_line(look) -> str:
    if not look:
        return "Empty"
    extra = "" if look["mark"] == "None" else f"  ·  {look['mark']}"
    return f"{look['hair']}  ·  {look['color'][0]}  ·  {look['eyes'][0]} eyes{extra}"

LANDSCAPE = (1600, 900)
PORTRAIT = (900, 1600)
GOLD = (212, 175, 55)
GOLD_LT = (246, 221, 140)
GOLD_DK = (110, 82, 24)
INK = (12, 10, 8)
PARCHMENT = (28, 22, 16)
ALLIANCE_C = (70, 130, 210)
HORDE_C = (196, 42, 42)
WHITE = (236, 228, 210)
MUTED = (160, 148, 122)

STAGES = ("faction", "race", "gender", "class")
SPIN_MS = {"faction": 1700, "race": 2300, "gender": 1400, "class": 2600}


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


# ---------------------------------------------------------------------------
# Sound
# ---------------------------------------------------------------------------
class SFX:
    def __init__(self):
        self.muted = False
        self.sr = 44100
        self.tick = self._click(880, 45, 0.28)
        self.tick_lo = self._click(520, 55, 0.32)
        self.lock = self._clang()
        self.fanfare = self._fanfare()
        self.sparkle = self._sparkle()

    def _arr(self, wave):
        wave = np.clip(wave, -1, 1)
        mono = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((mono, mono))
        return pygame.sndarray.make_sound(stereo)

    def _click(self, freq, ms, vol):
        n = int(self.sr * ms / 1000)
        t = np.arange(n) / self.sr
        noise = (np.random.rand(n) * 2 - 1) * 0.25
        w = (np.sin(2 * np.pi * freq * t) + noise) * np.exp(-t * 38) * vol
        return self._arr(w)

    def _clang(self):
        n = int(self.sr * 0.38)
        t = np.arange(n) / self.sr
        w = (
            0.45 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 8)
            + 0.28 * np.sin(2 * np.pi * 420 * t) * np.exp(-t * 14)
            + 0.16 * np.sin(2 * np.pi * 880 * t) * np.exp(-t * 22)
            + 0.10 * (np.random.rand(n) * 2 - 1) * np.exp(-t * 30)
        )
        return self._arr(w)

    def _fanfare(self):
        n = int(self.sr * 0.9)
        t = np.arange(n) / self.sr
        notes = [(0.00, 392), (0.12, 523), (0.24, 659), (0.40, 784)]
        w = np.zeros(n)
        for start, f in notes:
            i = int(start * self.sr)
            tt = np.arange(n - i) / self.sr
            env = np.exp(-tt * 3.2)
            w[i:] += 0.22 * np.sin(2 * np.pi * f * tt) * env
            w[i:] += 0.08 * np.sin(2 * np.pi * f * 2 * tt) * env
        return self._arr(w)

    def _sparkle(self):
        n = int(self.sr * 0.7)
        t = np.arange(n) / self.sr
        w = np.zeros(n)
        for i, f in enumerate((1174, 1396, 1568, 2093)):
            tt = np.arange(n) / self.sr
            w += 0.12 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * (4 + i))
        return self._arr(w)

    def play(self, snd, vol=0.7):
        if self.muted:
            return
        snd.set_volume(vol)
        snd.play()


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
def load_jpg(path: Path, size: tuple[int, int] | None = None) -> pygame.Surface:
    img = pygame.image.load(str(path)).convert()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


def circle_crop(src: pygame.Surface, diameter: int) -> pygame.Surface:
    src = pygame.transform.smoothscale(src, (diameter, diameter))
    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)
    out = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    out.blit(src, (0, 0))
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


def gender_icon(gender: str, size: int = 220) -> pygame.Surface:
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 8
    if gender == "Male":
        col = (90, 150, 220)
        pygame.draw.circle(s, (*col, 40), (cx, cy), size // 2 - 8)
        pygame.draw.circle(s, col, (cx, cy + 18), 46, 7)
        pygame.draw.line(s, col, (cx + 28, cy - 10), (cx + 62, cy - 48), 7)
        pygame.draw.line(s, col, (cx + 62, cy - 48), (cx + 38, cy - 48), 7)
        pygame.draw.line(s, col, (cx + 62, cy - 48), (cx + 62, cy - 24), 7)
    else:
        col = (220, 120, 170)
        pygame.draw.circle(s, (*col, 40), (cx, cy), size // 2 - 8)
        pygame.draw.circle(s, col, (cx, cy - 12), 46, 7)
        pygame.draw.line(s, col, (cx, cy + 34), (cx, cy + 78), 7)
        pygame.draw.line(s, col, (cx - 22, cy + 58), (cx + 22, cy + 58), 7)
    return s


class Assets:
    def __init__(self):
        self.races = {}
        self.races_sm = {}
        self.classes = {}
        self.factions = {}
        for name, fn in RACE_FILE.items():
            img = load_jpg(ASSET / "races" / fn)
            self.races[name] = pygame.transform.smoothscale(img, (460, 460))
            self.races_sm[name] = circle_crop(img, 168)
        for cls in CLASS_COLOR:
            img = load_jpg(ASSET / "classes" / f"{cls.lower()}.jpg")
            self.classes[cls] = circle_crop(img, 168)
        for fac in ("Alliance", "Horde"):
            img = load_jpg(ASSET / "factions" / f"{fac.lower()}.jpg")
            self.factions[fac] = circle_crop(img, 168)
        self.genders = {g: gender_icon(g, 168) for g in GENDERS}


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(40, 280)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(ang) * spd, math.sin(ang) * spd - 80
        self.max_life = self.life = random.uniform(0.35, 1.1)
        self.color = color
        self.size = random.randint(2, 5)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 420 * dt
        return self.life > 0

    def draw(self, surf):
        a = clamp(self.life / self.max_life, 0, 1)
        col = mix(self.color, GOLD_LT, 1 - a)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), max(1, int(self.size * a)))


# ---------------------------------------------------------------------------
# Slot
# ---------------------------------------------------------------------------
class Slot:
    def __init__(self, key, title, rect):
        self.key = key
        self.title = title
        self.rect = pygame.Rect(rect)
        self.items: list[str] = ["—"]
        self.winner = "—"
        self.pos = 0.0
        self.spinning = False
        self.locked = False
        self.t = 0.0
        self.duration = 1.0
        self.spins = 6
        self.flash = 0.0

    @property
    def current(self) -> str:
        if not self.items:
            return "—"
        i = int(math.floor(self.pos)) % len(self.items)
        return self.items[i]

    def idle(self, items, shown="—"):
        self.items = items or ["—"]
        self.winner = shown if shown in self.items else self.items[0]
        self.pos = float(self.items.index(self.winner) if self.winner in self.items else 0)
        self.spinning = False
        self.locked = shown != "—"

    def _target(self) -> int:
        return self.spins * len(self.items) + self.items.index(self.winner)

    def start(self, items, winner, duration):
        self.items = items
        self.winner = winner
        self.duration = duration / 1000.0
        self.t = 0.0
        self.spinning = True
        self.locked = False
        self.spins = 6
        self.pos = 0.0
        self.flash = 0.0

    def snap(self):
        if not self.spinning:
            return False
        self.t = self.duration
        self.pos = float(self._target())
        self.spinning = False
        self.locked = True
        self.flash = 0.45
        return True

    def update(self, dt) -> str | None:
        """Returns 'tick' or 'lock' event."""
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if not self.spinning:
            return None
        prev = int(math.floor(self.pos))
        self.t += dt
        p = clamp(self.t / self.duration, 0, 1)
        e = 1 - (1 - p) ** 3
        target = self._target()
        self.pos = target * e
        event = None
        now = int(math.floor(self.pos))
        if now != prev:
            event = "tick"
        if p >= 1:
            self.pos = float(target)
            self.spinning = False
            self.locked = True
            self.flash = 0.5
            event = "lock"
        return event


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class Forge:
    def __init__(self, portrait=False):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("WoW Forever — Character Forge")
        self.clock = pygame.time.Clock()
        self.portrait = portrait
        self.w, self.h = PORTRAIT if portrait else LANDSCAPE
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.assets = Assets()
        self.sfx = SFX()
        titles = ["FACTION", "RACE", "GENDER", "CLASS"]
        self.slots = {k: Slot(k, titles[i], (0, 0, 100, 100)) for i, k in enumerate(STAGES)}
        self.apply_layout()
        self.stage = "idle"
        self.result = {"faction": None, "race": None, "gender": None, "class": None}
        self.sparks: list[Spark] = []
        self.pulse = 0.0
        self.history: list[str] = []
        self.bg_shift = 0.0
        self.target_shift = 0.0
        self.shake = 0.0
        self.reveal_t = 0.0
        self.looks = [None, None, None]
        self.look_i = 0
        self.look_spin = 0.0
        self.look_preview = None
        self.toast = ""
        self.toast_t = 0.0
        for k, items in (
            ("faction", ["Alliance", "Horde"]),
            ("race", ["…"]),
            ("gender", GENDERS),
            ("class", ["…"]),
        ):
            self.slots[k].idle(items)

    def apply_layout(self):
        p = self.portrait
        self.w, self.h = PORTRAIT if p else LANDSCAPE
        self.font_title = self._font(["Palatino Linotype", "Georgia", "Times New Roman"], 40 if p else 58, True)
        self.font_sub = self._font(["Palatino Linotype", "Georgia"], 20 if p else 22, False)
        self.font_slot = self._font(["Trebuchet MS", "Segoe UI", "Arial"], 24 if p else 26, True)
        self.font_big = self._font(["Palatino Linotype", "Georgia"], 28 if p else 36, True)
        self.font_huge = self._font(["Palatino Linotype", "Georgia"], 32 if p else 42, True)
        self.font_small = self._font(["Trebuchet MS", "Segoe UI"], 15 if p else 16, False)
        self.font_tag = self._font(["Trebuchet MS", "Segoe UI"], 16 if p else 18, True)
        if p:
            self.portrait_rect = pygame.Rect(40, 118, 820, 560)
            gap, sw, sh = 14, 402, 210
            x0, y0 = 40, 694
            for i, k in enumerate(STAGES):
                col, row = i % 2, i // 2
                self.slots[k].rect = pygame.Rect(x0 + col * (sw + gap), y0 + row * (sh + gap), sw, sh)
            self.looks_rect = pygame.Rect(40, 1142, 820, 122)
            self.banner_rect = pygame.Rect(40, 1280, 820, 220)
        else:
            self.portrait_rect = pygame.Rect(56, 148, 476, 560)
            gap, sw, sh = 18, 250, 268
            total = 4 * sw + 3 * gap
            x0 = self.w - total - 48
            y0 = 168
            for i, k in enumerate(STAGES):
                self.slots[k].rect = pygame.Rect(x0 + i * (sw + gap), y0, sw, sh)
            self.looks_rect = pygame.Rect(x0, 456, total, 250)
            self.banner_rect = pygame.Rect(56, 728, self.w - 112, 86)

    def toggle_portrait(self):
        self.portrait = not self.portrait
        self.apply_layout()
        flags = self.screen.get_flags()
        self.screen = pygame.display.set_mode((self.w, self.h), flags & ~pygame.FULLSCREEN)

    def _font(self, names, size, bold):
        for n in names:
            path = pygame.font.match_font(n.replace(" ", "").lower(), bold=bold)
            if path:
                return pygame.font.Font(path, size)
        return pygame.font.SysFont(None, size, bold=bold)

    def pick_character(self):
        faction = random.choice(["Alliance", "Horde"])
        race = random.choice(RACES[faction])
        gender = random.choice(GENDERS)
        cls = random.choice(CLASSES[(faction, race)])
        self.result = {"faction": faction, "race": race, "gender": gender, "class": cls}

    def begin_roll(self):
        if self.stage not in ("idle", "done"):
            return
        self.pick_character()
        self.stage = "faction"
        self.reveal_t = 0.0
        self.slots["faction"].start(["Alliance", "Horde"], self.result["faction"], SPIN_MS["faction"])
        self.slots["race"].idle(["…"])
        self.slots["gender"].idle(GENDERS)
        self.slots["class"].idle(["…"])
        self.target_shift = 0.0
        self.looks = [None, None, None]
        self.look_i = 0
        self.look_spin = 0.0
        self.look_preview = None

    def skip_reel(self):
        for k in STAGES:
            if self.slots[k].spinning:
                if self.slots[k].snap():
                    self.sfx.play(self.sfx.lock, 0.85)
                    self.on_lock(k)
                return

    def on_lock(self, key):
        r = self.slots[key].rect
        color = GOLD
        if key == "faction":
            fac = self.result["faction"]
            color = ALLIANCE_C if fac == "Alliance" else HORDE_C
            self.target_shift = 1.0 if fac == "Alliance" else -1.0
            self.slots["race"].idle(RACES[fac])
        elif key == "race":
            color = mix(GOLD, CLASS_COLOR.get(self.result["class"], GOLD), 0.3)
        elif key == "class":
            color = CLASS_COLOR[self.result["class"]]
        for _ in range(28):
            self.sparks.append(Spark(r.centerx, r.centery, color))
        self.shake = 0.18
        nxt = {"faction": "race", "race": "gender", "gender": "class", "class": "done"}[key]
        if nxt == "done":
            self.stage = "done"
            self.reveal_t = 0.0
            line = self.combo_line()
            self.history = [line] + self.history[:6]
            self.looks = [roll_look(self.result["race"]), None, None]
            self.look_i = 0
            self.sfx.play(self.sfx.fanfare, 0.8)
            if self.is_new():
                self.sfx.play(self.sfx.sparkle, 0.9)
                for _ in range(70):
                    c = self.portrait_rect.center
                    self.sparks.append(Spark(c[0], c[1], GOLD_LT))
            return
        self.stage = nxt
        if nxt == "race":
            self.slots["race"].start(RACES[self.result["faction"]], self.result["race"], SPIN_MS["race"])
        elif nxt == "gender":
            self.slots["gender"].start(GENDERS, self.result["gender"], SPIN_MS["gender"])
        elif nxt == "class":
            pool = CLASSES[(self.result["faction"], self.result["race"])]
            self.slots["class"].start(pool, self.result["class"], SPIN_MS["class"])

    def combo_line(self) -> str:
        r = self.result
        return f"{r['faction']}  ·  {r['gender']} {r['race']} {r['class']}"

    def is_new(self) -> bool:
        r = self.result
        return (r["faction"], r["race"], r["class"]) in NEW_COMBOS

    def is_skyborne(self) -> bool:
        return self.result.get("race") == "Skyborne"

    def say(self, msg):
        self.toast = msg
        self.toast_t = 2.0

    def current_look(self):
        if self.look_preview:
            return self.look_preview
        return self.looks[self.look_i]

    def start_look_reroll(self):
        if self.stage != "done" or self.look_spin > 0:
            return
        self.look_spin = 1.15
        self.look_preview = roll_look(self.result["race"], self.looks[self.look_i])
        self.sfx.play(self.sfx.tick, 0.4)

    def select_look(self, i):
        if self.stage != "done" or self.look_spin > 0:
            return
        i = int(i)
        if i < 0 or i > 2:
            return
        if self.looks[i] is None:
            if self.looks[self.look_i] is None:
                return
            self.looks[i] = dict(self.looks[self.look_i])
            self.looks[i]["seed"] = random.randrange(1, 10**9)
            self.look_i = i
            self.sfx.play(self.sfx.lock, 0.55)
            self.say(f"Look {i + 1} saved. Reroll it with A.")
            return
        if i == self.look_i:
            return
        self.look_i = i
        self.sfx.play(self.sfx.sparkle, 0.55)
        c = self.portrait_rect.center
        for _ in range(24):
            self.sparks.append(Spark(c[0], c[1], self.looks[i]["color"][1]))
        self.say("Swapped instantly. No logout.")

    def look_hit(self, pos):
        if self.stage != "done" or not self.looks_rect.collidepoint(pos):
            return None
        w = self.looks_rect.w / 3
        return clamp(int((pos[0] - self.looks_rect.x) / w), 0, 2)

    def icon_for(self, key, value) -> pygame.Surface | None:
        if value in (None, "—", "…"):
            return None
        if key == "faction":
            return self.assets.factions.get(value)
        if key == "race":
            return self.assets.races_sm.get(value)
        if key == "gender":
            return self.assets.genders.get(value)
        if key == "class":
            return self.assets.classes.get(value)
        return None

    def update(self, dt):
        self.pulse += dt
        self.bg_shift = lerp(self.bg_shift, self.target_shift, 1 - math.exp(-dt * 3))
        self.shake = max(0.0, self.shake - dt)
        if self.stage == "done":
            self.reveal_t += dt
        if self.toast_t > 0:
            self.toast_t = max(0.0, self.toast_t - dt)
        if self.look_spin > 0:
            prev = int(self.look_spin * 10)
            self.look_spin = max(0.0, self.look_spin - dt)
            if int(self.look_spin * 10) != prev:
                self.look_preview = roll_look(self.result["race"])
                self.sfx.play(self.sfx.tick, 0.28)
            if self.look_spin <= 0:
                self.looks[self.look_i] = roll_look(self.result["race"], self.looks[self.look_i])
                self.look_preview = None
                self.sfx.play(self.sfx.lock, 0.8)
                c = self.portrait_rect.center
                col = self.looks[self.look_i]["color"][1]
                for _ in range(36):
                    self.sparks.append(Spark(c[0], c[1], col))
                self.say("Appearance rerolled. No logout.")
        self.sparks = [p for p in self.sparks if p.update(dt)]
        for k, slot in self.slots.items():
            ev = slot.update(dt)
            if ev == "tick":
                p = clamp(slot.t / slot.duration, 0, 1)
                snd = self.sfx.tick_lo if p > 0.65 else self.sfx.tick
                self.sfx.play(snd, 0.35 + 0.25 * (1 - p))
            elif ev == "lock":
                self.sfx.play(self.sfx.lock, 0.85)
                self.on_lock(k)

    def draw_bg(self, surf):
        surf.fill(INK)
        if self.bg_shift > 0.02:
            overlay = pygame.Surface((self.w, self.h))
            overlay.fill(ALLIANCE_C)
            overlay.set_alpha(int(28 * self.bg_shift))
            surf.blit(overlay, (0, 0))
        elif self.bg_shift < -0.02:
            overlay = pygame.Surface((self.w, self.h))
            overlay.fill(HORDE_C)
            overlay.set_alpha(int(32 * -self.bg_shift))
            surf.blit(overlay, (0, 0))
        for i in range(18):
            y = int((self.pulse * 28 + i * 70) % (self.h + 80)) - 40
            pygame.draw.line(surf, (22, 18, 12), (0, y), (self.w, y), 1)
        pygame.draw.rect(surf, GOLD_DK, (16, 16, self.w - 32, self.h - 32), 2)
        pygame.draw.rect(surf, GOLD, (22, 22, self.w - 44, self.h - 44), 1)
        for cx, cy in ((22, 22), (self.w - 22, 22), (22, self.h - 22), (self.w - 22, self.h - 22)):
            pygame.draw.circle(surf, GOLD, (cx, cy), 5)

    def draw_text(self, surf, font, text, pos, color=WHITE, center=False, glow=False):
        if glow:
            g = font.render(text, True, mix(color, (0, 0, 0), 0.6))
            gx, gy = pos
            if center:
                r = g.get_rect(center=pos)
                gx, gy = r.topleft
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surf.blit(g, (gx + dx, gy + dy))
        img = font.render(text, True, color)
        rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        surf.blit(img, rect)
        return rect

    def panel(self, surf, rect, fill=PARCHMENT, border=GOLD, thick=2, flash=0.0):
        pygame.draw.rect(surf, fill, rect, border_radius=10)
        col = mix(border, GOLD_LT, flash)
        pygame.draw.rect(surf, col, rect, thick, border_radius=10)
        pygame.draw.rect(surf, mix(col, (0, 0, 0), 0.4), rect.inflate(-8, -8), 1, border_radius=8)

    def draw_header(self, surf):
        cx = self.w // 2
        if self.portrait:
            self.draw_text(surf, self.font_title, "WOW FOREVER", (cx, 48), GOLD_LT, True, True)
            self.draw_text(surf, self.font_sub, "CHARACTER FORGE  ·  VERTICAL", (cx, 88), MUTED, True)
        else:
            self.draw_text(surf, self.font_title, "WORLD OF WARCRAFT: FOREVER", (cx, 58), GOLD_LT, True, True)
            self.draw_text(surf, self.font_sub, "CHARACTER FORGE  ·  BETA LAUNCH ROLLER", (cx, 102), MUTED, True)

    def draw_portrait(self, surf):
        frame = self.portrait_rect
        self.panel(surf, frame, (16, 12, 10), GOLD, 3)
        inner = frame.inflate(-24, -24)
        race = self.result.get("race") if self.slots["race"].locked else None
        if race and race in self.assets.races:
            img = self.assets.races[race]
            clip = pygame.Surface(inner.size)
            scale = max(inner.w / img.get_width(), inner.h / img.get_height())
            nw, nh = int(img.get_width() * scale), int(img.get_height() * scale)
            fitted = pygame.transform.smoothscale(img, (nw, nh))
            sx = (nw - inner.w) // 2
            sy = (nh - inner.h) // 2
            clip.blit(fitted, (0, 0), pygame.Rect(sx, sy, inner.w, inner.h))
            if self.result.get("gender") == "Female" and self.slots["gender"].locked:
                tint = pygame.Surface(inner.size)
                tint.fill((40, 8, 28))
                tint.set_alpha(36)
                clip.blit(tint, (0, 0))
            elif self.result.get("gender") == "Male" and self.slots["gender"].locked:
                tint = pygame.Surface(inner.size)
                tint.fill((8, 18, 40))
                tint.set_alpha(28)
                clip.blit(tint, (0, 0))
            if self.slots["class"].locked:
                wash = pygame.Surface(inner.size)
                wash.fill(CLASS_COLOR[self.result["class"]])
                wash.set_alpha(18)
                clip.blit(wash, (0, 0))
            look = self.current_look() if self.stage == "done" else None
            if look:
                self._paint_look(clip, look)
            surf.blit(clip, inner.topleft)
        else:
            pygame.draw.rect(surf, (10, 8, 6), inner)
            msg = "PRESS  SPACE  TO  ROLL"
            if self.stage not in ("idle", "done"):
                msg = "THE DICE ARE FALLING…"
            self.draw_text(surf, self.font_slot, msg, inner.center, MUTED, True)

        if self.slots["class"].locked:
            badge = pygame.transform.smoothscale(self.assets.classes[self.result["class"]], (88, 88))
            bx, by = inner.right - 108, inner.bottom - 108
            pygame.draw.circle(surf, (12, 10, 8), (bx + 44, by + 44), 50)
            pygame.draw.circle(surf, GOLD, (bx + 44, by + 44), 50, 3)
            surf.blit(badge, (bx, by))

        if self.slots["faction"].locked:
            fac = self.result["faction"]
            crest = pygame.transform.smoothscale(self.assets.factions[fac], (72, 72))
            pygame.draw.circle(surf, (12, 10, 8), (inner.left + 48, inner.top + 48), 42)
            pygame.draw.circle(surf, GOLD, (inner.left + 48, inner.top + 48), 42, 3)
            surf.blit(crest, (inner.left + 12, inner.top + 12))

        if self.toast_t > 0 and self.toast:
            a = clamp(self.toast_t / 0.4, 0, 1) if self.toast_t < 0.4 else 1
            pill = self.font_tag.render(self.toast, True, INK)
            pr = pill.get_rect(center=(frame.centerx, frame.bottom - 28))
            box = pr.inflate(28, 14)
            shade = pygame.Surface(box.size, pygame.SRCALPHA)
            shade.fill((246, 221, 140, int(230 * a)))
            surf.blit(shade, box.topleft)
            pygame.draw.rect(surf, GOLD, box, 1, border_radius=8)
            surf.blit(pill, pr)

    def _paint_look(self, clip, look):
        w, h = clip.get_size()
        wash = pygame.Surface((w, h))
        wash.fill(look["color"][1])
        wash.set_alpha(42)
        clip.blit(wash, (0, 0))
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*look["eyes"][1], 36), (int(w * 0.50), int(h * 0.34)), 70)
        clip.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if look["mark"] != "None":
            rng = random.Random(look["seed"])
            m = pygame.Surface((w, h), pygame.SRCALPHA)
            col = (*look["color"][1], 110)
            for _ in range(7):
                x = rng.randint(int(w * 0.22), int(w * 0.78))
                y = rng.randint(int(h * 0.22), int(h * 0.58))
                pygame.draw.line(
                    m,
                    col,
                    (x, y),
                    (x + rng.randint(-24, 24), y + rng.randint(6, 30)),
                    rng.choice((2, 2, 3)),
                )
            clip.blit(m, (0, 0))

    def draw_wardrobe(self, surf):
        r = self.looks_rect
        self.panel(surf, r, (18, 14, 10), GOLD, 2)
        title = "APPEARANCES  ·  REROLL ANYTIME  ·  SWAP INSTANTLY"
        self.draw_text(surf, self.font_tag, title, (r.x + 16, r.y + 10), GOLD)
        gap = 10
        card_w = (r.w - 32 - 2 * gap) / 3
        card_h = r.h - 52
        for i in range(3):
            cx = r.x + 16 + i * (card_w + gap)
            cr = pygame.Rect(cx, r.y + 36, card_w, card_h)
            look = self.looks[i]
            active = i == self.look_i and self.stage == "done"
            border = GOLD_LT if active else (GOLD if look else GOLD_DK)
            fill = (40, 32, 18) if active else (22, 16, 12)
            pygame.draw.rect(surf, fill, cr, border_radius=8)
            pygame.draw.rect(surf, border, cr, 2 if active else 1, border_radius=8)
            label = f"LOOK {i + 1}"
            compact = cr.h < 100
            if compact:
                self.draw_text(surf, self.font_small, label, (cr.centerx, cr.centery - 14), GOLD_LT if active else MUTED, True)
                if look:
                    pygame.draw.circle(surf, look["color"][1], (cr.x + 18, cr.centery + 12), 7)
                    pygame.draw.circle(surf, look["eyes"][1], (cr.x + 36, cr.centery + 12), 7)
                    self.draw_text(surf, self.font_small, look["hair"], (cr.centerx + 16, cr.centery + 12), WHITE, True)
                else:
                    self.draw_text(surf, self.font_small, "empty", (cr.centerx, cr.centery + 12), MUTED, True)
            else:
                self.draw_text(surf, self.font_small, label, (cr.centerx, cr.y + 16), GOLD_LT if active else MUTED, True)
                if look:
                    pygame.draw.circle(surf, look["color"][1], (cr.centerx - 18, cr.y + 48), 10)
                    pygame.draw.circle(surf, look["eyes"][1], (cr.centerx + 18, cr.y + 48), 10)
                    pygame.draw.circle(surf, GOLD, (cr.centerx - 18, cr.y + 48), 10, 1)
                    pygame.draw.circle(surf, GOLD, (cr.centerx + 18, cr.y + 48), 10, 1)
                    self.draw_text(surf, self.font_small, look["hair"], (cr.centerx, cr.bottom - 22), WHITE, True)
                else:
                    self.draw_text(surf, self.font_small, "empty", (cr.centerx, cr.centery + 8), MUTED, True)

    def draw_slot(self, surf, slot: Slot):
        r = slot.rect
        flash = slot.flash
        fill = (24, 18, 12) if not slot.locked else (32, 24, 14)
        self.panel(surf, r, fill, GOLD_LT if slot.spinning else GOLD, 2, flash)
        self.draw_text(surf, self.font_tag, slot.title, (r.centerx, r.y + 22), GOLD, True)

        window = pygame.Rect(r.x + 18, r.y + 48, r.w - 36, r.h - 96)
        pygame.draw.rect(surf, (8, 6, 5), window, border_radius=8)
        cx, cy = window.centerx, window.centery - 6
        if slot.locked:
            name = slot.winner
            icon = self.icon_for(slot.key, name)
            if icon:
                ic = pygame.transform.smoothscale(icon, (96, 96))
                surf.blit(ic, ic.get_rect(center=(cx, cy - 18)))
            col = self._name_color(slot.key, name)
            self.draw_text(surf, self.font_slot, name, (cx, cy + 52), col, True)
        else:
            item_h = 72
            n = max(1, len(slot.items))
            for k in (-1, 0, 1):
                idx = int(math.floor(slot.pos)) + k
                name = slot.items[idx % n]
                frac = slot.pos - math.floor(slot.pos)
                y = cy + (k - frac) * item_h
                icon = self.icon_for(slot.key, name)
                if icon and window.collidepoint(cx, int(y)):
                    ic = pygame.transform.smoothscale(icon, (52, 52))
                    if k != 0:
                        ic.set_alpha(110)
                    surf.blit(ic, ic.get_rect(center=(cx, int(y) - 10)))
                col = self._name_color(slot.key, name) if k == 0 else MUTED
                img = self.font_slot.render(name, True, col)
                ir = img.get_rect(center=(cx, int(y) + 26 if icon else int(y)))
                if window.colliderect(ir.inflate(0, -4)):
                    surf.blit(img, ir)
            pygame.draw.rect(surf, GOLD, (window.x, window.centery - 40, window.w, 80), 1, border_radius=6)
        status = "LOCKED" if slot.locked else ("SPINNING" if slot.spinning else "WAITING")
        sc = GOLD_LT if slot.locked else (MUTED if not slot.spinning else GOLD)
        self.draw_text(surf, self.font_small, status, (r.centerx, r.bottom - 22), sc, True)

    def _name_color(self, key, name):
        if key == "class" and name in CLASS_COLOR:
            return CLASS_COLOR[name]
        if key == "faction" and name == "Alliance":
            return ALLIANCE_C
        if key == "faction" and name == "Horde":
            return HORDE_C
        return WHITE

    def draw_result_banner(self, surf):
        banner = self.banner_rect
        self.panel(surf, banner, (18, 14, 10), GOLD, 2)
        if self.stage == "done":
            col = CLASS_COLOR[self.result["class"]]
            if self.portrait:
                r = self.result
                self.draw_text(surf, self.font_big, r["faction"].upper(), (banner.centerx, banner.y + 48), col, True, True)
                self.draw_text(
                    surf,
                    self.font_huge,
                    f"{r['gender']} {r['race']} {r['class']}".upper(),
                    (banner.centerx, banner.y + 108),
                    col,
                    True,
                    True,
                )
            else:
                self.draw_text(surf, self.font_huge, self.combo_line().upper(), (banner.centerx, banner.centery - 4), col, True, True)
            tags = []
            if self.is_new():
                tags.append("NEW FOREVER COMBO")
            if self.is_skyborne():
                tags.append("NEW RACE")
            if tags:
                blink = 0.55 + 0.45 * abs(math.sin(self.pulse * 6))
                tag = "  ·  ".join(tags)
                c = mix(GOLD, GOLD_LT, blink)
                pill = self.font_tag.render(tag, True, INK)
                pr = pill.get_rect(center=(banner.centerx, banner.y - 18))
                pygame.draw.rect(surf, c, pr.inflate(28, 12), border_radius=8)
                surf.blit(pill, pr)
        elif self.stage == "idle":
            msg = "SPACE to roll a destiny" if self.portrait else "Waiting on servers?  Roll a destiny.   SPACE to begin"
            self.draw_text(surf, self.font_big, msg, banner.center, MUTED, True)
        else:
            labels = {"faction": "Choosing a banner…", "race": "Calling a people…", "gender": "Shaping a face…", "class": "Binding a calling…"}
            self.draw_text(surf, self.font_big, labels.get(self.stage, "Rolling…"), banner.center, GOLD_LT, True)

    def draw_help(self, surf):
        if self.portrait:
            help_l = "SPACE roll   A look   1-3 swap   TAB snap   V landscape   ESC quit"
        else:
            help_l = "SPACE roll   A reroll look   1 2 3 swap looks   TAB snap   V vertical   F full   M mute   S shot   ESC quit"
        mute = "   MUTED" if self.sfx.muted else ""
        self.draw_text(surf, self.font_small, help_l + mute, (self.w // 2, self.h - 36), MUTED, True)

    def draw(self):
        ox = oy = 0
        if self.shake > 0:
            mag = 6 * self.shake
            ox = int(random.uniform(-mag, mag))
            oy = int(random.uniform(-mag, mag))
        surf = self.screen
        if ox or oy:
            surf = pygame.Surface((self.w, self.h))
        self.draw_bg(surf)
        self.draw_header(surf)
        self.draw_portrait(surf)
        for slot in self.slots.values():
            self.draw_slot(surf, slot)
        self.draw_wardrobe(surf)
        self.draw_result_banner(surf)
        self.draw_help(surf)
        for p in self.sparks:
            p.draw(surf)
        if ox or oy:
            self.screen.blit(surf, (ox, oy))
        pygame.display.flip()

    def screenshot(self):
        SHOTS.mkdir(exist_ok=True)
        n = 1
        while True:
            path = SHOTS / f"roll_{n:03d}.png"
            if not path.exists():
                break
            n += 1
        pygame.image.save(self.screen, str(path))
        return path

    def handle(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.begin_roll()
            elif e.key in (pygame.K_a, pygame.K_r):
                self.start_look_reroll()
            elif e.key in (pygame.K_1, pygame.K_KP1):
                self.select_look(0)
            elif e.key in (pygame.K_2, pygame.K_KP2):
                self.select_look(1)
            elif e.key in (pygame.K_3, pygame.K_KP3):
                self.select_look(2)
            elif e.key == pygame.K_TAB:
                self.skip_reel()
            elif e.key == pygame.K_m:
                self.sfx.muted = not self.sfx.muted
            elif e.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
            elif e.key == pygame.K_s:
                self.screenshot()
            elif e.key == pygame.K_v:
                self.toggle_portrait()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            hit = self.look_hit(e.pos)
            if hit is not None:
                self.select_look(hit)
            else:
                self.begin_roll()
        return True

    def run(self, auto=False, frames=0, save=None):
        running = True
        frame = 0
        if auto:
            self.begin_roll()
        while running:
            dt = self.clock.tick(60) / 1000.0
            for e in pygame.event.get():
                running = self.handle(e) and running
            self.update(dt)
            self.draw()
            frame += 1
            if frames and frame >= frames:
                if save:
                    pygame.image.save(self.screen, str(save))
                break
            if auto and self.stage == "done" and self.reveal_t > 1.2:
                if save:
                    pygame.image.save(self.screen, str(save))
                break
        pygame.quit()


def check_matrix():
    n = 0
    for fac, races in RACES.items():
        for race in races:
            n += len(CLASSES[(fac, race)])
    print(f"Valid faction/race/class combos: {n}  (x2 gender = {n * 2} characters)")
    print("New launch combos:")
    for c in sorted(NEW_COMBOS):
        print("  ", " / ".join(c))
    assert n == 56, n
    print("OK")


def main():
    if "--check" in sys.argv:
        check_matrix()
        return
    portrait = "--portrait" in sys.argv or "--vertical" in sys.argv
    auto = "--auto" in sys.argv
    save = None
    frames = 0
    if "--shot" in sys.argv:
        auto = True
        SHOTS.mkdir(exist_ok=True)
        save = SHOTS / ("preview-portrait.png" if portrait else "preview.png")
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    Forge(portrait=portrait).run(auto=auto, frames=frames, save=save)
    if save:
        print(f"saved {save}")


if __name__ == "__main__":
    main()
