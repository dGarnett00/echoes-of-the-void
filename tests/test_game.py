"""Integration smoke tests for the game systems."""

import pytest
from unittest.mock import patch, MagicMock
import io


class TestGameImport:
    def test_game_module_importable(self):
        from src.game import Game
        assert Game is not None

    def test_game_instantiation(self):
        from src.game import Game
        game = Game()
        assert game is not None
        assert game.player is not None
        assert game.resources is not None
        assert game.ship is not None
        assert game.npc_mgr is not None
        assert game.cora is not None
        assert game.sanity is not None
        assert game.puzzles is not None
        assert game.narrative is not None


class TestShipModel:
    def test_ship_loads_rooms(self):
        from src.ship import Ship
        ship = Ship()
        assert len(ship.rooms) > 0

    def test_starting_room_exists(self):
        from src.ship import Ship
        ship = Ship()
        cryo = ship.get_room("cryo_bay")
        assert cryo is not None
        assert cryo.deck == 10

    def test_room_has_exits(self):
        from src.ship import Ship
        ship = Ship()
        cryo = ship.get_room("cryo_bay")
        assert len(cryo.exits) > 0

    def test_room_navigation(self):
        from src.ship import Ship
        ship = Ship()
        cryo = ship.get_room("cryo_bay")
        # cryo_bay should connect to cryo_corridor going north
        assert "north" in cryo.exits

    def test_locked_room_stays_locked(self):
        from src.ship import Ship
        ship = Ship()
        reactor = ship.get_room("reactor_level")
        assert reactor is not None
        assert reactor.locked is True

    def test_unlock_room(self):
        from src.ship import Ship
        ship = Ship()
        ship.unlock_room("reactor_level")
        reactor = ship.get_room("reactor_level")
        assert reactor.locked is False

    def test_mark_visited(self):
        from src.ship import Ship
        ship = Ship()
        ship.mark_visited("cryo_bay")
        cryo = ship.get_room("cryo_bay")
        assert cryo.visited is True

    def test_room_description(self):
        from src.ship import Ship
        ship = Ship()
        cryo = ship.get_room("cryo_bay")
        desc = cryo.get_description()
        assert len(desc) > 10

    def test_ship_serialization(self):
        from src.ship import Ship
        ship = Ship()
        ship.mark_visited("cryo_bay")
        state = ship.to_dict()
        assert "cryo_bay" in state
        assert state["cryo_bay"]["visited"] is True


