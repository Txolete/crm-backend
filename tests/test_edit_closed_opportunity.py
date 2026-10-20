"""
Regresion: editar una oportunidad YA GANADA desde la ficha.

La ficha manda siempre stage_id (aunque no se toque) + expected_value_eur. Antes:
  1. el backend lo trataba como "acaba de cerrarse" y reescribia close_date = hoy
     (el cierre saltaba al mes actual);
  2. solo se actualizaba expected_value_eur, pero el KPI de EUR cerrado suma
     won_value_eur, asi que el importe nuevo nunca llegaba al dashboard.
"""
from datetime import datetime, timezone

import pytest

from app.models.account import Account
from app.models.config import CfgStage
from app.models.opportunity import Opportunity
from app.models.user import User
from app.main import app
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import generate_id, get_utc_now

ORIGINAL_CLOSE = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture()
def setup(db_session):
    now = get_utc_now()
    user = User(id=generate_id(), name="Admin", email=f"{generate_id()}@t.test", password_hash="x",
                role="admin", is_active=1, created_at=now, updated_at=now)
    acc = Account(id=generate_id(), name="ALTNO TEST", status="active", created_at=now, updated_at=now)
    open_stage = CfgStage(id=generate_id(), key=f"new-{generate_id()[:6]}", name="Nuevo", sort_order=1,
                          outcome="open", is_terminal=0, is_active=1, created_at=now, updated_at=now)
    won_stage = CfgStage(id=generate_id(), key=f"won-{generate_id()[:6]}", name="Ganado", sort_order=6,
                         outcome="won", is_terminal=1, is_active=1, created_at=now, updated_at=now)
    db_session.add_all([user, acc, open_stage, won_stage])
    db_session.flush()
    opp = Opportunity(id=generate_id(), account_id=acc.id, name="Opp ganada", stage_id=won_stage.id,
                      expected_value_eur=10_000.0, close_outcome="won", close_date=ORIGINAL_CLOSE,
                      won_value_eur=10_000.0, status="active", created_at=now, updated_at=now)
    db_session.add(opp)
    db_session.flush()
    app.dependency_overrides[get_current_user_from_cookie] = lambda: user
    yield opp, open_stage, won_stage
    app.dependency_overrides.pop(get_current_user_from_cookie, None)


def _same_naive_utc(a, b):
    return a.replace(tzinfo=None) == b.replace(tzinfo=None)


def test_editing_value_of_won_opp_keeps_original_close_date(client, db_session, setup):
    opp, _, won_stage = setup
    # Exactamente lo que manda la ficha: mismo stage_id + nuevo valor
    r = client.put(f"/opportunities/{opp.id}", json={"stage_id": won_stage.id, "expected_value_eur": 25_000.0})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert _same_naive_utc(opp.close_date, ORIGINAL_CLOSE), "close_date no debe moverse al editar el valor"
    assert opp.close_outcome == "won"


def test_editing_value_of_won_opp_updates_closed_amount(client, db_session, setup):
    opp, _, won_stage = setup
    r = client.put(f"/opportunities/{opp.id}", json={"stage_id": won_stage.id, "expected_value_eur": 25_000.0})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert opp.expected_value_eur == 25_000.0
    assert opp.won_value_eur == 25_000.0, "el KPI de EUR cerrado suma won_value_eur"


def test_saving_without_changing_value_keeps_custom_won_value(client, db_session, setup):
    """won_value distinto de expected (importe confirmado al cerrar) no se pisa si el valor no cambia."""
    opp, _, won_stage = setup
    opp.won_value_eur = 12_345.0
    db_session.flush()
    r = client.put(f"/opportunities/{opp.id}", json={"stage_id": won_stage.id, "expected_value_eur": 10_000.0})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert opp.won_value_eur == 12_345.0


def test_moving_open_opp_to_won_still_closes_with_today(client, db_session, setup):
    """El auto-cierre legitimo (cambio real de stage) sigue funcionando."""
    opp, open_stage, won_stage = setup
    opp.stage_id = open_stage.id
    opp.close_outcome, opp.close_date, opp.won_value_eur = "open", None, None
    db_session.flush()
    r = client.put(f"/opportunities/{opp.id}", json={"stage_id": won_stage.id})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert opp.close_outcome == "won"
    assert opp.close_date is not None and opp.close_date.year >= 2026
    assert opp.won_value_eur == 10_000.0


def test_reopening_by_changing_stage_still_works(client, db_session, setup):
    opp, open_stage, _ = setup
    r = client.put(f"/opportunities/{opp.id}", json={"stage_id": open_stage.id})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert opp.close_outcome == "open"
    assert opp.close_date is None
    assert opp.won_value_eur is None


