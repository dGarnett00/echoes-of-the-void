"""Player state: inventory, sanity, memories, and theory board."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InventoryItem:
    """A single item in the player's inventory."""
    item_id:     str
    name:        str
    description: str
    uses:        int = -1   # -1 = unlimited


@dataclass
class TheoryEntry:
    """A theory note recorded by the player."""
    index:   int
    text:    str
    cycle:   int
    related: List[str] = field(default_factory=list)  # related item/npc IDs


@dataclass
class Memory:
    """A narrative memory unlocked through play."""
    memory_id: str
    title:     str
    text:      str
    cycle:     int


@dataclass
class Player:
    """Complete player state."""

    name:           str  = "Survivor"
    cycle:          int  = 0
    location:       str  = "cryo_bay"      # current room ID
    previous_location: str = ""
    inventory:      Dict[str, InventoryItem] = field(default_factory=dict)
    theory_board:   List[TheoryEntry]        = field(default_factory=list)
    memories:       List[Memory]             = field(default_factory=list)
    known_rooms:    List[str]                = field(default_factory=list)
    known_npcs:     List[str]                = field(default_factory=list)
    flags:          Dict[str, bool]          = field(default_factory=dict)
    evidence:       List[str]                = field(default_factory=list)
    cycles_since_last_rest: int = 0
    cycles_since_last_social: int = 0

    # ── Inventory ─────────────────────────────────────────────────────────

    def add_item(self, item: InventoryItem) -> None:
        """Add an item to inventory."""
        self.inventory[item.item_id] = item

    def remove_item(self, item_id: str) -> Optional[InventoryItem]:
        """Remove and return an item from inventory, or None."""
        return self.inventory.pop(item_id, None)

    def has_item(self, item_id: str) -> bool:
        return item_id in self.inventory

    def use_item(self, item_id: str) -> Optional[InventoryItem]:
        """Use an item — decrements uses; removes if exhausted."""
        item = self.inventory.get(item_id)
        if item is None:
            return None
        if item.uses > 0:
            item.uses -= 1
            if item.uses == 0:
                del self.inventory[item_id]
        return item

    # ── Theory board ──────────────────────────────────────────────────────

    def add_theory(self, text: str, cycle: int, related: Optional[List[str]] = None) -> TheoryEntry:
        entry = TheoryEntry(
            index=len(self.theory_board) + 1,
            text=text,
            cycle=cycle,
            related=related or [],
        )
        self.theory_board.append(entry)
        return entry

    def show_theories(self) -> List[str]:
        """Return formatted theory entries."""
        if not self.theory_board:
            return ["Theory board is empty. Use THEORIZE to record your deductions."]
        lines = []
        for t in self.theory_board:
            lines.append(f"[{t.index}] Cycle {t.cycle}: {t.text}")
        return lines

    # ── Evidence ──────────────────────────────────────────────────────────

    def add_evidence(self, evidence_id: str) -> None:
        if evidence_id not in self.evidence:
            self.evidence.append(evidence_id)

    def has_evidence(self, evidence_id: str) -> bool:
        return evidence_id in self.evidence

    # ── Flags ─────────────────────────────────────────────────────────────

    def set_flag(self, flag: str, value: bool = True) -> None:
        self.flags[flag] = value

    def get_flag(self, flag: str, default: bool = False) -> bool:
        return self.flags.get(flag, default)

    # ── Memories ──────────────────────────────────────────────────────────

    def unlock_memory(self, memory_id: str, title: str, text: str) -> None:
        if not any(m.memory_id == memory_id for m in self.memories):
            self.memories.append(Memory(
                memory_id=memory_id,
                title=title,
                text=text,
                cycle=self.cycle,
            ))

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "cycle":      self.cycle,
            "location":   self.location,
            "previous_location": self.previous_location,
            "inventory":  {
                k: {
                    "item_id":     v.item_id,
                    "name":        v.name,
                    "description": v.description,
                    "uses":        v.uses,
                }
                for k, v in self.inventory.items()
            },
            "theory_board": [
                {"index": t.index, "text": t.text, "cycle": t.cycle,
                 "related": t.related}
                for t in self.theory_board
            ],
            "memories": [
                {"memory_id": m.memory_id, "title": m.title,
                 "text": m.text, "cycle": m.cycle}
                for m in self.memories
            ],
            "known_rooms":    self.known_rooms,
            "known_npcs":     self.known_npcs,
            "flags":          self.flags,
            "evidence":       self.evidence,
            "cycles_since_last_rest":   self.cycles_since_last_rest,
            "cycles_since_last_social": self.cycles_since_last_social,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(
            name=data.get("name", "Survivor"),
            cycle=data.get("cycle", 0),
            location=data.get("location", "cryo_bay"),
            previous_location=data.get("previous_location", ""),
        )
        # Inventory
        for k, v in data.get("inventory", {}).items():
            p.inventory[k] = InventoryItem(
                item_id=v["item_id"],
                name=v["name"],
                description=v["description"],
                uses=v.get("uses", -1),
            )
        # Theory board
        for t in data.get("theory_board", []):
            p.theory_board.append(TheoryEntry(
                index=t["index"], text=t["text"],
                cycle=t["cycle"], related=t.get("related", []),
            ))
        # Memories
        for m in data.get("memories", []):
            p.memories.append(Memory(
                memory_id=m["memory_id"], title=m["title"],
                text=m["text"], cycle=m["cycle"],
            ))
        p.known_rooms    = data.get("known_rooms", [])
        p.known_npcs     = data.get("known_npcs", [])
        p.flags          = data.get("flags", {})
        p.evidence       = data.get("evidence", [])
        p.cycles_since_last_rest   = data.get("cycles_since_last_rest", 0)
        p.cycles_since_last_social = data.get("cycles_since_last_social", 0)
        return p
