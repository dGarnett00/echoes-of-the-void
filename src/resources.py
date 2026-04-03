"""Resource management system for Echoes of the Void.

Tracks five critical resources per cycle:
  o2      – Ship atmospheric supply (starts 85%)
  power   – Fusion reactor output (starts 60%)
  rations – Food/water for survivors (starts 50 units)
  sanity  – Player mental coherence (starts 90%)
  trust   – Aggregate faction trust (starts 50%)

Power sub-allocation across six subsystems.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ── Constants ────────────────────────────────────────────────────────────────

RESOURCE_DEFAULTS: Dict[str, float] = {
    "o2":      85.0,
    "power":   60.0,
    "rations": 50.0,
    "sanity":  90.0,
    "trust":   50.0,
}

DECAY_RATES: Dict[str, float] = {
    "o2":      2.0,   # per cycle
    "power":   1.5,
    "rations": 1.0,
    "sanity":  0.0,   # handled separately by SanitySystem
    "trust":   0.0,   # event-driven
}

# Thresholds below which warnings are emitted
WARNING_THRESHOLDS: Dict[str, float] = {
    "o2":      30.0,
    "power":   20.0,
    "rations": 15.0,
    "sanity":  20.0,
    "trust":   15.0,
}

CRITICAL_THRESHOLDS: Dict[str, float] = {
    "o2":      10.0,
    "power":   10.0,
    "rations": 5.0,
    "sanity":  10.0,
    "trust":   5.0,
}

# Power subsystems — allocations are percentages of available power
POWER_SUBSYSTEMS: List[str] = [
    "life_support",
    "navigation",
    "cryo_bay",
    "medical",
    "comms",
    "fabrication",
]

DEFAULT_POWER_ALLOCATION: Dict[str, float] = {
    "life_support": 40.0,
    "navigation":   10.0,
    "cryo_bay":     25.0,
    "medical":      10.0,
    "comms":         5.0,
    "fabrication":  10.0,
}


@dataclass
class ResourceWarning:
    """A generated resource warning message."""
    resource: str
    level: str    # "warning" | "critical"
    message: str


@dataclass
class Resources:
    """Mutable resource state."""

    o2:      float = 85.0
    power:   float = 60.0
    rations: float = 50.0
    sanity:  float = 90.0
    trust:   float = 50.0
    power_allocation: Dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_POWER_ALLOCATION)
    )

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "o2":      self.o2,
            "power":   self.power,
            "rations": self.rations,
            "sanity":  self.sanity,
            "trust":   self.trust,
            "power_allocation": dict(self.power_allocation),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Resources":
        r = cls()
        r.o2      = float(data.get("o2",      85.0))
        r.power   = float(data.get("power",   60.0))
        r.rations = float(data.get("rations", 50.0))
        r.sanity  = float(data.get("sanity",  90.0))
        r.trust   = float(data.get("trust",   50.0))
        r.power_allocation = dict(data.get("power_allocation",
                                            DEFAULT_POWER_ALLOCATION))
        return r

    # ── Convenience ───────────────────────────────────────────────────────

    def as_dict(self) -> Dict[str, float]:
        """Return main resource values as a plain dict."""
        return {
            "o2":      self.o2,
            "power":   self.power,
            "rations": self.rations,
            "sanity":  self.sanity,
            "trust":   self.trust,
        }


class ResourceManager:
    """Manages resource decay, allocation, and threshold checks."""

    def __init__(self, resources: Resources) -> None:
        self.res = resources

    # ── Decay ─────────────────────────────────────────────────────────────

    def tick(self) -> Tuple[List[ResourceWarning], List[str]]:
        """Apply one cycle of resource decay.

        Returns:
            warnings – list of ResourceWarning objects
            events   – list of event-string keys for narrative engine
        """
        events: List[str] = []
        warnings: List[ResourceWarning] = []

        # O₂ decay — affected by life_support allocation
        ls_pct = self.res.power_allocation.get("life_support", 40.0) / 100.0
        o2_decay = DECAY_RATES["o2"] * (1.0 + max(0.0, 0.5 - ls_pct))
        self.res.o2 = max(0.0, self.res.o2 - o2_decay)

        # Power decay
        self.res.power = max(0.0, self.res.power - DECAY_RATES["power"])

        # Rations decay
        self.res.rations = max(0.0, self.res.rations - DECAY_RATES["rations"])

        # Low O₂ speeds up sanity loss
        if self.res.o2 < 30.0:
            self.res.sanity = max(0.0, self.res.sanity - 2.0)
            events.append("low_o2_sanity_drain")

        # Low power cascades
        if self.res.power < 20.0:
            self.res.o2 = max(0.0, self.res.o2 - 1.0)
            events.append("low_power_cascade")

        # Rations out → trust drops
        if self.res.rations <= 0.0:
            self.res.trust = max(0.0, self.res.trust - 3.0)
            events.append("rations_depleted")

        # Check thresholds
        for name in ("o2", "power", "rations", "sanity", "trust"):
            value = getattr(self.res, name)
            if value <= CRITICAL_THRESHOLDS.get(name, 10.0):
                warnings.append(ResourceWarning(
                    resource=name,
                    level="critical",
                    message=self._critical_message(name, value),
                ))
                events.append(f"critical_{name}")
            elif value <= WARNING_THRESHOLDS.get(name, 30.0):
                warnings.append(ResourceWarning(
                    resource=name,
                    level="warning",
                    message=self._warning_message(name, value),
                ))

        return warnings, events

    # ── Allocation ────────────────────────────────────────────────────────

    def allocate(self, subsystem: str, amount: float) -> Tuple[bool, str]:
        """Set power allocation for a subsystem.

        The total of all subsystem allocations must stay ≤ 100%.
        Returns (success, message).
        """
        if subsystem not in POWER_SUBSYSTEMS:
            return False, (
                f'Unknown subsystem "{subsystem}". '
                f'Valid: {", ".join(POWER_SUBSYSTEMS)}'
            )
        if not (0.0 <= amount <= 100.0):
            return False, "Allocation must be between 0 and 100."

        current = dict(self.res.power_allocation)
        current[subsystem] = amount
        total = sum(current.values())
        if total > 100.0:
            return False, (
                f"Total allocation would be {total:.1f}% — cannot exceed 100%."
            )
        self.res.power_allocation[subsystem] = amount
        return True, (
            f"Power to {subsystem.replace('_', ' ')} set to {amount:.0f}%."
        )

    def get_subsystem_power(self, subsystem: str) -> float:
        """Return the effective power level for a subsystem (0–100)."""
        alloc = self.res.power_allocation.get(subsystem, 0.0) / 100.0
        return alloc * self.res.power

    # ── Direct modifications ───────────────────────────────────────────────

    def modify(self, resource: str, delta: float) -> None:
        """Add delta to a resource, clamped to [0, 100] (or 0..∞ for rations)."""
        current = getattr(self.res, resource, 0.0)
        if resource == "rations":
            setattr(self.res, resource, max(0.0, current + delta))
        else:
            setattr(self.res, resource, max(0.0, min(100.0, current + delta)))

    # ── Messages ──────────────────────────────────────────────────────────

    @staticmethod
    def _warning_message(name: str, value: float) -> str:
        messages = {
            "o2":      f"WARNING: Atmospheric O₂ at {value:.1f}% — survivors showing hypoxic symptoms.",
            "power":   f"WARNING: Power reserves at {value:.1f}% — risk of cascade failure.",
            "rations": f"WARNING: Rations at {value:.1f} units — rationing required.",
            "sanity":  f"WARNING: Your grip on reality is slipping ({value:.1f}%).",
            "trust":   f"WARNING: Crew trust at {value:.1f}% — tensions rising.",
        }
        return messages.get(name, f"WARNING: {name} at {value:.1f}%.")

    @staticmethod
    def _critical_message(name: str, value: float) -> str:
        messages = {
            "o2":      f"CRITICAL: O₂ at {value:.1f}% — SUFFOCATION IMMINENT.",
            "power":   f"CRITICAL: Power at {value:.1f}% — SYSTEMS FAILING.",
            "rations": f"CRITICAL: Rations at {value:.1f} — STARVATION.",
            "sanity":  f"CRITICAL: Sanity at {value:.1f}% — LOSING YOURSELF.",
            "trust":   f"CRITICAL: Trust at {value:.1f}% — MUTINY POSSIBLE.",
        }
        return messages.get(name, f"CRITICAL: {name} at {value:.1f}%.")
