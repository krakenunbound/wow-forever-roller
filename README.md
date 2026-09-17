# WoW Forever Character Forge

Stream overlay that rolls a legal **World of Warcraft: Forever** character.

Order: **Faction → Gender → Race → Class** (class is filtered by faction + race).

Race portraits stay hidden until gender is locked, and every race has a male and female painting.

Includes Skyborne and the six launch combos (Human Hunter, Gnome Priest, Dwarf Shaman, Orc Mage, Troll Warlock, Undead Paladin).

## Run

```bat
python -m pip install -r requirements.txt
python wow_forever_roller.py
```

Portrait / vertical stream:

```bat
python wow_forever_roller.py --portrait
```

Or use `run.bat` / `run-portrait.bat`.

## Appearances (Forever barber)

After a character locks you can **reroll looks anytime** and **swap saved appearances instantly** — no fake logout.

| Key | Action |
|---|---|
| **A** or **R** | Reroll current look (keeps faction / race / gender / class) |
| **1** **2** **3** | Swap to that look. Empty slot saves a copy of the current look. |
| Click a look card | Same as 1 / 2 / 3 |

## Keys

| Key | Action |
|---|---|
| Space / click | Roll a new character |
| Tab | Snap current reel |
| V | Toggle vertical / landscape |
| F | Fullscreen |
| M | Mute |
| S | Screenshot |
| Esc | Quit |

Window sizes: landscape `1600×900`, portrait `900×1600`.
