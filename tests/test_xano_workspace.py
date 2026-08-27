from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "xano-workspace"
SITE = ROOT / "before" / "site"


def test_current_plan_entities_are_defined_in_xano_workspace() -> None:
    expected = {
        "clinic",
        "provider",
        "authority_evidence",
        "procedure",
        "jurisdiction_rule",
        "encounter",
        "gate_decision",
        "intake_doc",
        "product_lot",
        "alert_candidate",
        "comprehension",
        "skin_baseline",
        "consent_record",
        "safety_receipt",
        "audit_event",
    }
    assert {path.stem for path in (WORKSPACE / "table").glob("*.xs")} >= expected


def test_transition_is_guarded_idempotent_and_audited() -> None:
    source = (WORKSPACE / "function" / "before_transition.xs").read_text(encoding="utf-8")
    assert "Encounter state transition is not allowed" in source
    assert "if ($is_retry == false)" in source
    assert "db.add audit_event" in source
    assert "payload_hash" in source
    assert '"READY_FOR_PROCEDURE" && ($input.to_state == "HUMAN_REVIEW"' in source


def test_evaluate_route_uses_the_shared_deterministic_gate() -> None:
    route = (WORKSPACE / "api" / "time_out_public_api" / "v_1" / "encounters" / "encounter_id" / "evaluate_POST.xs").read_text(encoding="utf-8")
    evaluator = (WORKSPACE / "function" / "before_v_1_evaluate_encounter.xs").read_text(encoding="utf-8")
    gate = (WORKSPACE / "function" / "before_v_1_gate.xs").read_text(encoding="utf-8")

    assert 'function.run before_v1_evaluate_encounter' in route
    assert 'function.run before_v1_gate' in evaluator
    assert "db.add gate_decision" in evaluator
    assert "canonical_rule_snapshot" in evaluator
    assert "preprocedure_evidence_status" in evaluator
    assert "enum preprocedure_evidence_status" in gate
    assert "api.request" not in gate
    for check_id in (
        "provider_license",
        "authority_pathway",
        "delegation_and_supervision",
        "preprocedure_assessment",
        "product_lot",
        "comprehension",
        "board_status",
    ):
        assert f'check_id     : "{check_id}"' in gate


def test_required_encounter_rest_surface_exists() -> None:
    encounters = WORKSPACE / "api" / "time_out_public_api" / "v_1"
    expected = {
        "encounters_POST.xs",   # create
        "evidence_POST.xs",
        "evaluate_POST.xs",
        "remediate_POST.xs",
        "rerun_POST.xs",
        "encounter_id_GET.xs",
    }
    assert {path.name for path in encounters.rglob("*.xs")} >= expected


def test_hosted_site_targets_xano_not_localhost() -> None:
    app = (SITE / "app.js").read_text(encoding="utf-8")
    api_page = (SITE / "api-page.js").read_text(encoding="utf-8")
    api_html = (SITE / "api.html").read_text(encoding="utf-8")
    assert "https://x6g0-xqak-a8ri.n7e.xano.io/api:before" in app
    assert "https://x6g0-xqak-a8ri.n7e.xano.io/api:before" in api_page
    assert "localhost:4173" not in api_html
