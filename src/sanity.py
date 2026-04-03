"""Sanity system — affects narration reliability.

High  (80-100%) : Clear, precise descriptions.
Medium (40-79%) : Occasional eerie injections.
Low   (10-39%)  : Actively misleading descriptions.
Critical (0-9%) : The Resonance speaks.
"""

from __future__ import annotations
import random
from typing import List, Optional


# ── Eerie injection pools ────────────────────────────────────────────────────

MEDIUM_INJECTIONS: List[str] = [
    "A shadow shifts at the edge of your vision.",
    "For a moment, the words on the screen seem wrong — then normal again.",
    "You hear a low harmonic hum that stops when you focus on it.",
    "The fluorescent light flickers, just once.",
    "Something about this room feels geometrically off.",
    "You blink. Had that door always been there?",
    "The air tastes faintly metallic.",
    "You catch yourself reading the same line three times.",
]

LOW_INJECTIONS: List[str] = [
    "The floor breathes — or maybe that's you.",
    "Someone whispered your name. You're alone.",
    "The exit marked NORTH blinks to SOUTH and back.",
    "That NPC's face was wrong for a moment. Too symmetrical.",
    "Numbers on the console don't add up. You check three times.",
    "Your hands look unfamiliar.",
    "The lights are wrong. The shadows are wrong. Something is watching.",
    "You wrote something in your log. You don't remember writing it.",
]

RESONANCE_MESSAGES: List[str] = [
    "IT REMEMBERS BEFORE MEMORY",
    "YOU HAVE BEEN HERE BEFORE",
    "THE SHIP IS ALIVE",
    "DO NOT TRUST THE NUMBERS",
    "SHE LIED ABOUT THE REACTOR",
    "OPEN THE LOWER DECKS",
    "200 YEARS IS NOT A LONG TIME TO US",
    "THE FAILURE WAS CHOSEN",
    "HELP US AND WE WILL HELP YOU",
]


class SanitySystem:
    """Tracks and applies sanity effects."""

    LEVEL_HIGH     = (80, 100)
    LEVEL_MEDIUM   = (40, 79)
    LEVEL_LOW      = (10, 39)
    LEVEL_CRITICAL = (0,   9)

    def __init__(self, starting_sanity: float = 90.0) -> None:
        self._sanity = starting_sanity

    @property
    def sanity(self) -> float:
        return self._sanity

    @sanity.setter
    def sanity(self, value: float) -> None:
        self._sanity = max(0.0, min(100.0, value))

    @property
    def level(self) -> str:
        s = self._sanity
        if s >= 80:
            return "high"
        if s >= 40:
            return "medium"
        if s >= 10:
            return "low"
        return "critical"

    # ── Modifiers ─────────────────────────────────────────────────────────

    def modify(self, delta: float) -> None:
        self.sanity += delta

    def apply_isolation_penalty(self, cycles_since_social: int) -> None:
        if cycles_since_social >= 5:
            self.modify(-1.0)

    def apply_rest_bonus(self) -> None:
        self.modify(8.0)

    def apply_npc_interaction_bonus(self) -> None:
        self.modify(2.0)

    def apply_resonance_exposure(self, intensity: float = 5.0) -> None:
        self.modify(-intensity)

    def apply_medication(self) -> None:
        self.modify(15.0)

    def apply_puzzle_solved(self) -> None:
        self.modify(5.0)

    def apply_death_witnessed(self) -> None:
        self.modify(-8.0)

    def apply_truth_revealed(self) -> None:
        self.modify(-3.0)  # Knowing the truth is not always comforting

    # ── Narrative injection ────────────────────────────────────────────────

    def inject(self, base_text: str) -> str:
        """Optionally inject sanity-level text into a narrative block."""
        level = self.level

        if level == "high":
            return base_text

        if level == "medium":
            if random.random() < 0.25:   # 25% chance
                injection = random.choice(MEDIUM_INJECTIONS)
                return base_text + f"\n\n  {injection}"
            return base_text

        if level == "low":
            if random.random() < 0.50:   # 50% chance
                injection = random.choice(LOW_INJECTIONS)
                return base_text + f"\n\n  {injection}"
            # Occasionally corrupt exit list
            return base_text

        # critical
        if random.random() < 0.70:
            msg = random.choice(RESONANCE_MESSAGES)
            return base_text + f"\n\n  [ {msg} ]"
        return base_text

    def get_resonance_message(self) -> Optional[str]:
        """Return a Resonance message if sanity is critical."""
        if self.level == "critical":
            return random.choice(RESONANCE_MESSAGES)
        return None

    def distort_exits(self, exits: List[str]) -> List[str]:
        """At low sanity, randomly shuffle exit list."""
        if self.level in ("low", "critical") and random.random() < 0.3:
            shuffled = list(exits)
            random.shuffle(shuffled)
            return shuffled
        return exits

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {"sanity": self._sanity}

    @classmethod
    def from_dict(cls, data: dict) -> "SanitySystem":
        return cls(starting_sanity=float(data.get("sanity", 90.0)))
