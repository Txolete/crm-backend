"""
Tests for calculate_probability and calculate_weighted_value
"""
import pytest
from types import SimpleNamespace
from app.utils.opportunity import (
    calculate_probability,
    calculate_weighted_value,
    DEFAULT_STAGE_PROBABILITIES,
)


def _make_opp(
    stage_id="stage-1",
    probability_override=None,
    expected_value_eur=100_000.0,
    weighted_value_override_eur=None,
):
    return SimpleNamespace(
        stage_id=stage_id,
        probability_override=probability_override,
        expected_value_eur=expected_value_eur,
        weighted_value_override_eur=weighted_value_override_eur,
    )


def _make_stage(id, key):
    return SimpleNamespace(id=id, key=key)


# ---------------------------------------------------------------------------
# calculate_probability
# ---------------------------------------------------------------------------

class TestCalculateProbability:
    def test_override_takes_precedence(self):
        """Case 1: probability_override is set -> return override"""
        opp = _make_opp(probability_override=0.85)
        assert calculate_probability(opp, {}, {}) == 0.85

    def test_stage_probs_map_used(self):
        """Case 2: no override, stage_probs_map has entry -> return map value"""
        opp = _make_opp(stage_id="s1")
        stage_probs_map = {"s1": 0.42}
        assert calculate_probability(opp, stage_probs_map, {}) == 0.42

    def test_default_fallback_by_stage_key(self):
        """Case 3: no override, no map entry, known stage key -> return default"""
        stage = _make_stage("s1", "proposal")
        opp = _make_opp(stage_id="s1")
        stages_map = {"s1": stage}
        assert calculate_probability(opp, {}, stages_map) == 0.50

    def test_unknown_stage_returns_zero(self):
        """Fallback: unknown stage key and no map -> 0.0"""
        stage = _make_stage("s1", "unknown_key")
        opp = _make_opp(stage_id="s1")
        stages_map = {"s1": stage}
        assert calculate_probability(opp, {}, stages_map) == 0.0

    def test_all_default_keys_present(self):
        """Verify all expected default keys exist"""
        expected_keys = {"new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"}
        assert set(DEFAULT_STAGE_PROBABILITIES.keys()) == expected_keys


# ---------------------------------------------------------------------------
# calculate_weighted_value
# ---------------------------------------------------------------------------

class TestCalculateWeightedValue:
    def test_override_takes_precedence(self):
        """weighted_value_override_eur set -> return override"""
        opp = _make_opp(weighted_value_override_eur=55_000.0)
        assert calculate_weighted_value(opp, 0.5) == 55_000.0

    def test_calculated_from_expected_and_probability(self):
        """No override -> expected_value_eur * probability"""
        opp = _make_opp(expected_value_eur=100_000.0)
        assert calculate_weighted_value(opp, 0.3) == pytest.approx(30_000.0)

    def test_zero_probability(self):
        opp = _make_opp(expected_value_eur=100_000.0)
        assert calculate_weighted_value(opp, 0.0) == 0.0
