"""NPC system: factions, relationships, dialogue trees."""

from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FACTIONS = {
    "navigators": "The Navigators",
    "keepers":    "The Keepers",
    "listeners":  "The Listeners",
    "ghosts":     "The Ghosts",
    "neutral":    "Independent",
}


@dataclass
class NPC:
    """A non-player character aboard the Meridian."""
    npc_id:       str
    name:         str
    full_name:    str
    faction:      str
    location:     str
    relationship: int   # -100 to 100
    description:  str
    dialogue:     Dict[str, str] = field(default_factory=dict)
    knowledge:    List[str]      = field(default_factory=list)
    hidden_info:  Optional[str]  = None
    flags:        Dict[str, Any] = field(default_factory=dict)

    # ── Dialogue ──────────────────────────────────────────────────────────

    def get_dialogue(self, topic: str = "default",
                     game_flags: Optional[Dict] = None) -> str:
        """Return dialogue appropriate to relationship and topic."""
        game_flags = game_flags or {}

        # Low trust gatekeeping
        if self.relationship < -20 and topic == "default":
            return self.dialogue.get("trust_low", self._default_hostile())

        # High trust unlocks special dialogue
        if self.relationship >= 60 and topic == "default":
            high = self.dialogue.get("trust_high")
            if high:
                return high

        # Topic-specific response
        response = self.dialogue.get(f"{topic}_topic")
        if response:
            return response

        # Default
        return self.dialogue.get("default", f"{self.name} has nothing to say right now.")

    def _default_hostile(self) -> str:
        return f"{self.name} turns away. 'Not interested.'"

    # ── Relationship ──────────────────────────────────────────────────────

    def modify_relationship(self, delta: int) -> None:
        self.relationship = max(-100, min(100, self.relationship + delta))

    def relationship_label(self) -> str:
        r = self.relationship
        if r >= 80:  return "Trusted Ally"
        if r >= 50:  return "Friendly"
        if r >= 20:  return "Neutral"
        if r >= -20: return "Cautious"
        if r >= -50: return "Unfriendly"
        return "Hostile"

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "npc_id":       self.npc_id,
            "relationship": self.relationship,
            "location":     self.location,
            "flags":        self.flags,
        }

    def apply_state(self, state: dict) -> None:
        self.relationship = state.get("relationship", self.relationship)
        self.location     = state.get("location",     self.location)
        self.flags        = state.get("flags",        self.flags)


class NPCManager:
    """Manages all NPCs, their state, and faction relationships."""

    def __init__(self) -> None:
        self.npcs: Dict[str, NPC] = {}
        self._load_npcs()

    def _load_npcs(self) -> None:
        path = os.path.join(DATA_DIR, "npcs.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            data = {}

        for npc_id, ndata in (data or {}).items():
            npc = NPC(
                npc_id=npc_id,
                name=ndata["name"],
                full_name=ndata.get("full_name", ndata["name"]),
                faction=ndata.get("faction", "neutral"),
                location=ndata.get("location", "crew_commons"),
                relationship=ndata.get("relationship", 0),
                description=ndata.get("description", ""),
                dialogue=ndata.get("dialogue", {}),
                knowledge=ndata.get("knowledge", []),
                hidden_info=ndata.get("hidden_info"),
            )
            self.npcs[npc_id] = npc

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        return self.npcs.get(npc_id)

    def find_npc_by_name(self, name: str) -> Optional[NPC]:
        """Find an NPC by partial name match (case-insensitive)."""
        name_lower = name.lower()
        # Try exact match first
        for npc in self.npcs.values():
            if npc.name.lower() == name_lower:
                return npc
        # Try partial match
        for npc in self.npcs.values():
            if name_lower in npc.name.lower() or name_lower in npc.full_name.lower():
                return npc
            # Last-name match
            parts = npc.full_name.lower().split()
            if any(p == name_lower for p in parts):
                return npc
        return None

    def get_npcs_in_room(self, room_id: str) -> List[NPC]:
        """Return all NPCs currently in a given room."""
        return [npc for npc in self.npcs.values() if npc.location == room_id]

    def move_npc(self, npc_id: str, room_id: str) -> None:
        npc = self.npcs.get(npc_id)
        if npc:
            npc.location = room_id

    def get_faction_trust(self, faction: str) -> float:
        """Average relationship score for a given faction."""
        members = [n for n in self.npcs.values() if n.faction == faction]
        if not members:
            return 0.0
        return sum(n.relationship for n in members) / len(members)

    def modify_faction_trust(self, faction: str, delta: int) -> None:
        """Apply a relationship delta to all NPCs in a faction."""
        for npc in self.npcs.values():
            if npc.faction == faction:
                npc.modify_relationship(delta)

    def to_dict(self) -> dict:
        return {npc_id: npc.to_dict() for npc_id, npc in self.npcs.items()}

    def apply_state(self, state: dict) -> None:
        for npc_id, nstate in state.items():
            npc = self.npcs.get(npc_id)
            if npc:
                npc.apply_state(nstate)
