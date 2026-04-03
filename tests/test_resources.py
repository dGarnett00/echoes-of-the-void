"""Tests for the resource management system."""

import pytest
from src.resources import (
    Resources, ResourceManager, POWER_SUBSYSTEMS,
    DEFAULT_POWER_ALLOCATION, WARNING_THRESHOLDS, CRITICAL_THRESHOLDS,
)


@pytest.fixture
def resources() -> Resources:
    return Resources()


@pytest.fixture
def manager(resources) -> ResourceManager:
    return ResourceManager(resources)


class TestResourceDefaults:
    def test_default_o2(self, resources):
        assert resources.o2 == pytest.approx(85.0)

    def test_default_power(self, resources):
        assert resources.power == pytest.approx(60.0)

    def test_default_rations(self, resources):
        assert resources.rations == pytest.approx(50.0)

    def test_default_sanity(self, resources):
        assert resources.sanity == pytest.approx(90.0)

    def test_default_trust(self, resources):
        assert resources.trust == pytest.approx(50.0)

    def test_default_power_allocation_sums_to_100(self, resources):
        total = sum(resources.power_allocation.values())
        assert total == pytest.approx(100.0)

    def test_all_subsystems_in_allocation(self, resources):
        for sub in POWER_SUBSYSTEMS:
            assert sub in resources.power_allocation


class TestResourceDecay:
    def test_tick_reduces_o2(self, manager, resources):
        initial_o2 = resources.o2
        manager.tick()
        assert resources.o2 < initial_o2

    def test_tick_reduces_power(self, manager, resources):
        initial_power = resources.power
        manager.tick()
        assert resources.power < initial_power

    def test_tick_reduces_rations(self, manager, resources):
        initial_rations = resources.rations
        manager.tick()
        assert resources.rations < initial_rations

    def test_o2_does_not_go_negative(self, manager, resources):
        resources.o2 = 0.5
        manager.tick()
        assert resources.o2 >= 0.0

    def test_power_does_not_go_negative(self, manager, resources):
        resources.power = 0.5
        manager.tick()
        assert resources.power >= 0.0

    def test_rations_do_not_go_negative(self, manager, resources):
        resources.rations = 0.5
        manager.tick()
        assert resources.rations >= 0.0

    def test_tick_returns_warnings_and_events(self, manager):
        warnings, events = manager.tick()
        assert isinstance(warnings, list)
        assert isinstance(events, list)

    def test_critical_o2_triggers_event(self, manager, resources):
        resources.o2 = 5.0
        _, events = manager.tick()
        assert "critical_o2" in events

    def test_critical_power_triggers_event(self, manager, resources):
        resources.power = 5.0
        _, events = manager.tick()
        assert "critical_power" in events

    def test_low_o2_causes_sanity_drain(self, manager, resources):
        resources.o2 = 20.0
        initial_sanity = resources.sanity
        _, events = manager.tick()
        assert "low_o2_sanity_drain" in events
        assert resources.sanity < initial_sanity

    def test_low_power_cascades_to_o2(self, manager, resources):
        resources.power = 15.0
        initial_o2 = resources.o2
        _, events = manager.tick()
        assert "low_power_cascade" in events

    def test_rations_depleted_event(self, manager, resources):
        resources.rations = 0.5
        _, events = manager.tick()
        assert "rations_depleted" in events

    def test_rations_depleted_reduces_trust(self, manager, resources):
        resources.rations = 0.5
        initial_trust = resources.trust
        manager.tick()
        assert resources.trust < initial_trust


class TestPowerAllocation:
    def test_allocate_valid(self, manager, resources):
        # Reduce life_support from default 40 to 30 (total stays ≤ 100)
        ok, msg = manager.allocate("life_support", 30.0)
        assert ok is True
        assert resources.power_allocation["life_support"] == pytest.approx(30.0)

    def test_allocate_invalid_subsystem(self, manager):
        ok, msg = manager.allocate("warp_engine", 40.0)
        assert ok is False
        assert "unknown" in msg.lower() or "valid" in msg.lower()

    def test_allocate_negative_fails(self, manager):
        ok, msg = manager.allocate("navigation", -10.0)
        assert ok is False

    def test_allocate_over_100_fails(self, manager, resources):
        ok, msg = manager.allocate("life_support", 150.0)
        assert ok is False

    def test_allocate_exceeds_total_fails(self, manager, resources):
        # Try to set one system to 100 when total is already 100
        ok, msg = manager.allocate("navigation", 100.0)
        assert ok is False
        assert "100" in msg or "exceed" in msg.lower()

    def test_reduce_one_system_then_increase_another(self, manager, resources):
        # Reduce life_support from 40 to 20 (saves 20)
        ok1, _ = manager.allocate("life_support", 20.0)
        # Now increase navigation from 10 to 30
        ok2, _ = manager.allocate("navigation", 30.0)
        assert ok1 is True
        assert ok2 is True
        total = sum(resources.power_allocation.values())
        assert total == pytest.approx(100.0)

    def test_get_subsystem_power(self, manager, resources):
        resources.power = 60.0
        resources.power_allocation["life_support"] = 40.0
        pwr = manager.get_subsystem_power("life_support")
        assert pwr == pytest.approx(24.0)  # 40% of 60


class TestResourceModify:
    def test_modify_positive(self, manager, resources):
        resources.o2 = 50.0
        manager.modify("o2", 10.0)
        assert resources.o2 == pytest.approx(60.0)

    def test_modify_negative(self, manager, resources):
        resources.o2 = 50.0
        manager.modify("o2", -20.0)
        assert resources.o2 == pytest.approx(30.0)

    def test_modify_capped_at_100(self, manager, resources):
        resources.o2 = 95.0
        manager.modify("o2", 20.0)
        assert resources.o2 == pytest.approx(100.0)

    def test_modify_floors_at_0(self, manager, resources):
        resources.o2 = 5.0
        manager.modify("o2", -20.0)
        assert resources.o2 == pytest.approx(0.0)

    def test_modify_rations_no_cap(self, manager, resources):
        resources.rations = 50.0
        manager.modify("rations", 60.0)
        # Rations can exceed 100
        assert resources.rations == pytest.approx(110.0)


class TestWarningThresholds:
    def test_warning_at_threshold(self, manager, resources):
        resources.o2 = WARNING_THRESHOLDS["o2"] - 1
        warnings, _ = manager.tick()
        o2_warnings = [w for w in warnings if w.resource == "o2"]
        assert len(o2_warnings) > 0

    def test_critical_at_threshold(self, manager, resources):
        resources.o2 = CRITICAL_THRESHOLDS["o2"] - 1
        warnings, _ = manager.tick()
        o2_criticals = [w for w in warnings if w.resource == "o2" and w.level == "critical"]
        assert len(o2_criticals) > 0


class TestSerialization:
    def test_to_dict_roundtrip(self, resources):
        d = resources.to_dict()
        restored = Resources.from_dict(d)
        assert restored.o2      == pytest.approx(resources.o2)
        assert restored.power   == pytest.approx(resources.power)
        assert restored.rations == pytest.approx(resources.rations)
        assert restored.sanity  == pytest.approx(resources.sanity)
        assert restored.trust   == pytest.approx(resources.trust)

    def test_to_dict_includes_allocation(self, resources):
        d = resources.to_dict()
        assert "power_allocation" in d
        assert isinstance(d["power_allocation"], dict)

    def test_as_dict_returns_main_resources(self, resources):
        d = resources.as_dict()
        assert "o2" in d
        assert "power" in d
        assert "rations" in d
        assert "sanity" in d
        assert "trust" in d
        assert "power_allocation" not in d
