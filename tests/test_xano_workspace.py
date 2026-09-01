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


def test_absence_of_delegation_evidence_is_expressible_over_the_api() -> None:
    """An empty delegation id is how a caller says "there is no delegation document".

    Xano rejects "" for a *required* text input as a missing param, which made the two
    most important attacks — swapping in the aesthetician and deleting the delegation
    protocol — fail with HTTP 400 instead of producing a refusal. The inputs must stay
    optional so absence can be stated at all.
    """
    src = (WORKSPACE / "api" / "time_out_public_api" / "v_1" / "encounters"
           / "encounter_id" / "remediate_POST.xs").read_text(encoding="utf-8")
    for field in ("delegation_agreement_id", "protocol_id"):
        assert f"text {field}? filters=trim" in src, (
            f"{field} must be an optional input; a required text input rejects \"\" "
            f"and the absence of delegation evidence becomes unexpressible."
        )


def test_gate_treats_a_null_delegation_id_as_absent_not_present() -> None:
    """Fail closed. `null != ""` is true, so a bare != "" check reads missing as present.

    That would invert the safety default on the delegation check, which is the one the
    whole product exists to make.
    """
    src = (WORKSPACE / "function" / "before_v_1_gate.xs").read_text(encoding="utf-8")
    for field in ("delegation_agreement_id", "protocol_id"):
        for line in src.splitlines():
            if f"authority_evidence.{field} !=" in line:
                assert f"authority_evidence.{field} != null" in line, (
                    f"{field} is compared without a null guard on: {line.strip()[:110]}"
                )


def test_public_remediate_refuses_phi_shaped_input() -> None:
    """The site tells judges to send their own evidence, so the guard must be server-side.

    It originally lived only in the local dev server while /assumptions claimed PHI was
    "rejected before it reaches storage" — and the deployed API accepted an email and a
    phone number and wrote them to the audit log.

    The per-field threshold matters: counting digits across all fields together rejects
    the legitimate synthetic identifiers, which already carry ten between them.
    """
    src = (WORKSPACE / "api" / "time_out_public_api" / "v_1" / "encounters"
           / "encounter_id" / "remediate_POST.xs").read_text(encoding="utf-8")
    assert 'contains:"@"' in src, "no email check on the public remediate endpoint"
    for field in ("actor_digits", "deleg_digits", "protocol_digits", "lot_digits"):
        assert f"${field} < 9" in src, f"no per-field digit guard for {field}"
    guard = src.index("precondition (!($all_text|contains")
    body = src.index("db.get encounter {")
    assert guard < body, "the PHI guard must run before anything is read or written"
