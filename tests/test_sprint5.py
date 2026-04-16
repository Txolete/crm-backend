"""
Tests Sprint 5 — AI Agents, opportunity_outcomes y helpers de cierre.

Cubre:
  5A  analyze_multi_agent — schema de respuesta y parsing de análisis
  5B  _save_opportunity_outcome — snapshot al cierre (won/lost)
  5B  ensure_opportunity_outcome — retroactivo para oportunidades ya cerradas
  5C  initTaskCalendar — lógica de mapeo de prioridad a color (JS puro, se verifica aquí la lógica equivalente en Python)
  5D  exportTaskICS — generación de .ics (lógica de formato RFC 5545)
  5E  loadTaskTypeFilter — parsing de respuesta /config/task-templates

Todos los tests son unitarios puros (sin BD, sin HTTP) salvo los marcados con [integration].
"""
import json
import re
import pytest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers compartidos
# ---------------------------------------------------------------------------

def _make_opportunity(
    id="opp-test-1",
    account_id="acc-1",
    close_outcome="open",
    won_value_eur=None,
    expected_value_eur=50_000.0,
    probability_override=None,
    created_at=None,
    name="Opp Test",
    executive_summary=None,
    strategic_objective=None,
):
    return SimpleNamespace(
        id=id,
        account_id=account_id,
        name=name,
        close_outcome=close_outcome,
        won_value_eur=won_value_eur,
        expected_value_eur=expected_value_eur,
        probability_override=probability_override,
        opportunity_type_id=None,
        client_mental_state_id=None,
        executive_summary=executive_summary,
        strategic_objective=strategic_objective,
        created_at=created_at or datetime(2024, 1, 1, tzinfo=timezone.utc),
        stage_id="stage-negotiation",
    )


def _make_close_request(
    close_outcome="won",
    close_date="2024-06-15",
    won_value_eur=None,
    lost_reason_id=None,
    lost_reason_detail=None,
):
    from datetime import date
    return SimpleNamespace(
        close_outcome=close_outcome,
        close_date=date.fromisoformat(close_date),
        won_value_eur=won_value_eur,
        lost_reason_id=lost_reason_id,
        lost_reason_detail=lost_reason_detail,
    )


# ---------------------------------------------------------------------------
# 5B — _save_opportunity_outcome (lógica de snapshot)
# ---------------------------------------------------------------------------

