# G1R Unlock Permadeath

Unlocks a Gothic 1 Remake permadeath save after the game marks the profile as dead.

It edits `PersistentDataList.sav`, finds the profile containing the requested slot, and clears `m_PermanentDeathGameOver`. The numbered save file like `G1R-042.sav` is not modified. A backup is created automatically.

## Usage

```bash
python g1r_unlock_permadeath.py --list
python g1r_unlock_permadeath.py --dry-run G1R-042
python g1r_unlock_permadeath.py G1R-042
```

Short slot forms also work:

```bash
python g1r_unlock_permadeath.py 42
python g1r_unlock_permadeath.py 042
```

If auto-detection fails:

```bash
python g1r_unlock_permadeath.py --file "C:\Users\You\AppData\Local\G1R\Saved\SaveGames\PersistentDataList.sav" G1R-042
```

## Default Paths

Windows:
`%LOCALAPPDATA%\G1R\Saved\SaveGames\PersistentDataList.sav`

Linux/Steam Proton:
`~/.local/share/Steam/steamapps/compatdata/1297900/pfx/drive_c/users/steamuser/AppData/Local/G1R/Saved/SaveGames/PersistentDataList.sav`
