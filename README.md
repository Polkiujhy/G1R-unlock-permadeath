# Gothic 1 Remake Save Unlocker

Small CLI tool for Gothic 1 Remake saves on Steam/Proton.

It clears the persistent profile flag that marks a slot as blocked after permanent death:

```text
m_PermanentDeathGameOver -> 0x00
```

The numbered save file, for example `G1R-042.sav`, is not modified. The tool edits `PersistentDataList.sav` and creates a timestamped backup by default.

## Usage

List detected profiles and slots:

```bash
python3 g1r_unlock_permadeath.py --list
```

Preview a fix:

```bash
python3 g1r_unlock_permadeath.py --dry-run G1R-042
```

Unlock a slot:

```bash
python3 g1r_unlock_permadeath.py G1R-042
```

Short slot forms also work:

```bash
python3 g1r_unlock_permadeath.py 42
python3 g1r_unlock_permadeath.py 042
```

Use a custom save file:

```bash
python3 g1r_unlock_permadeath.py --file /path/to/PersistentDataList.sav G1R-042
```

## Default Save Path

On Linux/Steam Proton, the default path is:

```text
~/.local/share/Steam/steamapps/compatdata/1297900/pfx/drive_c/users/steamuser/AppData/Local/G1R/Saved/SaveGames/PersistentDataList.sav
```

On Windows, the default path is:

```text
%LOCALAPPDATA%\G1R\Saved\SaveGames\PersistentDataList.sav
```

Use `--file` if your save is elsewhere.

## Notes

This only clears the persistent game-over lock for the profile containing the requested slot. It does not edit the Oodle-compressed numbered save body.
