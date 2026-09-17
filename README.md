# WoW Forever Character Forge

Stream overlay that rolls a legal **World of Warcraft: Forever** character.

Order: **Faction → Race → Gender → Class** (class is filtered by faction + race).

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

## Keys

| Key | Action |
|---|---|
| Space / click | Roll |
| Tab | Snap current reel |
| V | Toggle vertical / landscape |
| F | Fullscreen |
| M | Mute |
| S | Screenshot |
| Esc | Quit |

Window sizes: landscape `1600×900`, portrait `900×1600`.
