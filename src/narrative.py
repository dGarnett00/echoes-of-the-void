"""Narrative engine: events, branching, act progression."""

from __future__ import annotations
import os
import yaml
from typing import Dict, List, Optional, Set


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class NarrativeEngine:
    """Manages story events and Act I progression."""

    def __init__(self) -> None:
        self.events:  Dict[str, dict] = {}
        self.fired:   Set[str] = set()        # event IDs already triggered
        self._load_events()

    def _load_events(self) -> None:
        path = os.path.join(DATA_DIR, "events.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.events = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.events = {}

    # ── Event checking ─────────────────────────────────────────────────────

    def get_pending_events(
        self,
        cycle: int,
        flags: Dict[str, bool],
    ) -> List[dict]:
        """Return events that should fire this cycle (not yet fired)."""
        pending = []
        for event_id, event in self.events.items():
            if event_id in self.fired:
                continue
            # Cycle trigger
            trigger_cycle = event.get("cycle_trigger", 0)
            if cycle < trigger_cycle:
                continue
            # Flag requirements
            required_flags = event.get("flags_required", [])
            if not all(flags.get(f, False) for f in required_flags):
                continue
            pending.append(event)
        # Sort by cycle_trigger so they fire in order
        pending.sort(key=lambda e: e.get("cycle_trigger", 0))
        return pending

    def mark_fired(self, event_id: str) -> None:
        self.fired.add(event_id)

    def fire_event(self, event_id: str, flags: Dict[str, bool]) -> Optional[dict]:
        """Mark an event as fired and apply its flag effects."""
        event = self.events.get(event_id)
        if event:
            self.fired.add(event_id)
            for flag in event.get("sets_flags", []):
                flags[flag] = True
        return event

    def is_act_complete(self, flags: Dict[str, bool]) -> bool:
        return flags.get("act_1_complete", False)

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {"fired": list(self.fired)}

    def apply_state(self, data: dict) -> None:
        self.fired = set(data.get("fired", []))
