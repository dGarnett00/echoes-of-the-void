"""Main game loop for Echoes of the Void."""

from __future__ import annotations
import os
import yaml
from typing import Dict, List, Optional

from .parser import Parser, Command
from .player import Player, InventoryItem
from .resources import Resources, ResourceManager
from .ship import Ship
from .npcs import NPCManager
from .cora import CORA
from .sanity import SanitySystem
from .puzzles import PuzzleManager
from .narrative import NarrativeEngine
from .save_system import SaveSystem
from .utils import (
    Colors, show_title, header, divider, instant_print, slow_print,
    fast_print, typewrite, prompt, press_enter, display_status, display_help,
    resource_bar,
)


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
AUTO_SAVE_EVERY = 5   # cycles


class Game:
    """Top-level game object."""

    def __init__(self) -> None:
        self.parser    = Parser()
        self.player    = Player()
        self.resources = Resources()
        self.res_mgr   = ResourceManager(self.resources)
        self.ship      = Ship()
        self.npc_mgr   = NPCManager()
        self.cora      = CORA()
        self.sanity    = SanitySystem()
        self.puzzles   = PuzzleManager()
        self.narrative = NarrativeEngine()
        self.save_sys  = SaveSystem()
        self.items_data: Dict[str, dict] = self._load_items()
        self._running  = True

    # ── Bootstrap ─────────────────────────────────────────────────────────

    def _load_items(self) -> Dict[str, dict]:
        path = os.path.join(DATA_DIR, "items.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def run(self) -> None:
        """Start and run the game."""
        show_title()
        press_enter()
        self._main_menu()

    def _main_menu(self) -> None:
        """Show the main menu and handle player choice."""
        while True:
            header("MAIN MENU", color=Colors.ROOM)
            instant_print("  1. New Game")
            instant_print("  2. Load Game")
            instant_print("  3. Help")
            instant_print("  4. Quit")
            divider()
            choice = prompt("Choice > ")

            if choice in ("1", "new"):
                self._new_game()
                break
            if choice in ("2", "load"):
                if self._load_menu():
                    break
            elif choice in ("3", "help"):
                display_help()
                press_enter()
            elif choice in ("4", "quit", "q", "exit"):
                instant_print("Goodbye.", color=Colors.DIM)
                return

    def _load_menu(self) -> bool:
        """Show save slot list and offer to load."""
        saves = self.save_sys.list_saves()
        header("LOAD GAME", color=Colors.ROOM)
        for s in saves:
            if s["exists"]:
                instant_print(
                    f"  Slot {s['slot']}: Cycle {s.get('cycle', '?')} "
                    f"— {s.get('location', '?').replace('_', ' ').title()} "
                    f"(saved {s.get('saved_at', '?')[:16]})"
                )
            else:
                instant_print(f"  Slot {s['slot']}: [empty]", color=Colors.DIM)
        divider()
        slot_str = prompt("Load slot (1-3) or BACK > ")
        if slot_str.lower() in ("back", "b", ""):
            return False
        try:
            slot = int(slot_str)
        except ValueError:
            return False
        state, msg = self.save_sys.load(slot)
        if state:
            self._restore_state(state)
            instant_print(msg, color=Colors.CORA)
            self._game_loop()
            return True
        else:
            instant_print(msg, color=Colors.WARNING)
            return False

    def _new_game(self) -> None:
        """Initialise and start a new game."""
        instant_print(
            "\nEnter your name (or press Enter for 'Survivor'): ",
            color=Colors.CORA,
        )
        name = prompt("> ").strip() or "Survivor"
        self.player.name = name

        # Give starting items
        self._give_item("medpatch")

        self._game_loop()

    # ── Main game loop ─────────────────────────────────────────────────────

    def _game_loop(self) -> None:
        """Core game loop."""
        # Sync sanity between systems
        self.sanity.sanity = self.resources.sanity

        # First-time room description
        self._describe_current_room()

        while self._running:
            # Fire pending narrative events
            self._process_events()

            if not self._running:
                break

            # Get player input
            raw = prompt("\n> ")
            result = self.parser.parse(raw)

            if not result.ok:
                instant_print(result.error, color=Colors.WARNING)
                continue

            cmd = result.command
            self._dispatch(cmd)

            # Advance cycle after each command (except status/help/save/load/inventory)
            if cmd.verb not in ("status", "help", "save", "load", "inventory", "quit"):
                self._tick_cycle()

        instant_print(
            "\nThank you for playing Echoes of the Void.",
            color=Colors.CORA,
        )

    def _tick_cycle(self) -> None:
        """Advance one game cycle."""
        self.player.cycle += 1
        self.player.cycles_since_last_rest += 1
        self.player.cycles_since_last_social += 1

        # Apply isolation sanity penalty
        self.sanity.apply_isolation_penalty(self.player.cycles_since_last_social)
        self.resources.sanity = self.sanity.sanity

        # Resource decay
        warnings, events = self.res_mgr.tick()

        # Sync sanity back
        self.sanity.sanity = self.resources.sanity

        # Display warnings
        for w in warnings:
            color = Colors.CRITICAL if w.level == "critical" else Colors.WARNING
            instant_print(f"\n  {w.message}", color=color)

        # Handle resource events
        for event_key in events:
            self._handle_resource_event(event_key)

        # Auto-save
        if self.player.cycle % AUTO_SAVE_EVERY == 0:
            ok, msg = self.save_sys.save(self._build_state(), slot=1)
            if ok:
                instant_print(f"\n  [Auto-saved — Cycle {self.player.cycle}]",
                               color=Colors.DIM)

        # Show cycle indicator
        fast_print(f"\n  — Cycle {self.player.cycle} —", color=Colors.DIM)

    def _handle_resource_event(self, event_key: str) -> None:
        if event_key == "critical_o2":
            instant_print(
                "  CRITICAL: The air is thin. Every breath takes effort.",
                color=Colors.CRITICAL,
            )
        elif event_key == "critical_power":
            instant_print(
                "  CRITICAL: Emergency lighting activates. Darkness encroaches.",
                color=Colors.CRITICAL,
            )
        elif event_key == "rations_depleted":
            instant_print(
                "  The last ration pack is gone. Trust is eroding.",
                color=Colors.WARNING,
            )

    # ── Event processing ───────────────────────────────────────────────────

    def _process_events(self) -> None:
        """Check for and fire narrative events."""
        pending = self.narrative.get_pending_events(
            self.player.cycle, self.player.flags
        )
        for event in pending:
            event_id = event.get("id", "")
            self.narrative.fire_event(event_id, self.player.flags)
            self._display_event(event)

            # Special handling for act completion
            if event.get("type") == "ending":
                self._save_act_end()
                self._running = False
                return

    def _display_event(self, event: dict) -> None:
        etype = event.get("type", "story")
        title = event.get("title", "")
        text  = event.get("text", "")

        print()
        if etype == "crisis":
            header(title, color=Colors.CRITICAL)
            slow_print(text, color=Colors.WARNING)
        elif etype == "revelation":
            header(title, color=Colors.RESONANCE)
            slow_print(text, color=Colors.RESONANCE)
        elif etype == "ending":
            header(title, color=Colors.RESONANCE)
            slow_print(text, color=Colors.CORA)
        else:
            header(title, color=Colors.ROOM)
            slow_print(text)

        if etype == "decision":
            instant_print(
                "\n  [This situation requires your action. Explore and interact to proceed.]",
                color=Colors.CORA,
            )
        else:
            press_enter()

    # ── Command dispatch ───────────────────────────────────────────────────

    def _dispatch(self, cmd: Command) -> None:
        """Route a parsed command to the right handler."""
        verb = cmd.verb
        dispatch_table = {
            "examine":   self._cmd_examine,
            "move":      self._cmd_move,
            "talk":      self._cmd_talk,
            "query":     self._cmd_query,
            "allocate":  self._cmd_allocate,
            "use":       self._cmd_use,
            "repair":    self._cmd_repair,
            "theorize":  self._cmd_theorize,
            "rest":      self._cmd_rest,
            "confront":  self._cmd_confront,
            "inventory": self._cmd_inventory,
            "status":    self._cmd_status,
            "help":      self._cmd_help,
            "save":      self._cmd_save,
            "load":      self._cmd_load,
            "quit":      self._cmd_quit,
        }
        handler = dispatch_table.get(verb)
        if handler:
            handler(cmd)
        else:
            instant_print(f"Command '{verb}' not implemented.", color=Colors.WARNING)

    # ── Command handlers ───────────────────────────────────────────────────

    def _cmd_examine(self, cmd: Command) -> None:
        target = cmd.full_args.lower()
        room = self.ship.get_room(self.player.location)
        if not room:
            instant_print("You're nowhere. This shouldn't happen.", color=Colors.WARNING)
            return

        # No target → describe room
        if not target:
            self._describe_current_room()
            return

        # Check room objects
        for obj_id, obj in room.objects.items():
            if target in obj.name.lower() or target in obj_id.lower():
                text = self.sanity.inject(obj.description)
                slow_print(text)
                # Give item if attached and not already have
                if obj.item_id and not self.player.has_item(obj.item_id):
                    self._give_item(obj.item_id)
                return

        # Check NPCs in room
        npc = self._find_npc_in_room(target, room.room_id)
        if npc:
            slow_print(self.sanity.inject(npc.description))
            return

        # Generic fallback
        instant_print(
            f"You don't see '{target}' here.",
            color=Colors.DIM,
        )

    def _cmd_move(self, cmd: Command) -> None:
        target = cmd.noun.lower()
        room   = self.ship.get_room(self.player.location)
        if not room:
            return

        # Try direction
        dest_id = room.exits.get(target)

        # Try room name / ID substring
        if not dest_id:
            for direction, rid in room.exits.items():
                if target in rid.lower() or target in direction.lower():
                    dest_id = rid
                    break

        if not dest_id:
            instant_print(
                f"You can't go '{target}' from here. {room.get_exits_string()}",
                color=Colors.WARNING,
            )
            return

        dest = self.ship.get_room(dest_id)
        if not dest:
            instant_print("That path leads nowhere.", color=Colors.WARNING)
            return

        if dest.locked:
            instant_print(
                f"The way to {dest.name} is sealed. "
                f"[Requires: {dest.lock_key or 'unknown'}]",
                color=Colors.WARNING,
            )
            return

        # Move
        self.player.previous_location = self.player.location
        self.player.location = dest_id
        self.ship.mark_visited(dest_id)

        if dest_id not in self.player.known_rooms:
            self.player.known_rooms.append(dest_id)

        # Resonance exposure on lower decks
        if dest.deck <= 6:
            self.cora.increase_corruption(2.0)
            self.sanity.apply_resonance_exposure(intensity=2.0)
            self.resources.sanity = self.sanity.sanity

        self._describe_current_room()

    def _cmd_talk(self, cmd: Command) -> None:
        target = cmd.full_args

        if not target:
            # List NPCs in room
            room = self.ship.get_room(self.player.location)
            if room:
                npcs = self.npc_mgr.get_npcs_in_room(room.room_id)
                if npcs:
                    names = ", ".join(n.name for n in npcs)
                    instant_print(f"  Present: {names}", color=Colors.NPC)
                else:
                    instant_print("  No one here to talk to.", color=Colors.DIM)
            return

        npc = self.npc_mgr.find_npc_by_name(target)
        if not npc:
            instant_print(
                f"You don't know anyone named '{target}'.",
                color=Colors.WARNING,
            )
            return

        # Check they're in the room or nearby
        room = self.ship.get_room(self.player.location)
        if room and npc.npc_id not in room.npcs:
            instant_print(
                f"{npc.name} isn't here right now.",
                color=Colors.DIM,
            )
            return

        # Determine topic from modifier
        topic = cmd.modifier.lower() if cmd.modifier else "default"
        dialogue = npc.get_dialogue(topic=topic, game_flags=self.player.flags)
        dialogue = self.sanity.inject(dialogue)

        print()
        instant_print(f"  {npc.name}:", color=Colors.NPC)
        slow_print(f'  "{dialogue}"')

        # Relationship and sanity effects
        if npc.relationship >= 0:
            npc.modify_relationship(2)
            self.sanity.apply_npc_interaction_bonus()
            self.resources.sanity = self.sanity.sanity

        self.player.cycles_since_last_social = 0
        if npc.npc_id not in self.player.known_npcs:
            self.player.known_npcs.append(npc.npc_id)

    def _cmd_query(self, cmd: Command) -> None:
        question = cmd.quoted or cmd.full_args
        if not question:
            instant_print(
                'Usage: QUERY CORA "your question"',
                color=Colors.WARNING,
            )
            return

        res_dict = {
            "o2": self.resources.o2,
            "power": self.resources.power,
        }
        response, was_corrupted = self.cora.query(question, resources=res_dict)
        response = self.sanity.inject(response)

        print()
        instant_print("  CORA:", color=Colors.CORA)
        slow_print(f'  "{response}"', color=Colors.CORA)

        if was_corrupted and self.sanity.level in ("high", "medium"):
            # Subtle hint that something might be off
            if self.cora.times_caught == 0:
                fast_print(
                    "\n  [Something in CORA's tone feels slightly off — "
                    "but you can't pinpoint it.]",
                    color=Colors.DIM,
                )

    def _cmd_allocate(self, cmd: Command) -> None:
        args = cmd.args
        # Usage: ALLOCATE life_support 40
        if len(args) < 2:
            # Show current allocation
            instant_print("\n  Current Power Allocation:", color=Colors.CORA)
            for sub, pct in self.resources.power_allocation.items():
                instant_print(f"    {sub.replace('_', ' '):<16} {pct:5.1f}%")
            total = sum(self.resources.power_allocation.values())
            instant_print(f"    {'TOTAL':<16} {total:5.1f}%")
            instant_print(
                "\n  Usage: ALLOCATE <subsystem> <percent>",
                color=Colors.DIM,
            )
            return

        subsystem = args[0]
        try:
            amount = float(args[1])
        except ValueError:
            instant_print("Amount must be a number.", color=Colors.WARNING)
            return

        ok, msg = self.res_mgr.allocate(subsystem, amount)
        color = Colors.CORA if ok else Colors.WARNING
        instant_print(f"  {msg}", color=color)

    def _cmd_use(self, cmd: Command) -> None:
        item_id = cmd.noun.lower().replace(" ", "_")

        # Find in inventory (partial match)
        matched_id = None
        for iid in self.player.inventory:
            if item_id in iid or item_id in self.player.inventory[iid].name.lower():
                matched_id = iid
                break

        if not matched_id:
            instant_print(
                f"You don't have '{cmd.noun}' in your inventory.",
                color=Colors.WARNING,
            )
            return

        item = self.player.use_item(matched_id)
        if not item:
            instant_print("Item couldn't be used.", color=Colors.WARNING)
            return

        # Apply effects
        effects = self.items_data.get(item.item_id, {}).get("effects", {})
        self._apply_item_effects(item, effects)
        instant_print(f"  Used: {item.name}", color=Colors.CORA)

        # Item-specific narrative
        if matched_id == "medpatch":
            slow_print("  The patch activates. A warmth spreads through your arm.")
        elif matched_id == "synaptix_dose":
            slow_print("  The dose hits quickly — a steadying clarity returns.")
        elif matched_id == "oxygen_canister":
            slow_print("  Fresh O₂ vents into the local atmosphere. Easier to breathe.")
        elif matched_id == "ration_pack":
            slow_print("  Compressed nutrition. Barely food. Better than nothing.")

    def _apply_item_effects(self, item: InventoryItem, effects: dict) -> None:
        if "sanity" in effects:
            self.res_mgr.modify("sanity", float(effects["sanity"]))
            self.sanity.sanity = self.resources.sanity
        if "o2" in effects:
            self.res_mgr.modify("o2", float(effects["o2"]))
        if "rations" in effects:
            self.res_mgr.modify("rations", float(effects["rations"]))
        if "evidence" in effects:
            self.player.add_evidence(str(effects["evidence"]))
            instant_print(
                f"  [Evidence recorded: {effects['evidence']}]",
                color=Colors.WARNING,
            )

    def _cmd_repair(self, cmd: Command) -> None:
        target = cmd.full_args.lower()
        room   = self.ship.get_room(self.player.location)

        if not target:
            instant_print("Repair what? Specify a target.", color=Colors.WARNING)
            return

        # Atmospheric processor puzzle
        if ("atmos" in target or "processor" in target) and room and room.deck == 5:
            instant_print(
                "\n  The atmospheric processor has three subsystems.\n"
                "  Each can be set to ACTIVE, STANDBY, or OFFLINE.\n"
                "  Specify: REPAIR processor <filters> <compressors> <regulators>",
                color=Colors.CORA,
            )
            args = cmd.args
            if len(args) >= 4:
                f, c, r = args[1], args[2], args[3]
                ok, msg = self.puzzles.attempt_atmospheric_processor(f, c, r)
                color = Colors.CORA if ok else Colors.WARNING
                slow_print(f"\n  {msg}", color=color)
                if ok:
                    self.res_mgr.modify("o2", 10.0)
                    self.sanity.apply_puzzle_solved()
                    self.resources.sanity = self.sanity.sanity
                    self.player.set_flag("atmospheric_processor_repaired")
            return

        # Reactor coolant repair
        if "coolant" in target or "reactor" in target:
            if not self.player.has_item("hydrospanner"):
                instant_print(
                    "  You need a hydrospanner for this repair.",
                    color=Colors.WARNING,
                )
                return
            if self.puzzles.is_solved("reactor_diagnostic"):
                slow_print(
                    "  You work on the coolant loop with the hydrospanner. "
                    "Pressure climbs from 1.4 MPa toward 2.4 MPa — a partial repair. "
                    "It's not perfect, but it's something.",
                )
                self.res_mgr.modify("power", 8.0)
                self.player.set_flag("coolant_partially_repaired")
            else:
                instant_print(
                    "  Run reactor diagnostics first to identify the correct "
                    "system to repair.",
                    color=Colors.WARNING,
                )
            return

        instant_print(
            f"  You can't see how to repair '{target}' right now.",
            color=Colors.DIM,
        )

    def _cmd_theorize(self, cmd: Command) -> None:
        if not cmd.args:
            # Display theory board
            lines = self.player.show_theories()
            header("THEORY BOARD", color=Colors.RESONANCE)
            for line in lines:
                instant_print(f"  {line}")
            divider()
            return

        theory_text = " ".join(cmd.args)
        entry = self.player.add_theory(theory_text, self.player.cycle)
        instant_print(
            f"  Theory #{entry.index} recorded: \"{theory_text}\"",
            color=Colors.RESONANCE,
        )

    def _cmd_rest(self, cmd: Command) -> None:
        slow_print(
            "  You find a quiet corner and rest. The ship's sounds "
            "fade to a background hum. When you wake, your head is "
            "clearer."
        )
        self.sanity.apply_rest_bonus()
        self.resources.sanity = self.sanity.sanity
        self.player.cycles_since_last_rest = 0
        # Rest takes a cycle
        self._tick_cycle()

    def _cmd_confront(self, cmd: Command) -> None:
        target = cmd.full_args
        if not target:
            instant_print("Confront whom?", color=Colors.WARNING)
            return

        npc = self.npc_mgr.find_npc_by_name(target)
        if not npc:
            instant_print(f"You don't know '{target}'.", color=Colors.WARNING)
            return

        ok, msg = self.puzzles.confront_suspect(
            npc.npc_id,
            evidence=self.player.evidence,
        )

        color = Colors.CORA if ok else Colors.WARNING
        slow_print(f"\n  {msg}", color=color)

        if ok:
            self.res_mgr.modify("trust", 15.0)
            self.player.set_flag("saboteur_confronted")
            npc.modify_relationship(-20)

    def _cmd_inventory(self, cmd: Command) -> None:
        header("INVENTORY", color=Colors.ROOM)
        if not self.player.inventory:
            instant_print("  [empty]", color=Colors.DIM)
        else:
            for item_id, item in self.player.inventory.items():
                uses_str = "" if item.uses == -1 else f" (×{item.uses})"
                instant_print(f"  • {item.name}{uses_str}")
                instant_print(f"    {item.description[:80]}...", color=Colors.DIM)
        divider()
        # Also show evidence
        if self.player.evidence:
            header("EVIDENCE", color=Colors.WARNING)
            for ev in self.player.evidence:
                instant_print(f"  ★ {ev.replace('_', ' ').title()}")
            divider()

    def _cmd_status(self, cmd: Command) -> None:
        room = self.ship.get_room(self.player.location)
        loc_name = room.name if room else self.player.location
        display_status(self.resources.as_dict(), self.player.cycle, loc_name)

        # Show faction relationships if any NPCs known
        if self.player.known_npcs:
            instant_print("\n  Faction Trust:", color=Colors.NPC)
            for faction in ("navigators", "keepers", "listeners", "ghosts"):
                trust = self.npc_mgr.get_faction_trust(faction)
                bar = resource_bar(faction.title(), trust)
                instant_print(f"  {bar}")

    def _cmd_help(self, cmd: Command) -> None:
        display_help()

    def _cmd_save(self, cmd: Command) -> None:
        slot = 1
        if cmd.args:
            try:
                slot = int(cmd.args[0])
            except ValueError:
                pass
        ok, msg = self.save_sys.save(self._build_state(), slot=slot)
        color = Colors.CORA if ok else Colors.WARNING
        instant_print(f"  {msg}", color=color)

    def _cmd_load(self, cmd: Command) -> None:
        slot = 1
        if cmd.args:
            try:
                slot = int(cmd.args[0])
            except ValueError:
                pass
        state, msg = self.save_sys.load(slot)
        if state:
            self._restore_state(state)
            instant_print(f"  {msg}", color=Colors.CORA)
            self._describe_current_room()
        else:
            instant_print(f"  {msg}", color=Colors.WARNING)

    def _cmd_quit(self, cmd: Command) -> None:
        slow_print(
            "\n  The void is patient. The Meridian drifts. "
            "Your story is unfinished."
        )
        self._running = False

    # ── Room description ───────────────────────────────────────────────────

    def _describe_current_room(self) -> None:
        room = self.ship.get_room(self.player.location)
        if not room:
            instant_print("ERROR: Invalid location.", color=Colors.CRITICAL)
            return

        # Header
        header(room.name, color=Colors.ROOM)

        # Description with sanity injection
        desc = room.get_description(
            sanity_level=self.sanity.level,
            game_flags=self.player.flags,
        )
        desc = self.sanity.inject(desc)
        slow_print(desc)

        # NPCs present
        npcs = self.npc_mgr.get_npcs_in_room(room.room_id)
        if npcs:
            names = ", ".join(
                f"{Colors.NPC}{n.name}{Colors.RESET}" for n in npcs
            )
            instant_print(f"\n  Present: {names}")

        # Objects
        if room.objects:
            obj_names = ", ".join(o.name for o in room.objects.values())
            instant_print(f"\n  You notice: {obj_names}", color=Colors.DIM)

        # Exits
        exits = room.exits
        if self.sanity.level in ("low", "critical"):
            exits_keys = self.sanity.distort_exits(list(exits.keys()))
            exits_display = {k: exits.get(k, "?") for k in exits_keys}
        else:
            exits_display = exits

        if exits_display:
            exit_str = ", ".join(
                f"{Colors.CORA}{d.upper()}{Colors.RESET}"
                for d in exits_display
            )
            instant_print(f"\n  Exits: {exit_str}")
        else:
            instant_print("\n  No obvious exits.", color=Colors.DIM)

        divider()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _find_npc_in_room(self, name: str, room_id: str) -> Optional[object]:
        npcs = self.npc_mgr.get_npcs_in_room(room_id)
        name_lower = name.lower()
        for npc in npcs:
            if name_lower in npc.name.lower() or name_lower in npc.full_name.lower():
                return npc
        return None

    def _give_item(self, item_id: str) -> None:
        """Grant an item to the player from the items data."""
        idata = self.items_data.get(item_id)
        if not idata:
            return
        if self.player.has_item(item_id):
            return
        item = InventoryItem(
            item_id=item_id,
            name=idata["name"],
            description=idata["description"],
            uses=idata.get("uses", -1),
        )
        self.player.add_item(item)
        instant_print(
            f"\n  [Obtained: {item.name}]",
            color=Colors.CORA,
        )

    def _save_act_end(self) -> None:
        """Auto-save at Act I end."""
        ok, msg = self.save_sys.save(self._build_state(), slot=1)
        instant_print(f"\n  {msg}", color=Colors.CORA)

    # ── State serialisation ────────────────────────────────────────────────

    def _build_state(self) -> dict:
        return {
            "player":    self.player.to_dict(),
            "resources": self.resources.to_dict(),
            "ship":      self.ship.to_dict(),
            "npcs":      self.npc_mgr.to_dict(),
            "cora":      self.cora.to_dict(),
            "sanity":    self.sanity.to_dict(),
            "puzzles":   self.puzzles.to_dict(),
            "narrative": self.narrative.to_dict(),
        }

    def _restore_state(self, state: dict) -> None:
        """Restore all systems from saved state."""
        self.player    = Player.from_dict(state.get("player", {}))
        self.resources = Resources.from_dict(state.get("resources", {}))
        self.res_mgr   = ResourceManager(self.resources)
        self.ship.apply_state(state.get("ship", {}))
        self.npc_mgr.apply_state(state.get("npcs", {}))
        self.cora      = CORA.from_dict(state.get("cora", {}))
        self.sanity    = SanitySystem.from_dict(state.get("sanity", {}))
        self.puzzles.apply_state(state.get("puzzles", {}))
        self.narrative.apply_state(state.get("narrative", {}))