class TestNPCSystem:
    def test_npc_manager_loads(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        assert len(mgr.npcs) > 0

    def test_vasquez_exists(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        assert vasquez is not None
        assert vasquez.faction == "neutral"

    def test_find_npc_by_name(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        npc = mgr.find_npc_by_name("vasquez")
        assert npc is not None

    def test_find_npc_partial_name(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        npc = mgr.find_npc_by_name("tanaka")
        assert npc is not None

    def test_npc_dialogue_default(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        dialogue = vasquez.get_dialogue()
        assert len(dialogue) > 0

    def test_npc_hostile_dialogue_at_low_trust(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        vasquez.relationship = -30
        dialogue = vasquez.get_dialogue()
        assert dialogue is not None

    def test_npc_relationship_modify(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        initial = vasquez.relationship
        vasquez.modify_relationship(10)
        assert vasquez.relationship == initial + 10

    def test_npc_relationship_capped_at_100(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        vasquez.relationship = 95
        vasquez.modify_relationship(20)
        assert vasquez.relationship == 100

    def test_npc_relationship_floored_at_minus_100(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        vasquez.relationship = -95
        vasquez.modify_relationship(-20)
        assert vasquez.relationship == -100

    def test_get_npcs_in_room(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        # razor is in cargo_main per the YAML
        npcs = mgr.get_npcs_in_room("cargo_main")
        assert any(n.npc_id == "razor" for n in npcs)

    def test_faction_trust_calculation(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        trust = mgr.get_faction_trust("navigators")
        assert isinstance(trust, float)

    def test_npc_serialization(self):
        from src.npcs import NPCManager
        mgr = NPCManager()
        vasquez = mgr.get_npc("vasquez")
        vasquez.relationship = 42
        state = mgr.to_dict()
        assert "vasquez" in state
        assert state["vasquez"]["relationship"] == 42


class TestCORA:
    def test_cora_instantiation(self):
        from src.cora import CORA
        cora = CORA()
        assert cora.corruption == pytest.approx(15.0)

    def test_query_returns_string(self):
        from src.cora import CORA
        cora = CORA(corruption=0.0)  # No corruption for predictable test
        response, was_corrupted = cora.query("reactor status")
        assert isinstance(response, str)
        assert len(response) > 0
        assert was_corrupted is False

    def test_query_reactor_topic(self):
        from src.cora import CORA
        cora = CORA(corruption=0.0)
        response, _ = cora.query("what is the reactor status?")
        assert "reactor" in response.lower() or "output" in response.lower()

    def test_query_ftl_topic(self):
        from src.cora import CORA
        cora = CORA(corruption=0.0)
        response, _ = cora.query("tell me about the FTL drive failure")
        assert len(response) > 0

    def test_corruption_increases(self):
        from src.cora import CORA
        cora = CORA(corruption=10.0)
        cora.increase_corruption(10.0)
        assert cora.corruption == pytest.approx(20.0)

    def test_corruption_capped_at_100(self):
        from src.cora import CORA
        cora = CORA(corruption=95.0)
        cora.increase_corruption(20.0)
        assert cora.corruption == pytest.approx(100.0)

    def test_corruption_floored_at_0(self):
        from src.cora import CORA
        cora = CORA(corruption=5.0)
        cora.corruption = -10.0
        assert cora.corruption == pytest.approx(0.0)

    def test_high_corruption_can_corrupt(self):
        from src.cora import CORA
        cora = CORA(corruption=100.0)
        # With 100% corruption, every query should be corrupted
        corrupted_count = 0
        for _ in range(10):
            _, was_corrupted = cora.query("reactor")
            if was_corrupted:
                corrupted_count += 1
        assert corrupted_count == 10

    def test_zero_corruption_never_corrupts(self):
        from src.cora import CORA
        cora = CORA(corruption=0.0)
        for _ in range(10):
            _, was_corrupted = cora.query("reactor")
            assert was_corrupted is False

    def test_run_diagnostic(self):
        from src.cora import CORA
        cora = CORA()
        result, revealed = cora.run_diagnostic("reactor confinement")
        assert "coolant" in result.lower() or "diagnostic" in result.lower()

    def test_serialization(self):
        from src.cora import CORA
        cora = CORA(corruption=42.0)
        cora.record_caught_corruption("reactor")
        d = cora.to_dict()
        restored = CORA.from_dict(d)
        assert restored.corruption == pytest.approx(42.0)
        assert restored.times_caught == 1


class TestSanitySystem:
    def test_default_sanity(self):
        from src.sanity import SanitySystem
        s = SanitySystem()
        assert s.sanity == pytest.approx(90.0)

    def test_level_high(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=90.0)
        assert s.level == "high"

    def test_level_medium(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=60.0)
        assert s.level == "medium"

    def test_level_low(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=25.0)
        assert s.level == "low"

    def test_level_critical(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=5.0)
        assert s.level == "critical"

    def test_rest_bonus(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=50.0)
        s.apply_rest_bonus()
        assert s.sanity > 50.0

    def test_sanity_capped_at_100(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=98.0)
        s.apply_rest_bonus()
        assert s.sanity <= 100.0

    def test_sanity_floored_at_0(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=2.0)
        s.apply_resonance_exposure(10.0)
        assert s.sanity >= 0.0

    def test_inject_high_sanity_no_change(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=95.0)
        text = "The cryo-bay is cold and quiet."
        result = s.inject(text)
        assert result == text

    def test_resonance_message_at_critical(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=5.0)
        msg = s.get_resonance_message()
        assert msg is not None
        assert len(msg) > 0

    def test_no_resonance_message_at_high(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=90.0)
        msg = s.get_resonance_message()
        assert msg is None

    def test_serialization(self):
        from src.sanity import SanitySystem
        s = SanitySystem(starting_sanity=65.0)
        d = s.to_dict()
        restored = SanitySystem.from_dict(d)
        assert restored.sanity == pytest.approx(65.0)


class TestPlayerState:
    def test_player_instantiation(self):
        from src.player import Player
        p = Player()
        assert p.location == "cryo_bay"
        assert p.cycle == 0

    def test_add_item(self):
        from src.player import Player, InventoryItem
        p = Player()
        item = InventoryItem("medpatch", "Medpatch", "A medical patch.", uses=1)
        p.add_item(item)
        assert p.has_item("medpatch")

    def test_remove_item(self):
        from src.player import Player, InventoryItem
        p = Player()
        item = InventoryItem("medpatch", "Medpatch", "A medical patch.", uses=1)
        p.add_item(item)
        removed = p.remove_item("medpatch")
        assert removed is not None
        assert not p.has_item("medpatch")

    def test_use_item_decrements_uses(self):
        from src.player import Player, InventoryItem
        p = Player()
        item = InventoryItem("medpatch", "Medpatch", "A patch.", uses=2)
        p.add_item(item)
        p.use_item("medpatch")
        assert p.inventory["medpatch"].uses == 1

    def test_use_item_removes_when_exhausted(self):
        from src.player import Player, InventoryItem
        p = Player()
        item = InventoryItem("medpatch", "Medpatch", "A patch.", uses=1)
        p.add_item(item)
        p.use_item("medpatch")
        assert not p.has_item("medpatch")

    def test_unlimited_item_not_removed(self):
        from src.player import Player, InventoryItem
        p = Player()
        item = InventoryItem("hydrospanner", "Hydrospanner", "A tool.", uses=-1)
        p.add_item(item)
        p.use_item("hydrospanner")
        assert p.has_item("hydrospanner")

    def test_add_theory(self):
        from src.player import Player
        p = Player()
        entry = p.add_theory("The FTL failure was deliberate.", cycle=5)
        assert entry.index == 1
        assert "deliberate" in entry.text

    def test_multiple_theories(self):
        from src.player import Player
        p = Player()
        p.add_theory("Theory 1", cycle=1)
        p.add_theory("Theory 2", cycle=2)
        assert len(p.theory_board) == 2
        assert p.theory_board[1].index == 2

    def test_add_evidence(self):
        from src.player import Player
        p = Player()
        p.add_evidence("timestamp_discrepancy")
        assert p.has_evidence("timestamp_discrepancy")

    def test_evidence_not_duplicated(self):
        from src.player import Player
        p = Player()
        p.add_evidence("some_clue")
        p.add_evidence("some_clue")
        assert p.evidence.count("some_clue") == 1

    def test_flags(self):
        from src.player import Player
        p = Player()
        p.set_flag("met_cora")
        assert p.get_flag("met_cora") is True
        assert p.get_flag("nonexistent") is False

    def test_serialization_roundtrip(self):
        from src.player import Player, InventoryItem
        p = Player(name="Test", cycle=5, location="cargo_hold")
        item = InventoryItem("hydrospanner", "Hydrospanner", "Tool.", uses=-1)
        p.add_item(item)
        p.add_theory("Test theory", cycle=5)
        p.add_evidence("some_evidence")
        p.set_flag("met_vasquez")

        d = p.to_dict()
        restored = Player.from_dict(d)

        assert restored.name == "Test"
        assert restored.cycle == 5
        assert restored.location == "cargo_hold"
        assert restored.has_item("hydrospanner")
        assert len(restored.theory_board) == 1
        assert restored.has_evidence("some_evidence")
        assert restored.get_flag("met_vasquez") is True


class TestPuzzleSystem:
    def test_puzzle_manager_loads(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        assert len(mgr.puzzles) > 0

    def test_atmospheric_processor_correct_solution(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.attempt_atmospheric_processor("ACTIVE", "STANDBY", "ACTIVE")
        assert ok is True
        assert "life" in msg.lower() or "hum" in msg.lower() or "processor" in msg.lower()

    def test_atmospheric_processor_wrong_solution(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.attempt_atmospheric_processor("OFFLINE", "OFFLINE", "OFFLINE")
        assert ok is False

    def test_atmospheric_processor_cora_wrong(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        # CORA's wrong suggestion: filters ACTIVE, compressors ACTIVE, regulators STANDBY
        ok, msg = mgr.attempt_atmospheric_processor("ACTIVE", "ACTIVE", "STANDBY")
        assert ok is False
        assert "wrong" in msg.lower() or "overload" in msg.lower() or "surge" in msg.lower()

    def test_puzzle_is_solved_after_correct(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        mgr.attempt_atmospheric_processor("ACTIVE", "STANDBY", "ACTIVE")
        assert mgr.is_solved("atmospheric_processor")

    def test_reactor_test_a(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, result, test_data = mgr.run_reactor_test("a")
        assert ok is True
        assert "confinement" in result.lower() or "field" in result.lower()

    def test_reactor_test_invalid(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, result, _ = mgr.run_reactor_test("z")
        assert ok is False

    def test_reactor_correct_answer(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.conclude_reactor_diagnosis("C")
        assert ok is True
        assert "coolant" in msg.lower()

    def test_reactor_wrong_answer(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.conclude_reactor_diagnosis("A")
        assert ok is False

    def test_confront_suspect_insufficient_evidence(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.confront_suspect("venn", evidence=[])
        assert ok is False
        assert "evidence" in msg.lower()

    def test_confront_wrong_suspect(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        ok, msg = mgr.confront_suspect("vasquez", evidence=["listener_tool_marks", "venn_motive_confirmed"])
        assert ok is False

    def test_confront_correct_suspect_with_evidence(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        evidence = ["listener_tool_marks", "venn_motive_confirmed", "listener_proximity"]
        ok, msg = mgr.confront_suspect("venn", evidence=evidence)
        assert ok is True

    def test_puzzle_serialization(self):
        from src.puzzles import PuzzleManager
        mgr = PuzzleManager()
        mgr.attempt_atmospheric_processor("ACTIVE", "STANDBY", "ACTIVE")
        state = mgr.to_dict()
        assert "atmospheric_processor" in state
        assert state["atmospheric_processor"]["solved"] is True


class TestNarrativeEngine:
    def test_narrative_loads_events(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        assert len(eng.events) > 0

    def test_awakening_event_fires_at_cycle_1(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        pending = eng.get_pending_events(cycle=1, flags={})
        ids = [e.get("id") for e in pending]
        assert "awakening_intro" in ids

    def test_event_requires_flag(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        # cora_introduction requires awakening_complete flag
        pending = eng.get_pending_events(cycle=2, flags={})
        ids = [e.get("id") for e in pending]
        assert "cora_introduction" not in ids

    def test_event_fires_with_flag(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        pending = eng.get_pending_events(
            cycle=2, flags={"awakening_complete": True}
        )
        ids = [e.get("id") for e in pending]
        assert "cora_introduction" in ids

    def test_fired_events_not_repeated(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        flags = {}
        eng.fire_event("awakening_intro", flags)
        pending = eng.get_pending_events(cycle=1, flags=flags)
        ids = [e.get("id") for e in pending]
        assert "awakening_intro" not in ids

    def test_fire_event_sets_flags(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        flags = {}
        eng.fire_event("awakening_intro", flags)
        assert flags.get("awakening_complete") is True

    def test_act_not_complete_initially(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        assert eng.is_act_complete({}) is False

    def test_act_complete_with_flag(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        assert eng.is_act_complete({"act_1_complete": True}) is True

    def test_narrative_serialization(self):
        from src.narrative import NarrativeEngine
        eng = NarrativeEngine()
        eng.fired.add("awakening_intro")
        state = eng.to_dict()
        restored = NarrativeEngine()
        restored.apply_state(state)
        assert "awakening_intro" in restored.fired


class TestSaveSystem:
    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        from src.save_system import SaveSystem, SAVE_DIR
        # Redirect save directory to tmp
        monkeypatch.setattr("src.save_system.SAVE_DIR", str(tmp_path))

        ss = SaveSystem()
        state = {"player": {"name": "TestPlayer", "cycle": 7}}
        ok, msg = ss.save(state, slot=1)
        assert ok is True

        loaded, msg = ss.load(slot=1)
        assert loaded is not None
        assert loaded["player"]["name"] == "TestPlayer"
        assert loaded["player"]["cycle"] == 7

    def test_load_nonexistent_slot(self, tmp_path, monkeypatch):
        from src.save_system import SaveSystem
        monkeypatch.setattr("src.save_system.SAVE_DIR", str(tmp_path))

        ss = SaveSystem()
        state, msg = ss.load(slot=2)
        assert state is None
        assert "no save" in msg.lower()

    def test_invalid_slot(self, tmp_path, monkeypatch):
        from src.save_system import SaveSystem
        monkeypatch.setattr("src.save_system.SAVE_DIR", str(tmp_path))

        ss = SaveSystem()
        ok, msg = ss.save({}, slot=99)
        assert ok is False

    def test_list_saves_empty(self, tmp_path, monkeypatch):
        from src.save_system import SaveSystem
        monkeypatch.setattr("src.save_system.SAVE_DIR", str(tmp_path))

        ss = SaveSystem()
        slots = ss.list_saves()
        assert len(slots) == 3
        assert all(not s["exists"] for s in slots)

    def test_meta_added_on_save(self, tmp_path, monkeypatch):
        from src.save_system import SaveSystem
        monkeypatch.setattr("src.save_system.SAVE_DIR", str(tmp_path))

        ss = SaveSystem()
        ok, _ = ss.save({"test": "data"}, slot=1)
        loaded, _ = ss.load(slot=1)
        assert "meta" in loaded
        assert "saved_at" in loaded["meta"]


class TestGameIntegration:
    """High-level smoke tests for game command handling."""

    @pytest.fixture
    def game(self):
        from src.game import Game
        return Game()

    def test_game_has_player_in_cryo_bay(self, game):
        assert game.player.location == "cryo_bay"

    def test_parse_examine_dispatches(self, game):
        from src.parser import Command
        # Silence output
        with patch("builtins.print"):
            cmd = Command(verb="examine", args=[], raw="examine")
            game._cmd_examine(cmd)

    def test_parse_status_dispatches(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="status", args=[], raw="status")
            game._cmd_status(cmd)

    def test_parse_inventory_dispatches(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="inventory", args=[], raw="inventory")
            game._cmd_inventory(cmd)

    def test_parse_theorize_creates_entry(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="theorize",
                          args=["the", "captain", "lied"],
                          raw="theorize the captain lied")
            game._cmd_theorize(cmd)
        assert len(game.player.theory_board) == 1

    def test_move_to_adjacent_room(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="move", args=["north"], raw="move north")
            game._cmd_move(cmd)
        assert game.player.location == "cryo_corridor"

    def test_move_to_locked_room_fails(self, game):
        from src.parser import Command
        # Place player near reactor
        game.player.location = "command_deck"
        game.ship.rooms["command_deck"].exits["down"] = "reactor_level"
        with patch("builtins.print"):
            cmd = Command(verb="move", args=["down"], raw="move down")
            game._cmd_move(cmd)
        # Should still be on command_deck since reactor is locked
        assert game.player.location == "command_deck"

    def test_query_cora_returns_response(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="query", args=["reactor"],
                          raw="query cora reactor", quoted=None)
            game._cmd_query(cmd)

    def test_allocate_power_updates_resource(self, game):
        from src.parser import Command
        with patch("builtins.print"):
            cmd = Command(verb="allocate",
                          args=["life_support", "35"],
                          raw="allocate life_support 35")
            game._cmd_allocate(cmd)
        assert game.resources.power_allocation["life_support"] == pytest.approx(35.0)

    def test_build_state_is_complete(self, game):
        state = game._build_state()
        required_keys = ["player", "resources", "ship", "npcs",
                         "cora", "sanity", "puzzles", "narrative"]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"

    def test_restore_state_roundtrip(self, game):
        from src.player import InventoryItem
        # Modify state
        game.player.cycle = 15
        game.player.name = "RoundtripTest"
        game.resources.o2 = 55.0
        item = InventoryItem("hydrospanner", "Hydrospanner", "Tool.", uses=-1)
        game.player.add_item(item)

        state = game._build_state()
        game._restore_state(state)

        assert game.player.cycle == 15
        assert game.player.name == "RoundtripTest"
        assert game.resources.o2 == pytest.approx(55.0)
        assert game.player.has_item("hydrospanner")
