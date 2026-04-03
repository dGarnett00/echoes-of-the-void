"""Light decision-based encounter/combat system."""

from __future__ import annotations
import random
from typing import Optional, Tuple


ENCOUNTER_OUTCOMES = {
    "standoff": [
        "You hold your ground. Neither of you moves for a long moment.",
        "The tension is palpable. Something has to give.",
    ],
    "withdraw": [
        "You step back. Sometimes discretion is the better part of survival.",
        "You decide this isn't the moment. Live to think another day.",
    ],
    "negotiate": [
        "Words, carefully chosen, defuse the immediate threat.",
        "An uneasy truce. Better than the alternative.",
    ],
    "overcome": [
        "You find a way through — not by force, but by leverage.",
        "The threat resolves in your favour.",
    ],
    "fail": [
        "It doesn't go your way.",
        "Sometimes the situation wins.",
    ],
}


class CombatSystem:
    """Decision-based encounter resolution (not action-based combat)."""

    def resolve_encounter(
        self,
        encounter_type: str,
        player_choice: str,
        player_relationship: int = 0,
        player_sanity: float = 80.0,
    ) -> Tuple[str, str, dict]:
        """Resolve a non-combat encounter.

        Args:
            encounter_type: Type of encounter ("confrontation", "negotiation", etc.)
            player_choice:  Player's chosen approach
            player_relationship: Relationship score with the relevant NPC/faction
            player_sanity:  Current sanity (affects options available)

        Returns:
            (outcome_key, narrative_text, effects)
        """
        effects: dict = {}

        if encounter_type == "faction_confrontation":
            return self._resolve_faction_confrontation(
                player_choice, player_relationship, effects
            )

        if encounter_type == "ghost_standoff":
            return self._resolve_ghost_standoff(
                player_choice, player_relationship, effects
            )

        # Generic fallback
        outcome = random.choice(list(ENCOUNTER_OUTCOMES.keys()))
        text = random.choice(ENCOUNTER_OUTCOMES[outcome])
        return outcome, text, effects

    def _resolve_faction_confrontation(
        self,
        choice: str,
        relationship: int,
        effects: dict,
    ) -> Tuple[str, str, dict]:
        choice_lower = choice.lower()

        if "mediate" in choice_lower or "both" in choice_lower:
            effects["trust_navigators"] = +3
            effects["trust_keepers"] = +3
            effects["sanity"] = -2
            return "negotiate", (
                "You offer a middle path — not either/or, but a temporary "
                "allocation that buys time for a longer-term solution. "
                "Neither Okonkwo nor Tanaka is satisfied. Both accept. "
                "It's the best outcome available right now."
            ), effects

        if "navigator" in choice_lower or "okonkwo" in choice_lower:
            effects["trust_navigators"] = +8
            effects["trust_keepers"] = -10
            effects["power_navigation"] = +10
            return "overcome", (
                "You side with the Captain's math. Tanaka's face tightens "
                "but she doesn't argue — she simply turns and walks to her "
                "cabin. The cryo-pods that go dark tonight will haunt you "
                "in ways the numbers don't capture."
            ), effects

        if "keeper" in choice_lower or "tanaka" in choice_lower:
            effects["trust_keepers"] = +8
            effects["trust_navigators"] = -10
            effects["power_cryo_bay"] = +10
            return "overcome", (
                "You stand with Tanaka. The pods are maintained. The "
                "navigation window closes. Okonkwo's jaw tightens. "
                "'You've chosen sentiment over survival,' she says. "
                "She may be right."
            ), effects

        effects["trust_navigators"] = -2
        effects["trust_keepers"] = -2
        return "fail", (
            "Your indecision costs you credibility with both factions. "
            "They make the decision without you."
        ), effects

    def _resolve_ghost_standoff(
        self,
        choice: str,
        relationship: int,
        effects: dict,
    ) -> Tuple[str, str, dict]:
        choice_lower = choice.lower()

        if "trade" in choice_lower or "offer" in choice_lower:
            effects["trust_ghosts"] = +5
            return "negotiate", (
                "Razor evaluates your offer with flat, professional eyes. "
                "'Acceptable,' they say. An exchange is made. "
                "You're now slightly less unknown to them."
            ), effects

        if "back" in choice_lower or "leave" in choice_lower or "withdraw" in choice_lower:
            return "withdraw", (
                "You step away. Razor watches you go. "
                "'Smart,' one of their followers says."
            ), effects

        if relationship > 20:
            effects["trust_ghosts"] = +3
            return "negotiate", (
                "Your history with the Ghosts counts for something. "
                "The standoff de-escalates into something approaching "
                "mutual tolerance."
            ), effects

        return "standoff", (
            "Nobody moves. After a long moment, both sides back away. "
            "Nothing resolved. Nothing worsened."
        ), effects
