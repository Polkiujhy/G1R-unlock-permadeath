#!/usr/bin/env python3
"""
Clear Gothic 1 Remake's persistent "permanent death game over" profile flag.

The numbered save file is not modified. This edits PersistentDataList.sav,
finds the profile that contains a given G1R-### slot, and clears only that
profile's m_PermanentDeathGameOver BoolProperty byte.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


PERSISTENT_FILE = "PersistentDataList.sav"
SLOT_RE = re.compile(rb"G1R-\d{3}")


def default_save_dir() -> Path:
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "G1R" / "Saved" / "SaveGames"
        return Path.home() / "AppData" / "Local" / "G1R" / "Saved" / "SaveGames"

    return (
        Path.home()
        / ".local/share/Steam/steamapps/compatdata/1297900/pfx/drive_c/users/steamuser"
        / "AppData/Local/G1R/Saved/SaveGames"
    )


@dataclass(frozen=True)
class BoolField:
    field_offset: int
    value_offset: int
    value: int


@dataclass(frozen=True)
class ProfileBlock:
    index: int
    start: int
    end: int
    slots: tuple[str, ...]


def normalize_slot(slot: str) -> str:
    slot = slot.strip().upper()
    if slot.endswith(".SAV"):
        slot = slot[:-4]
    if re.fullmatch(r"\d{1,3}", slot):
        slot = f"G1R-{int(slot):03d}"
    if not re.fullmatch(r"G1R-\d{3}", slot):
        raise ValueError("slot must look like G1R-042, 042, or 42")
    return slot


def load_data(path: Path) -> bytearray:
    if not path.exists():
        raise FileNotFoundError(path)
    return bytearray(path.read_bytes())


def profile_blocks(data: bytes) -> list[ProfileBlock]:
    profiles_offset = data.find(b"m_Profiles\x00")
    if profiles_offset < 0:
        raise ValueError("could not find m_Profiles in PersistentDataList.sav")

    starts = [m.start() - 4 for m in re.finditer(b"m_ProfileName\x00", data[profiles_offset:])]
    starts = [profiles_offset + start for start in starts]
    if not starts:
        raise ValueError("could not find any profile blocks")

    blocks: list[ProfileBlock] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(data)
        slots = tuple(sorted({m.group().decode("ascii") for m in SLOT_RE.finditer(data[start:end])}))
        blocks.append(ProfileBlock(index=index, start=start, end=end, slots=slots))
    return blocks


def find_profile_for_slot(data: bytes, slot: str) -> ProfileBlock:
    matches = [block for block in profile_blocks(data) if slot in block.slots]
    if not matches:
        known = sorted({slot for block in profile_blocks(data) for slot in block.slots})
        raise ValueError(f"{slot} was not found in any profile. Known slots: {', '.join(known)}")
    if len(matches) > 1:
        indexes = ", ".join(str(block.index) for block in matches)
        raise ValueError(f"{slot} appears in multiple profile blocks: {indexes}")
    return matches[0]


def find_bool_field(data: bytes, block: ProfileBlock, name: bytes) -> BoolField:
    field = name + b"\x00"
    field_offset = data.find(field, block.start, block.end)
    if field_offset < 0:
        raise ValueError(f"{name.decode()} was not found in profile block {block.index}")

    type_offset = data.find(b"BoolProperty\x00", field_offset, block.end)
    if type_offset < 0:
        raise ValueError(f"{name.decode()} is missing its BoolProperty tag")

    # In these save files BoolProperty stores its inline byte directly after
    # the eight-byte tag payload header. Nonzero means true; clearing to 0
    # removes the game-over lock while leaving the profile/run settings intact.
    value_offset = type_offset + len(b"BoolProperty\x00") + 8
    if value_offset >= len(data):
        raise ValueError(f"{name.decode()} value offset is outside the file")

    return BoolField(field_offset=field_offset, value_offset=value_offset, value=data[value_offset])


def backup_path(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.backup-{stamp}")


def unlock(path: Path, slot: str, dry_run: bool, no_backup: bool) -> int:
    data = load_data(path)
    block = find_profile_for_slot(data, slot)
    death = find_bool_field(data, block, b"m_PermanentDeath")
    game_over = find_bool_field(data, block, b"m_PermanentDeathGameOver")

    print(f"file: {path}")
    print(f"slot: {slot}")
    print(f"profile block: {block.index}")
    print(f"profile slots: {', '.join(block.slots) if block.slots else '(none)'}")
    print(f"m_PermanentDeath: offset {death.value_offset}, value 0x{death.value:02x}")
    print(
        "m_PermanentDeathGameOver: "
        f"offset {game_over.value_offset}, value 0x{game_over.value:02x}"
    )

    if game_over.value == 0:
        print("already unlocked: m_PermanentDeathGameOver is already 0x00")
        return 0

    if dry_run:
        print("dry run: would clear m_PermanentDeathGameOver to 0x00")
        return 0

    if not no_backup:
        backup = backup_path(path)
        shutil.copy2(path, backup)
        print(f"backup: {backup}")

    data[game_over.value_offset] = 0
    path.write_bytes(data)
    print("updated: m_PermanentDeathGameOver cleared to 0x00")
    return 0


def list_profiles(path: Path) -> int:
    data = load_data(path)
    print(f"file: {path}")
    for block in profile_blocks(data):
        summary = []
        for name in (b"m_PermanentDeath", b"m_PermanentDeathGameOver"):
            try:
                field = find_bool_field(data, block, name)
                summary.append(f"{name.decode()}=0x{field.value:02x}")
            except ValueError:
                summary.append(f"{name.decode()}=?")
        slots = ", ".join(block.slots) if block.slots else "(none)"
        print(f"profile {block.index}: {slots} | {'; '.join(summary)}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unlock a Gothic 1 Remake save profile after permanent death."
    )
    parser.add_argument(
        "slot",
        nargs="?",
        help="slot to unlock, e.g. G1R-042, 042, or 42",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=default_save_dir(),
        help="SaveGames directory. Default: auto-detected Steam/Proton or Windows path.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="PersistentDataList.sav path. Overrides --save-dir.",
    )
    parser.add_argument("--dry-run", action="store_true", help="show what would change")
    parser.add_argument("--no-backup", action="store_true", help="do not create a backup")
    parser.add_argument("--list", action="store_true", help="list profiles and slots")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    path = args.file if args.file else args.save_dir / PERSISTENT_FILE

    try:
        if args.list:
            return list_profiles(path)
        if not args.slot:
            raise ValueError("slot is required unless --list is used")
        slot = normalize_slot(args.slot)
        return unlock(path=path, slot=slot, dry_run=args.dry_run, no_backup=args.no_backup)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