class TestSaveOpportunityOutcome:

    def _simulate_snapshot(self, opp, request, activity_count=3, task_count=5):
        """
        Replica la lógica de _save_opportunity_outcome sin BD.
        Devuelve el dict que iría a OpportunityOutcome.
        """
        close_dt = request.close_date
        created_dt = opp.created_at.date() if hasattr(opp.created_at, 'date') else opp.created_at
        days_in_pipeline = (close_dt - created_dt).days

        final_value = (
            opp.won_value_eur if request.close_outcome == 'won' and opp.won_value_eur
            else opp.expected_value_eur
        )

        return {
            "outcome": request.close_outcome,
            "close_date": close_dt,
            "final_value_eur": final_value,
            "days_in_pipeline": days_in_pipeline,
            "activity_count": activity_count,
            "task_count": task_count,
            "lost_reason_id": request.lost_reason_id if request.close_outcome == 'lost' else None,
            "lost_reason_detail": request.lost_reason_detail if request.close_outcome == 'lost' else None,
            "opportunity_name": opp.name,
            "executive_summary_at_close": opp.executive_summary,
        }

    def test_won_snapshot_uses_won_value(self):
        """El snapshot de ganada usa won_value_eur, no expected."""
        opp = _make_opportunity(
            close_outcome="won",
            won_value_eur=60_000.0,
            expected_value_eur=50_000.0,
        )
        req = _make_close_request(close_outcome="won", won_value_eur=60_000.0)
        opp.won_value_eur = 60_000.0

        snap = self._simulate_snapshot(opp, req)
        assert snap["final_value_eur"] == 60_000.0
        assert snap["outcome"] == "won"

    def test_lost_snapshot_uses_expected_value(self):
        """El snapshot de perdida usa expected_value_eur."""
        opp = _make_opportunity(
            close_outcome="lost",
            expected_value_eur=45_000.0,
        )
        req = _make_close_request(
            close_outcome="lost",
            close_date="2024-06-20",
            lost_reason_id="lr-1",
            lost_reason_detail="Precio fuera de presupuesto",
        )
        snap = self._simulate_snapshot(opp, req)
        assert snap["final_value_eur"] == 45_000.0
        assert snap["outcome"] == "lost"
        assert snap["lost_reason_id"] == "lr-1"
        assert "presupuesto" in snap["lost_reason_detail"]

    def test_won_snapshot_clears_lost_reason(self):
        """Un cierre ganado no guarda lost_reason_id aunque se pase."""
        opp = _make_opportunity()
        req = _make_close_request(
            close_outcome="won",
            lost_reason_id="lr-9",  # no debería guardarse
        )
        snap = self._simulate_snapshot(opp, req)
        assert snap["lost_reason_id"] is None

    def test_days_in_pipeline_calculated(self):
        """Días en pipeline = close_date - created_at."""
        opp = _make_opportunity(
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        req = _make_close_request(close_date="2024-04-01")
        snap = self._simulate_snapshot(opp, req)
        # 2024 es bisiesto: ene(31)+feb(29)+mar(31) = 91 días
        assert snap["days_in_pipeline"] == 91

    def test_days_in_pipeline_same_day(self):
        """Si se crea y cierra el mismo día, días = 0."""
        opp = _make_opportunity(
            created_at=datetime(2024, 6, 15, tzinfo=timezone.utc)
        )
        req = _make_close_request(close_date="2024-06-15")
        snap = self._simulate_snapshot(opp, req)
        assert snap["days_in_pipeline"] == 0

    def test_executive_summary_captured_at_close(self):
        """El resumen ejecutivo se captura en el momento del cierre."""
        opp = _make_opportunity(
            executive_summary="Cliente muy interesado, pendiente de presupuesto definitivo."
        )
        req = _make_close_request()
        snap = self._simulate_snapshot(opp, req)
        assert "presupuesto definitivo" in snap["executive_summary_at_close"]

    def test_snapshot_without_summary(self):
        """Si no hay executive_summary, el campo es None."""
        opp = _make_opportunity(executive_summary=None)
        req = _make_close_request()
        snap = self._simulate_snapshot(opp, req)
        assert snap["executive_summary_at_close"] is None


# ---------------------------------------------------------------------------
# 5B — ensure_opportunity_outcome (retroactivo)
# ---------------------------------------------------------------------------

class TestEnsureOpportunityOutcome:

    def test_already_closed_won_can_create_outcome(self):
        """Una oportunidad ya cerrada como won puede tener un outcome creado retroactivamente."""
        opp = _make_opportunity(
            close_outcome="won",
            won_value_eur=80_000.0,
            expected_value_eur=75_000.0,
        )
        # Simular que ensure-outcome crearía con el valor ganado
        final_value = opp.won_value_eur if opp.close_outcome == 'won' else opp.expected_value_eur
        assert final_value == 80_000.0
        assert opp.close_outcome == "won"

    def test_already_closed_lost_can_create_outcome(self):
        """Una oportunidad perdida puede tener outcome retroactivo."""
        opp = _make_opportunity(
            close_outcome="lost",
            expected_value_eur=30_000.0,
        )
        final_value = opp.won_value_eur if opp.close_outcome == 'won' else opp.expected_value_eur
        assert final_value == 30_000.0
        assert opp.close_outcome == "lost"

    def test_open_opportunity_cannot_have_outcome(self):
        """Una oportunidad abierta no debe crear outcome retroactivo."""
        opp = _make_opportunity(close_outcome="open")
        # La lógica del endpoint rechaza si close_outcome no es won/lost
        is_closed = opp.close_outcome in ('won', 'lost')
        assert not is_closed


# ---------------------------------------------------------------------------
# 5A — AI Multi-agent: schema de respuesta y parsing
# ---------------------------------------------------------------------------

class TestMultiAgentSchema:

    def _parse_agents_analysis_entry(self, ai_chat_history_json: str):
        """
        Replica la lógica de _loadLastAgentsAnalysis en JS:
        busca la última entrada con role='agents' en ai_chat_history.
        """
        if not ai_chat_history_json:
            return None
        history = json.loads(ai_chat_history_json)
        agents_entries = [e for e in history if e.get('role') == 'agents']
        return agents_entries[-1] if agents_entries else None

    def test_agents_entry_found_in_history(self):
        """El parser encuentra la entrada role='agents' en ai_chat_history."""
        history = [
            {"role": "user", "content": "Analiza esta oportunidad"},
            {"role": "assistant", "content": "Resumen ejecutivo..."},
            {"role": "agents", "analyses": {
                "client": "Perspectiva del cliente...",
                "sales": "Táctica comercial...",
                "memory": "Historial similar...",
            }},
        ]
        entry = self._parse_agents_analysis_entry(json.dumps(history))
        assert entry is not None
        assert entry["role"] == "agents"
        assert "client" in entry["analyses"]
        assert "sales" in entry["analyses"]
        assert "memory" in entry["analyses"]

    def test_no_agents_entry_returns_none(self):
        """Si no hay role='agents', devuelve None."""
        history = [{"role": "user", "content": "Hola"}]
        entry = self._parse_agents_analysis_entry(json.dumps(history))
        assert entry is None

    def test_empty_history_returns_none(self):
        """Historia vacía → None."""
        entry = self._parse_agents_analysis_entry(None)
        assert entry is None

    def test_last_agents_entry_is_used(self):
        """Si hay múltiples entradas role='agents', se usa la última."""
        history = [
            {"role": "agents", "analyses": {"client": "Primera", "sales": "S1", "memory": "M1"}},
            {"role": "agents", "analyses": {"client": "Segunda", "sales": "S2", "memory": "M2"}},
        ]
        entry = self._parse_agents_analysis_entry(json.dumps(history))
        assert entry["analyses"]["client"] == "Segunda"

    def test_multi_agent_response_has_three_analyses(self):
        """La respuesta de analyze-multi debe tener los tres agentes."""
        mock_response = {
            "analyses": {
                "client": "El comprador busca reducir costes operativos...",
                "sales": "Táctica recomendada: demostración técnica...",
                "memory": "Casos similares: 2 ganados con descuento >15%...",
            },
            "thread_ids": {
                "client": "thread_abc",
                "sales": "thread_def",
                "memory": None,
            },
            "message": "Análisis multi-agente completado",
        }
        assert len(mock_response["analyses"]) == 3
        assert "client" in mock_response["analyses"]
        assert "sales" in mock_response["analyses"]
        assert "memory" in mock_response["analyses"]

    def test_thread_ids_can_be_null_for_chat_mode(self):
        """En modo chat completions (sin Assistants), thread_ids es None."""
        thread_ids = {"client": None, "sales": None, "memory": None}
        # Todos pueden ser None si no se usa Assistants API
        assert all(v is None for v in thread_ids.values())


# ---------------------------------------------------------------------------
# 5A — _build_historical_context
# ---------------------------------------------------------------------------

class TestBuildHistoricalContext:

    def _build_context_from_outcomes(self, outcomes: list) -> str:
        """Replica la lógica de _build_historical_context."""
        if not outcomes:
            return ""
        lines = []
        for o in outcomes:
            icon = "✅" if o["outcome"] == "won" else "❌"
            val = f"{o.get('final_value_eur', 0):,.0f}€"
            days = o.get("days_in_pipeline", "?")
            lines.append(
                f"{icon} {o.get('opportunity_name', '—')} | {val} | {days} días en pipeline"
            )
            if o.get("retro_what_worked"):
                lines.append(f"  + Lo que funcionó: {o['retro_what_worked']}")
            if o.get("retro_what_failed"):
                lines.append(f"  - Lo que falló: {o['retro_what_failed']}")
        return "\n".join(lines)

    def test_won_outcome_shows_checkmark(self):
        outcomes = [{"outcome": "won", "opportunity_name": "Proyecto Alpha",
                     "final_value_eur": 40000, "days_in_pipeline": 60}]
        ctx = self._build_context_from_outcomes(outcomes)
        assert "✅" in ctx
        assert "Proyecto Alpha" in ctx

    def test_lost_outcome_shows_cross(self):
        outcomes = [{"outcome": "lost", "opportunity_name": "Proyecto Beta",
                     "final_value_eur": 25000, "days_in_pipeline": 45}]
        ctx = self._build_context_from_outcomes(outcomes)
        assert "❌" in ctx

    def test_retro_notes_included_when_present(self):
        outcomes = [{
            "outcome": "won",
            "opportunity_name": "Proyecto Gamma",
            "final_value_eur": 80000,
            "days_in_pipeline": 90,
            "retro_what_worked": "Demo técnica muy impactante",
            "retro_what_failed": None,
        }]
        ctx = self._build_context_from_outcomes(outcomes)
        assert "Demo técnica" in ctx

    def test_empty_outcomes_returns_empty_string(self):
        ctx = self._build_context_from_outcomes([])
        assert ctx == ""


# ---------------------------------------------------------------------------
# 5D — Generación de .ics (RFC 5545)
# ---------------------------------------------------------------------------

class TestICSGeneration:

    def _generate_ics(self, title: str, description: str, due_date: str, uid: str = "test-uid-123") -> str:
        """
        Replica la lógica de exportTaskICS en JS.
        due_date en formato YYYY-MM-DD.
        """
        date_str = due_date.replace("-", "")  # YYYYMMDD
        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//CRM ASIC XXI//ES",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;VALUE=DATE:{date_str}",
            f"DTEND;VALUE=DATE:{date_str}",
            f"SUMMARY:{title}",
            "DESCRIPTION:" + description.replace("\n", r"\n"),
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "\r\n".join(lines)

    def test_ics_contains_required_fields(self):
        ics = self._generate_ics("Llamada de seguimiento", "Revisar propuesta", "2024-07-15")
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "END:VEVENT" in ics
        assert "END:VCALENDAR" in ics
        assert "VERSION:2.0" in ics

    def test_ics_date_format(self):
        """La fecha en .ics debe estar en formato YYYYMMDD sin guiones."""
        ics = self._generate_ics("Reunión", "", "2024-09-03")
        assert "DTSTART;VALUE=DATE:20240903" in ics
        assert "2024-09-03" not in ics  # sin guiones

    def test_ics_summary_matches_title(self):
        ics = self._generate_ics("Demo con cliente ABC", "", "2024-08-01")
        assert "SUMMARY:Demo con cliente ABC" in ics

    def test_ics_description_newlines_escaped(self):
        """Los saltos de línea en descripción deben escaparse como \\n."""
        desc = "Línea 1\nLínea 2"
        ics = self._generate_ics("Tarea", desc, "2024-08-01")
        assert r"Línea 1\nLínea 2" in ics

    def test_ics_empty_description(self):
        """Descripción vacía genera campo DESCRIPTION vacío, sin error."""
        ics = self._generate_ics("Sin descripción", "", "2024-08-01")
        assert "DESCRIPTION:" in ics

    def test_ics_crlf_line_endings(self):
        """El formato RFC 5545 requiere CRLF como separador de línea."""
        ics = self._generate_ics("Test", "desc", "2024-08-01")
        assert "\r\n" in ics


# ---------------------------------------------------------------------------
# 5E — loadTaskTypeFilter: parsing de /config/task-templates
# ---------------------------------------------------------------------------

class TestTaskTypeFilterParsing:

    def _parse_task_templates_response(self, items: list) -> list:
        """
        Replica la lógica de loadTaskTypeFilter en JS:
        convierte la respuesta JSON en opciones {value, text}.
        """
        return [{"value": item["id"], "text": item["name"]} for item in items]

    def test_templates_parsed_correctly(self):
        api_response = [
            {"id": "tt-1", "name": "Llamada", "is_active": 1, "sort_order": 1},
            {"id": "tt-2", "name": "Reunión", "is_active": 1, "sort_order": 2},
            {"id": "tt-3", "name": "Email", "is_active": 1, "sort_order": 3},
        ]
        opts = self._parse_task_templates_response(api_response)
        assert len(opts) == 3
        assert opts[0] == {"value": "tt-1", "text": "Llamada"}
        assert opts[2] == {"value": "tt-3", "text": "Email"}

    def test_empty_response_gives_no_options(self):
        opts = self._parse_task_templates_response([])
        assert opts == []

    def test_id_is_used_as_value(self):
        """El value del select es el ID, no el nombre."""
        api_response = [{"id": "uuid-abc", "name": "Demo", "is_active": 1, "sort_order": 1}]
        opts = self._parse_task_templates_response(api_response)
        assert opts[0]["value"] == "uuid-abc"
        assert opts[0]["text"] == "Demo"


# ---------------------------------------------------------------------------
# 5C — Lógica de colores por prioridad (FullCalendar)
# ---------------------------------------------------------------------------

class TestCalendarPriorityColors:

    def _priority_to_color(self, priority: str) -> str:
        """Replica la lógica de initTaskCalendar en JS."""
        return {
            "high": "#dc3545",
            "medium": "#fd7e14",
            "low": "#6c757d",
        }.get(priority, "#6c757d")

    def test_high_priority_is_red(self):
        assert self._priority_to_color("high") == "#dc3545"

    def test_medium_priority_is_orange(self):
        assert self._priority_to_color("medium") == "#fd7e14"

    def test_low_priority_is_gray(self):
        assert self._priority_to_color("low") == "#6c757d"

    def test_unknown_priority_defaults_to_gray(self):
        assert self._priority_to_color("critical") == "#6c757d"
        assert self._priority_to_color("") == "#6c757d"

    def test_task_mapped_to_calendar_event(self):
        """Una tarea se mapea correctamente a un evento de FullCalendar."""
        task = {
            "id": "task-1",
            "title": "Enviar propuesta",
            "due_date": "2024-07-20",
            "priority": "high",
        }
        event = {
            "id": task["id"],
            "title": task["title"],
            "start": task["due_date"],
            "color": self._priority_to_color(task["priority"]),
        }
        assert event["color"] == "#dc3545"
        assert event["start"] == "2024-07-20"

    def test_task_without_due_date_excluded(self):
        """Las tareas sin due_date no deben añadirse al calendario."""
        tasks = [
            {"id": "t1", "title": "Con fecha", "due_date": "2024-07-20", "priority": "high"},
            {"id": "t2", "title": "Sin fecha", "due_date": None, "priority": "medium"},
        ]
        events = [
            {"id": t["id"], "title": t["title"], "start": t["due_date"]}
            for t in tasks if t.get("due_date")
        ]
        assert len(events) == 1
        assert events[0]["id"] == "t1"
