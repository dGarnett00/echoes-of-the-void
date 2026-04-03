"""Puzzle and challenge system for Echoes of the Void."""

from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@dataclass
class PuzzleState:
    """Tracks a puzzle's progress."""
    puzzle_id:  str
    solved:     bool = False
    attempts:   int  = 0
    progress:   Dict[str, Any] = field(default_factory=dict)


class PuzzleManager:
    """Manages puzzle definitions and state."""

    def __init__(self) -> None:
        self.puzzles: Dict[str, dict] = {}
        self.states:  Dict[str, PuzzleState] = {}
        self._load_puzzles()

    def _load_puzzles(self) -> None:
        path = os.path.join(DATA_DIR, "puzzles.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.puzzles = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.puzzles = {}

        for pid in self.puzzles:
            self.states[pid] = PuzzleState(puzzle_id=pid)

    def get_puzzle(self, puzzle_id: str) -> Optional[dict]:
        return self.puzzles.get(puzzle_id)

    def is_solved(self, puzzle_id: str) -> bool:
        state = self.states.get(puzzle_id)
        return state.solved if state else False

    # ── Atmospheric Processor (Logic puzzle) ─────────────────────────────

    def attempt_atmospheric_processor(
        self,
        filters: str,
        compressors: str,
        regulators: str,
    ) -> Tuple[bool, str]:
        """Attempt to solve the atmospheric processor puzzle."""
        pid = "atmospheric_processor"
        puzzle = self.puzzles.get(pid, {})
        state  = self.states.get(pid)
        if not state or not puzzle:
            return False, "Puzzle not available."
        if state.solved:
            return True, "The processor is already running."

        state.attempts += 1
        solution = puzzle.get("correct_solution", {})
        cora_wrong = puzzle.get("cora_wrong_solution", {})

        attempt = {
            "filters": filters.upper(),
            "compressors": compressors.upper(),
            "regulators": regulators.upper(),
        }

        if attempt == {k: v.upper() for k, v in solution.items()}:
            state.solved = True
            return True, (
                "The processor hums to life. The three subsystems find "
                "their equilibrium — filters and regulators ACTIVE, "
                "compressors in STANDBY. O₂ output begins to climb."
            )

        # CORA's wrong answer
        if attempt == {k: v.upper() for k, v in cora_wrong.items()}:
            return False, (
                "The configuration triggers a power surge. The compressors "
                "fight each other — you cut the power just in time. A faint "
                "burn mark joins the others on the compressor panel. "
                "CORA's recommendation was wrong. There's a clue here."
            )

        hints = []
        for key in ("filters", "compressors", "regulators"):
            if attempt.get(key) == solution.get(key, "").upper():
                hints.append(f"{key}: ✓")
            else:
                hints.append(f"{key}: ✗")

        return False, (
            f"The configuration doesn't work. ({', '.join(hints)}) "
            "Examine the environmental clues more carefully."
        )

    # ── Archive Decryption (Cipher puzzle) ───────────────────────────────

    def attempt_archive_decryption(
        self,
        fragments: List[str],
        identified_fake: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Attempt the archive decryption puzzle."""
        pid = "archive_decryption"
        puzzle = self.puzzles.get(pid, {})
        state  = self.states.get(pid)
        if not state or not puzzle:
            return False, "Puzzle not available."
        if state.solved:
            return True, "The archives are already open."

        state.attempts += 1
        real_fragments = set(puzzle.get("real_fragments", []))
        fake_fragment  = puzzle.get("fake_fragment", "")

        provided = set(fragments)
        if identified_fake and identified_fake != fake_fragment:
            return False, (
                f"You believe '{identified_fake}' is the fake, but the "
                "decryption fails. The archive remains locked. "
                "Cross-reference the log author name and date format more carefully."
            )

        # Need real fragments and identified fake
        if real_fragments.issubset(provided) and identified_fake == fake_fragment:
            state.solved = True
            return True, (
                "With the forgery identified and discarded, the two authentic "
                "key fragments unlock the archive. The screens fill with data "
                "— 200 years of ship history, mission briefings, the unredacted "
                "truth of the FTL event. The archive is open."
            )

        if not real_fragments.issubset(provided):
            missing = real_fragments - provided
            return False, (
                f"Missing key fragments: {', '.join(missing)}. "
                "Find all authentic fragments before attempting decryption."
            )

        return False, (
            "You have the fragments but haven't identified the fake. "
            "Examine the log metadata — author, date format, content consistency."
        )

    # ── Reactor Diagnostic (Bayesian puzzle) ─────────────────────────────

    def run_reactor_test(self, test_id: str) -> Tuple[bool, str, dict]:
        """Run one reactor diagnostic test.

        Returns (success, result_text, test_data).
        """
        pid = "reactor_diagnostic"
        puzzle = self.puzzles.get(pid, {})
        state  = self.states.get(pid)
        if not state or not puzzle:
            return False, "Puzzle not available.", {}

        tests = puzzle.get("tests", {})
        test = tests.get(f"test_{test_id.lower()}")
        if not test:
            return False, f"Unknown test '{test_id}'. Valid: A, B, C.", {}

        # Record which tests have been run
        if "run_tests" not in state.progress:
            state.progress["run_tests"] = []
        if test_id.lower() not in state.progress["run_tests"]:
            state.progress["run_tests"].append(test_id.lower())

        # Check if all three tests run → auto-solve
        if len(state.progress.get("run_tests", [])) >= 2:
            state.progress["can_conclude"] = True

        return True, test["result"], test

    def conclude_reactor_diagnosis(self, answer: str) -> Tuple[bool, str]:
        """Submit the reactor diagnosis conclusion."""
        pid = "reactor_diagnostic"
        puzzle = self.puzzles.get(pid, {})
        state  = self.states.get(pid)
        if not state or not puzzle:
            return False, "Puzzle not available."
        if state.solved:
            return True, "Reactor already optimised."

        correct = puzzle.get("correct_answer", "C")
        if answer.upper() == correct.upper():
            state.solved = True
            return True, (
                "Correct. The coolant loop pressure drop is the primary "
                "cause. With targeted repairs to the coolant system, "
                "reactor output climbs from 11% toward 22%. Power reserves "
                "increase significantly."
            )
        else:
            return False, (
                f"Incorrect. Targeting system {answer.upper()} has no "
                "significant effect on reactor efficiency. Review the test "
                "results and reason through which system is actually "
                "the primary constraint."
            )

    # ── Saboteur Investigation (Deduction puzzle) ─────────────────────────

    def add_evidence(self, evidence_id: str, state_ref: PuzzleState) -> str:
        """Record finding evidence for the investigation."""
        pid = "saboteur_investigation"
        puzzle = self.puzzles.get(pid, {})
        evidence_items = puzzle.get("evidence_items", [])

        for item in evidence_items:
            if item["id"] == evidence_id:
                if "found_evidence" not in state_ref.progress:
                    state_ref.progress["found_evidence"] = []
                if evidence_id not in state_ref.progress["found_evidence"]:
                    state_ref.progress["found_evidence"].append(evidence_id)
                return f"Evidence recorded: {item['description']}"
        return f"Evidence item '{evidence_id}' not found."

    def confront_suspect(
        self,
        suspect_id: str,
        evidence: List[str],
    ) -> Tuple[bool, str]:
        """Confront a suspect with accumulated evidence."""
        pid = "saboteur_investigation"
        puzzle = self.puzzles.get(pid, {})
        state  = self.states.get(pid)
        if not state or not puzzle:
            return False, "Investigation not active."
        if state.solved:
            return True, "The case is already closed."

        correct_saboteur = puzzle.get("saboteur", "venn")
        suspects = puzzle.get("suspects", {})
        suspect_data = suspects.get(suspect_id, {})

        if not suspect_data:
            return False, f"Unknown suspect '{suspect_id}'."

        state.attempts += 1

        if suspect_id == correct_saboteur:
            # Check if player has enough evidence
            pointing_evidence = [
                e for e in puzzle.get("evidence_items", [])
                if e.get("points_to") == correct_saboteur and e["id"] in evidence
            ]
            if len(pointing_evidence) >= 2:
                state.solved = True
                return True, (
                    f"Confronted with the evidence, {suspect_id.title()} "
                    "doesn't deny it. 'I did what needed to be done,' "
                    "Venn says quietly. 'The factions had to be forced to "
                    "consider alternatives. I'm sorry for the risk. I'm not "
                    "sorry for the goal.' The truth is complicated. "
                    "The case is closed."
                )
            else:
                return False, (
                    f"You confront {suspect_id.title()} but lack sufficient "
                    "evidence. They deny everything calmly. You need more "
                    "before you can make this stick."
                )
        else:
            # Wrong suspect
            alibi_strength = suspect_data.get("alibi_strength", "medium")
            if alibi_strength == "strong":
                return False, (
                    f"The accusation fails immediately. {suspect_id.title()}'s "
                    f"alibi is airtight: {suspect_data.get('alibi', 'multiple witnesses')}. "
                    "You've wasted trust. Reassess the evidence."
                )
            return False, (
                f"{suspect_id.title()} challenges you to prove it. "
                f"Their alibi: {suspect_data.get('alibi', 'disputed')}. "
                "You don't have enough to counter it convincingly. "
                "You may have accused the wrong person."
            )

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            pid: {
                "solved":   s.solved,
                "attempts": s.attempts,
                "progress": s.progress,
            }
            for pid, s in self.states.items()
        }

    def apply_state(self, data: dict) -> None:
        for pid, sdata in data.items():
            if pid not in self.states:
                self.states[pid] = PuzzleState(puzzle_id=pid)
            state = self.states[pid]
            state.solved   = sdata.get("solved",   False)
            state.attempts = sdata.get("attempts", 0)
            state.progress = sdata.get("progress", {})
