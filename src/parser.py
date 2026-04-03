"""Command parser for Echoes of the Void.

Supports verb-noun-modifier grammar:
    EXAMINE reactor console
    TALK TO Dr. Tanaka
    QUERY CORA "Why hasn't the reactor shut down?"
    ALLOCATE power life_support 30
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional, List


# ── Verb aliases ─────────────────────────────────────────────────────────────

VERB_ALIASES: dict[str, str] = {
    # Movement
    "go":       "move",
    "walk":     "move",
    "travel":   "move",
    "enter":    "move",
    "north":    "move",
    "south":    "move",
    "east":     "move",
    "west":     "move",
    "up":       "move",
    "down":     "move",
    # Examine
    "look":     "examine",
    "inspect":  "examine",
    "check":    "examine",
    "read":     "examine",
    "search":   "examine",
    # Inventory
    "inv":      "inventory",
    "items":    "inventory",
    "i":        "inventory",
    # Status
    "stat":     "status",
    "stats":    "status",
    "resources":"status",
    # Quit
    "exit":     "quit",
    "q":        "quit",
    # Help
    "h":        "help",
    "?":        "help",
    # Talk
    "speak":    "talk",
    "ask":      "talk",
    # Allocate
    "distribute":"allocate",
    "route":    "allocate",
    "power":    "allocate",
    # Theorize
    "note":     "theorize",
    "theory":   "theorize",
    "record":   "theorize",
    # Confront
    "accuse":   "confront",
    # Use
    "take":     "use",
    "pick":     "use",
    "grab":     "use",
    "activate": "use",
    "open":     "use",
}

VALID_VERBS: set[str] = {
    "examine", "move", "talk", "query", "allocate", "use",
    "repair", "theorize", "rest", "confront", "inventory",
    "status", "help", "save", "load", "quit",
}

DIRECTION_WORDS: set[str] = {"north", "south", "east", "west", "up", "down"}

# Words that are ignored when parsing objects ("the", "to", etc.)
FILLER_WORDS: set[str] = {"the", "a", "an", "to", "at", "into", "in", "on",
                           "with", "about", "of"}


@dataclass
class Command:
    """Parsed player command."""
    verb:     str                        # Normalised verb
    args:     List[str] = field(default_factory=list)   # Remaining tokens
    raw:      str = ""                   # Original input
    quoted:   Optional[str] = None       # Text inside quotes (for QUERY CORA)

    @property
    def noun(self) -> str:
        """First non-filler argument (the primary noun)."""
        for arg in self.args:
            if arg not in FILLER_WORDS:
                return arg
        return ""

    @property
    def modifier(self) -> str:
        """Everything after the noun joined together."""
        args = [a for a in self.args if a not in FILLER_WORDS]
        if len(args) > 1:
            return " ".join(args[1:])
        return ""

    @property
    def full_args(self) -> str:
        """All args joined (after stripping fillers)."""
        return " ".join(a for a in self.args if a not in FILLER_WORDS)


@dataclass
class ParseResult:
    """Result of parsing a player input string."""
    ok:      bool
    command: Optional[Command] = None
    error:   str = ""


class Parser:
    """Parse raw text input into Command objects."""

    def parse(self, raw: str) -> ParseResult:
        """Parse a raw input string into a ParseResult."""
        text = raw.strip()
        if not text:
            return ParseResult(ok=False, error="Please enter a command. Type HELP for a list.")

        # Extract quoted strings before tokenising
        quoted: Optional[str] = None
        quote_match = re.search(r'"([^"]*)"', text)
        if quote_match:
            quoted = quote_match.group(1)
            text = text[:quote_match.start()] + text[quote_match.end():]

        tokens = text.lower().split()
        if not tokens:
            return ParseResult(ok=False, error="Please enter a command. Type HELP for a list.")

        verb_token = tokens[0]
        rest = tokens[1:]

        # Handle direction shortcuts at the verb position
        if verb_token in DIRECTION_WORDS:
            return ParseResult(
                ok=True,
                command=Command(verb="move", args=[verb_token] + rest, raw=raw, quoted=quoted),
            )

        # Normalise via alias map
        verb = VERB_ALIASES.get(verb_token, verb_token)

        # Special case: "query cora" is a two-word command
        if verb == "query" and rest and rest[0] == "cora":
            rest = rest[1:]

        if verb not in VALID_VERBS:
            return ParseResult(
                ok=False,
                error=(
                    f'I don\'t understand "{verb_token}". '
                    "Type HELP for a list of commands."
                ),
            )

        # Strip filler words that precede the noun (e.g. "talk TO tanaka")
        cleaned = [t for t in rest if t not in FILLER_WORDS] if verb not in ("theorize",) else rest

        return ParseResult(
            ok=True,
            command=Command(verb=verb, args=cleaned, raw=raw, quoted=quoted),
        )