# ---------------------------------------------------------------------------
# Reparacion de datos: localizar y restaurar cierres que ya se movieron al mes actual
# ---------------------------------------------------------------------------

def _simulate_moved_close(db_session, opp):
    """Estado tras el bug: cerrada en junio (hay audit + actividad), pero close_date = octubre."""
    from app.models.opportunity import Activity
    from app.utils.audit import create_audit_log
    create_audit_log(db=db_session, entity="opportunities", entity_id=opp.id, action="close_won",
                     user_id=None, before_data={"close_outcome": "open"},
                     after_data={"close_outcome": "won", "close_date": ORIGINAL_CLOSE})
    db_session.add(Activity(id=generate_id(), opportunity_id=opp.id, type="won", occurred_at=ORIGINAL_CLOSE,
                            summary="GANADA", created_at=ORIGINAL_CLOSE))
    opp.close_date = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)
    db_session.flush()


def test_audit_endpoint_flags_moved_close_and_suggests_original(client, db_session, setup):
    opp, _, _ = setup
    _simulate_moved_close(db_session, opp)
    r = client.get("/admin/system/closed-won-audit?month=2026-10")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1 and body["sospechosas"] == 1
    item = body["oportunidades"][0]
    assert item["sospechosa"] is True
    assert item["fecha_original_sugerida"].startswith("2026-06-15")
    assert item["account"] == "ALTNO TEST"


def test_audit_endpoint_does_not_flag_genuine_october_close(client, db_session, setup):
    opp, _, _ = setup
    opp.close_date = datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)   # cierre real de octubre, sin historial previo
    db_session.flush()
    body = client.get("/admin/system/closed-won-audit?month=2026-10").json()
    assert body["total"] == 1 and body["sospechosas"] == 0


def test_restore_close_dates_dry_run_then_commit(client, db_session, setup):
    opp, _, _ = setup
    _simulate_moved_close(db_session, opp)
    payload = {"items": [{"opportunity_id": opp.id, "close_date": "2026-06-15"}]}

    dry = client.post("/admin/system/restore-close-dates", json=payload)
    assert dry.status_code == 200 and dry.json()["dry_run"] is True
    db_session.refresh(opp)
    assert opp.close_date.month == 10, "la simulacion no debe cambiar nada"

    real = client.post("/admin/system/restore-close-dates?commit=true", json=payload)
    assert real.status_code == 200 and real.json()["dry_run"] is False
    db_session.refresh(opp)
    assert (opp.close_date.year, opp.close_date.month, opp.close_date.day) == (2026, 6, 15)
    assert opp.won_value_eur == 10_000.0, "solo cambia la fecha, no los importes"


def test_restore_rejects_open_opportunity(client, db_session, setup):
    opp, open_stage, _ = setup
    opp.close_outcome, opp.stage_id = "open", open_stage.id
    db_session.flush()
    r = client.post("/admin/system/restore-close-dates?commit=true",
                    json={"items": [{"opportunity_id": opp.id, "close_date": "2026-06-15"}]})
    assert r.status_code == 400


def test_restore_sets_value_and_date_together(client, db_session, setup):
    opp, _, _ = setup
    _simulate_moved_close(db_session, opp)
    opp.expected_value_eur, opp.won_value_eur = 2749.99, 2250.0
    db_session.flush()
    payload = {"items": [{"opportunity_id": opp.id, "close_date": "2026-06-19", "value_eur": 2750.0}]}

    dry = client.post("/admin/system/restore-close-dates", json=payload).json()
    assert dry["dry_run"] is True
    assert dry["cambios"][0]["despues"]["won_value_eur"] == 2750.0
    db_session.refresh(opp)
    assert opp.won_value_eur == 2250.0, "la simulacion no cambia nada"

    assert client.post("/admin/system/restore-close-dates?commit=true", json=payload).status_code == 200
    db_session.refresh(opp)
    assert (opp.close_date.month, opp.close_date.day) == (6, 19)
    assert opp.won_value_eur == 2750.0 and opp.expected_value_eur == 2750.0


def test_restore_value_only_keeps_close_date(client, db_session, setup):
    opp, _, _ = setup
    before = opp.close_date
    r = client.post("/admin/system/restore-close-dates?commit=true",
                    json={"items": [{"opportunity_id": opp.id, "value_eur": 2750.0}]})
    assert r.status_code == 200, r.text
    db_session.refresh(opp)
    assert _same_naive_utc(opp.close_date, before)
    assert opp.won_value_eur == 2750.0


def test_restore_requires_at_least_one_field(client, db_session, setup):
    opp, _, _ = setup
    r = client.post("/admin/system/restore-close-dates?commit=true", json={"items": [{"opportunity_id": opp.id}]})
    assert r.status_code == 400
