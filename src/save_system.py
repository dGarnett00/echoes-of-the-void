"""Save/load game state using YAML files."""

from __future__ import annotations
import os
import yaml
from datetime import datetime
from typing import Optional


SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


def _ensure_save_dir() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"save_slot_{slot}.yaml")


class SaveSystem:
    """Handles save/load of complete game state."""

    MAX_SLOTS: int = 3

    def save(self, state: dict, slot: int = 1) -> tuple[bool, str]:
        """Save game state to a YAML file.

        Returns (success, message).
        """
        if not (1 <= slot <= self.MAX_SLOTS):
            return False, f"Invalid save slot {slot}. Use 1–{self.MAX_SLOTS}."

        _ensure_save_dir()
        path = save_path(slot)

        state["meta"] = {
            "saved_at": datetime.now().isoformat(),
            "version": "0.1.0",
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(state, f, allow_unicode=True, default_flow_style=False)
            return True, f"Game saved to slot {slot}."
        except OSError as e:
            return False, f"Save failed: {e}"

    def load(self, slot: int = 1) -> tuple[Optional[dict], str]:
        """Load game state from a YAML file.

        Returns (state_dict or None, message).
        """
        if not (1 <= slot <= self.MAX_SLOTS):
            return None, f"Invalid save slot {slot}. Use 1–{self.MAX_SLOTS}."

        path = save_path(slot)
        if not os.path.exists(path):
            return None, f"No save found in slot {slot}."

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return None, "Save file is corrupted."
            meta = data.get("meta", {})
            saved_at = meta.get("saved_at", "unknown")
            return data, f"Game loaded from slot {slot} (saved {saved_at})."
        except (OSError, yaml.YAMLError) as e:
            return None, f"Load failed: {e}"

    def list_saves(self) -> list[dict]:
        """Return metadata for all existing save slots."""
        slots = []
        for slot in range(1, self.MAX_SLOTS + 1):
            path = save_path(slot)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    meta = data.get("meta", {}) if isinstance(data, dict) else {}
                    player = data.get("player", {}) if isinstance(data, dict) else {}
                    slots.append({
                        "slot":     slot,
                        "exists":   True,
                        "saved_at": meta.get("saved_at", "unknown"),
                        "cycle":    player.get("cycle", 0),
                        "location": player.get("location", "unknown"),
                    })
                except (OSError, yaml.YAMLError):
                    slots.append({"slot": slot, "exists": True, "saved_at": "corrupted"})
            else:
                slots.append({"slot": slot, "exists": False})
        return slots

    def delete(self, slot: int) -> tuple[bool, str]:
        """Delete a save slot."""
        if not (1 <= slot <= self.MAX_SLOTS):
            return False, f"Invalid slot {slot}."
        path = save_path(slot)
        if os.path.exists(path):
            os.remove(path)
            return True, f"Save slot {slot} deleted."
        return False, f"No save in slot {slot}."
