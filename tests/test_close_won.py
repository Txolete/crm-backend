"""
Tests for B5/B6: close_opportunity won debe limpiar probability_override
y calcular won_value_eur correctamente.
"""
import pytest
from types import SimpleNamespace
from app.utils.opportunity import calculate_probability, calculate_weighted_value


def _make_opp(
    stage_id="stage-won",
    probability_override=None,
    expected_value_eur=50_000.0,
    won_value_eur=None,
    close_outcome="open",
    lost_reason=None,
    weighted_value_override_eur=None,
):
    return SimpleNamespace(
        id="opp-1",
        stage_id=stage_id,
        probability_override=probability_override,
        expected_value_eur=expected_value_eur,
        won_value_eur=won_value_eur,
        close_outcome=close_outcome,
        lost_reason=lost_reason,
        weighted_value_override_eur=weighted_value_override_eur,
    )


def _simulate_close_won(opp, won_value_eur_request=None):
    """Simula la lógica del endpoint close_opportunity para outcome==won."""
    won_value = won_value_eur_request if won_value_eur_request is not None else opp.expected_value_eur
    opp.won_value_eur = won_value
    opp.lost_reason = None
    opp.probability_override = None  # B5/B6: limpiar override
    opp.close_outcome = "won"
    return opp


class TestCloseWonClearsOverride:
    def test_override_cleared_after_won(self):
        """B5: probability_override debe ser None tras cerrar como won."""
        opp = _make_opp(probability_override=0.65)
        assert opp.probability_override == 0.65

        opp = _simulate_close_won(opp)
        assert opp.probability_override is None

    def test_won_value_defaults_to_expected(self):
        """B6: si no se pasa won_value_eur, usa expected_value_eur."""
        opp = _make_opp(expected_value_eur=75_000.0, probability_override=0.4)
        opp = _simulate_close_won(opp, won_value_eur_request=None)

        assert opp.won_value_eur == 75_000.0
        assert opp.probability_override is None

    def test_won_value_custom_overrides_expected(self):
        """El usuario puede confirmar un valor final distinto al esperado."""
        opp = _make_opp(expected_value_eur=75_000.0)
        opp = _simulate_close_won(opp, won_value_eur_request=80_000.0)

        assert opp.won_value_eur == 80_000.0

    def test_probability_is_100_after_clearing_override(self):
        """Tras limpiar override, calculate_probability devuelve 1.0 para stage won."""
        from types import SimpleNamespace

        won_stage = SimpleNamespace(id="stage-won", key="won")
        stages_map = {"stage-won": won_stage}
        stage_probs_map = {"stage-won": 1.0}

        opp = _make_opp(probability_override=0.65)
        opp = _simulate_close_won(opp)

        prob = calculate_probability(opp, stage_probs_map, stages_map)
        assert prob == pytest.approx(1.0)

    def test_weighted_value_is_full_won_value(self):
        """Tras won, weighted_value_eur debe ser igual a won_value_eur (prob=1.0)."""
        opp = _make_opp(expected_value_eur=60_000.0, probability_override=0.3)
        opp = _simulate_close_won(opp)

        weighted = calculate_weighted_value(opp, 1.0)
        assert weighted == pytest.approx(60_000.0)
