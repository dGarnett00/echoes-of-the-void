"""Tests for the command parser."""

import pytest
from src.parser import Parser, Command, VALID_VERBS


@pytest.fixture
def parser() -> Parser:
    return Parser()


class TestBasicParsing:
    def test_empty_input(self, parser):
        result = parser.parse("")
        assert result.ok is False
        assert "command" in result.error.lower() or "enter" in result.error.lower()

    def test_whitespace_only(self, parser):
        result = parser.parse("   ")
        assert result.ok is False

    def test_valid_verb_examine(self, parser):
        result = parser.parse("examine")
        assert result.ok is True
        assert result.command.verb == "examine"

    def test_valid_verb_with_noun(self, parser):
        result = parser.parse("examine reactor console")
        assert result.ok is True
        assert result.command.verb == "examine"
        assert "reactor" in result.command.args

    def test_invalid_verb(self, parser):
        result = parser.parse("dance wildly")
        assert result.ok is False
        assert "dance" in result.error.lower() or "understand" in result.error.lower()

    def test_help_command(self, parser):
        result = parser.parse("help")
        assert result.ok is True
        assert result.command.verb == "help"

    def test_quit_command(self, parser):
        result = parser.parse("quit")
        assert result.ok is True
        assert result.command.verb == "quit"

    def test_status_command(self, parser):
        result = parser.parse("status")
        assert result.ok is True
        assert result.command.verb == "status"


class TestAliases:
    def test_look_is_examine(self, parser):
        result = parser.parse("look")
        assert result.ok is True
        assert result.command.verb == "examine"

    def test_go_is_move(self, parser):
        result = parser.parse("go north")
        assert result.ok is True
        assert result.command.verb == "move"

    def test_direction_shortcut_north(self, parser):
        result = parser.parse("north")
        assert result.ok is True
        assert result.command.verb == "move"
        assert "north" in result.command.args

    def test_direction_shortcut_south(self, parser):
        result = parser.parse("south")
        assert result.ok is True
        assert result.command.verb == "move"

    def test_inv_is_inventory(self, parser):
        result = parser.parse("inv")
        assert result.ok is True
        assert result.command.verb == "inventory"

    def test_exit_is_quit(self, parser):
        result = parser.parse("exit")
        assert result.ok is True
        assert result.command.verb == "quit"

    def test_i_is_inventory(self, parser):
        result = parser.parse("i")
        assert result.ok is True
        assert result.command.verb == "inventory"


class TestQueryCora:
    def test_query_cora_simple(self, parser):
        result = parser.parse("query cora reactor")
        assert result.ok is True
        assert result.command.verb == "query"
        assert "reactor" in result.command.args

    def test_query_cora_with_quotes(self, parser):
        result = parser.parse('query cora "Why hasn\'t the reactor shut down?"')
        assert result.ok is True
        assert result.command.verb == "query"
        assert result.command.quoted is not None
        assert "reactor" in result.command.quoted.lower()

    def test_query_without_cora(self, parser):
        result = parser.parse("query reactor")
        assert result.ok is True
        assert result.command.verb == "query"


class TestTalkCommand:
    def test_talk_to_npc(self, parser):
        result = parser.parse("talk vasquez")
        assert result.ok is True
        assert result.command.verb == "talk"
        assert "vasquez" in result.command.args

    def test_talk_to_with_to(self, parser):
        result = parser.parse("talk to tanaka")
        assert result.ok is True
        assert result.command.verb == "talk"
        # "to" should be filtered out
        assert "tanaka" in result.command.args


class TestAllocateCommand:
    def test_allocate_power(self, parser):
        result = parser.parse("allocate life_support 40")
        assert result.ok is True
        assert result.command.verb == "allocate"
        assert "life_support" in result.command.args

    def test_allocate_no_args(self, parser):
        result = parser.parse("allocate")
        assert result.ok is True
        assert result.command.verb == "allocate"
        assert result.command.args == []


class TestTheorizeCommand:
    def test_theorize_with_text(self, parser):
        result = parser.parse("theorize The FTL failure was intentional")
        assert result.ok is True
        assert result.command.verb == "theorize"
        # All words preserved for theory notes
        text = " ".join(result.command.args)
        assert "ftl" in text.lower() or "failure" in text.lower()

    def test_theory_alias(self, parser):
        result = parser.parse("theory something")
        assert result.ok is True
        assert result.command.verb == "theorize"


class TestCommandProperties:
    def test_noun_extraction(self, parser):
        result = parser.parse("examine the reactor console")
        assert result.ok is True
        cmd = result.command
        # "the" should be filtered from noun
        assert cmd.noun == "reactor"

    def test_full_args_no_fillers(self, parser):
        result = parser.parse("examine the big reactor console")
        assert result.ok is True
        cmd = result.command
        full = cmd.full_args
        assert "reactor" in full
        assert "the" not in full

    def test_raw_preserved(self, parser):
        raw = "EXAMINE the Reactor Console"
        result = parser.parse(raw)
        assert result.ok is True
        assert result.command.raw == raw


class TestSaveLoadCommands:
    def test_save_default(self, parser):
        result = parser.parse("save")
        assert result.ok is True
        assert result.command.verb == "save"

    def test_save_with_slot(self, parser):
        result = parser.parse("save 2")
        assert result.ok is True
        assert "2" in result.command.args

    def test_load_with_slot(self, parser):
        result = parser.parse("load 3")
        assert result.ok is True
        assert result.command.verb == "load"
        assert "3" in result.command.args


class TestAllValidVerbs:
    @pytest.mark.parametrize("verb", list(VALID_VERBS))
    def test_valid_verb_parses(self, parser, verb):
        result = parser.parse(verb)
        assert result.ok is True, f"Expected '{verb}' to parse successfully"
        assert result.command.verb == verb
