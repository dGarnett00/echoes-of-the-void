"""Ship model: decks, rooms, connections, states."""

from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@dataclass
class RoomObject:
    """An interactable object within a room."""
    obj_id:      str
    name:        str
    description: str
    item_id:     Optional[str] = None   # item granted on examine/use
    requires:    Optional[str] = None   # flag required to interact
    flags:       Dict[str, Any] = field(default_factory=dict)


@dataclass
class Room:
    """A single location on the ship."""
    room_id:     str
    name:        str
    deck:        int
    description: str                         # default description
    descriptions: Dict[str, str] = field(default_factory=dict)  # keyed by state
    exits:       Dict[str, str] = field(default_factory=dict)   # direction -> room_id
    objects:     Dict[str, RoomObject] = field(default_factory=dict)
    npcs:        List[str] = field(default_factory=list)   # NPC IDs present
    locked:      bool = False
    lock_key:    Optional[str] = None    # item_id or flag needed to unlock
    powered:     bool = True
    visited:     bool = False
    flags:       Dict[str, Any] = field(default_factory=dict)

    def get_description(self, sanity_level: str = "high",
                        game_flags: Optional[Dict] = None) -> str:
        """Return the appropriate description based on state/sanity."""
        flags = game_flags or {}

        # Check state-specific descriptions
        for state_key, state_desc in self.descriptions.items():
            if flags.get(state_key, False):
                return state_desc

        # Sanity-degraded descriptions
        if sanity_level in ("low", "critical"):
            return self.descriptions.get("low_sanity", self.description)
        if sanity_level == "medium":
            return self.descriptions.get("medium_sanity", self.description)

        return self.description

    def get_exits_string(self) -> str:
        """Return a human-readable exit list."""
        if not self.exits:
            return "No obvious exits."
        return "Exits: " + ", ".join(
            f"{direction.upper()} → {room_id.replace('_', ' ').title()}"
            for direction, room_id in self.exits.items()
        )


class Ship:
    """The UNS Meridian — room graph and state."""

    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}
        self._load_rooms()

    def _load_rooms(self) -> None:
        path = os.path.join(DATA_DIR, "rooms.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            data = {}

        for room_id, rdata in (data or {}).items():
            objects: Dict[str, RoomObject] = {}
            for obj_data in rdata.get("objects", []):
                obj = RoomObject(
                    obj_id=obj_data["id"],
                    name=obj_data["name"],
                    description=obj_data["description"],
                    item_id=obj_data.get("item_id"),
                    requires=obj_data.get("requires"),
                    flags=obj_data.get("flags", {}),
                )
                objects[obj.obj_id] = obj

            room = Room(
                room_id=room_id,
                name=rdata["name"],
                deck=rdata.get("deck", 0),
                description=rdata["description"],
                descriptions=rdata.get("descriptions", {}),
                exits=rdata.get("exits", {}),
                objects=objects,
                npcs=rdata.get("npcs", []),
                locked=rdata.get("locked", False),
                lock_key=rdata.get("lock_key"),
                powered=rdata.get("powered", True),
                flags=rdata.get("flags", {}),
            )
            self.rooms[room_id] = room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def unlock_room(self, room_id: str) -> bool:
        room = self.rooms.get(room_id)
        if room:
            room.locked = False
            return True
        return False

    def mark_visited(self, room_id: str) -> None:
        room = self.rooms.get(room_id)
        if room:
            room.visited = True

    def set_room_flag(self, room_id: str, flag: str, value: Any = True) -> None:
        room = self.rooms.get(room_id)
        if room:
            room.flags[flag] = value

    def add_npc_to_room(self, npc_id: str, room_id: str) -> None:
        for room in self.rooms.values():
            if npc_id in room.npcs:
                room.npcs.remove(npc_id)
        room = self.rooms.get(room_id)
        if room:
            room.npcs.append(npc_id)

    def get_connected_rooms(self, room_id: str) -> Dict[str, str]:
        """Return exits dict for a room."""
        room = self.rooms.get(room_id)
        if room:
            return dict(room.exits)
        return {}

    def to_dict(self) -> dict:
        """Serialise room state flags and visited status."""
        result = {}
        for room_id, room in self.rooms.items():
            result[room_id] = {
                "visited": room.visited,
                "locked":  room.locked,
                "powered": room.powered,
                "flags":   room.flags,
                "npcs":    room.npcs,
            }
        return result

    def apply_state(self, state: dict) -> None:
        """Restore room states from saved data."""
        for room_id, rstate in state.items():
            room = self.rooms.get(room_id)
            if room:
                room.visited = rstate.get("visited", room.visited)
                room.locked  = rstate.get("locked",  room.locked)
                room.powered = rstate.get("powered", room.powered)
                room.flags   = rstate.get("flags",   room.flags)
                room.npcs    = rstate.get("npcs",    room.npcs)
