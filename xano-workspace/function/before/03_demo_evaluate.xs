// Bound to explicit Gate enum input.
// Post-schema binding: preprocedure_evidence_status.
// Gate revision binding: fail-closed typed evidence.
// Dependency order: demo_evaluate is compiled before its callers.
// Creates/resets only synthetic demo evidence, then invokes the same persisted Gate path as public encounters.
function before_v1_demo_evaluate {
  input {
  }

  stack {
    db.query clinic {
      where = $db.clinic.synthetic_key == "SYN-CLINIC-001"
      return = {type: "single"}
    } as $clinic

    var $clinic_id {

      value = $clinic|get:"id":null

    }
    conditional {
      if ($clinic == null) {
        db.add clinic {
          data = {
            created_at    : "now"
            synthetic_key : "SYN-CLINIC-001"
            name          : "Synthetic BEFORE Clinic"
            state         : "TX"
            license_no    : "SYN-TX-CLINIC-001"
            synthetic     : true
          }
        } as $created_clinic
        var.update $clinic_id {
          value = $created_clinic.id
        }
      }
    }

    db.query provider {
      where = $db.provider.synthetic_key == "SYN-PROVIDER-BLOCKED-001"
      return = {type: "single"}
    } as $provider

    var $provider_id {

      value = $provider|get:"id":null

    }
    conditional {
      if ($provider == null) {
        db.add provider {
          data = {
            created_at         : "now"
            synthetic_key      : "SYN-PROVIDER-BLOCKED-001"
            clinic_id          : $clinic_id
            name               : "Synthetic Demo Provider"
            credential_type    : "AESTHETICIAN"
            license_no         : "SYN-TX-PROVIDER-001"
            license_state      : "TX"
            license_status     : "ACTIVE"
            license_expires    : "2027-12-31"
            board_status       : "CLEAR"
            evidence_confidence: "HIGH"
            synthetic          : true
          }
        } as $created_provider
        var.update $provider_id {
          value = $created_provider.id
        }
      }
      else {
        db.edit provider {
          field_name = "id"
          field_value = $provider|get:"id":null
          data = {
            clinic_id          : $clinic_id
            credential_type    : "AESTHETICIAN"
            license_state      : "TX"
            license_status     : "ACTIVE"
            license_expires    : "2027-12-31"
            board_status       : "CLEAR"
            evidence_confidence: "HIGH"
            synthetic          : true
          }
        } as $reset_provider
      }
    }

    db.query authority_evidence {
      where = $db.authority_evidence.provider_id == $provider_id
      return = {type: "single"}
    } as $authority

    conditional {
      if ($authority == null) {
        db.add authority_evidence {
          data = {
            created_at                              : "now"
            provider_id                             : $provider_id
            training_documented                     : false
            complication_training                   : false
            delegation_agreement_id                 : ""
            protocol_id                             : ""
            delegating_physician_active             : false
            patient_specific_order_present          : false
            order_contains_drug_dose_strength_route : false
            bls_current                             : false
            supervisor_onsite                       : false
            supervisor_immediately_available        : false
            physician_emergency_appointment_available: false
            verified_at                             : "now"
            confidence                              : "HIGH"
          }
        } as $created_authority
      }
      else {
        db.edit authority_evidence {
          field_name = "id"
          field_value = $authority.id
          data = {
            training_documented                     : false
            complication_training                   : false
            delegation_agreement_id                 : ""
            protocol_id                             : ""
            delegating_physician_active             : false
            patient_specific_order_present          : false
            order_contains_drug_dose_strength_route : false
            bls_current                             : false
            supervisor_onsite                       : false
            supervisor_immediately_available        : false
            physician_emergency_appointment_available: false
            verified_at                             : "now"
            confidence                              : "HIGH"
          }
        } as $reset_authority
      }
    }

    db.query procedure {
      where = $db.procedure.code == "TX_NEUROTOXIN_INJECTION"
      return = {type: "single"}
    } as $procedure

    var $procedure_id {

      value = $procedure|get:"id":null

    }
    conditional {
      if ($procedure == null) {
        db.add procedure {
          data = {
            created_at                 : "now"
            code                       : "TX_NEUROTOXIN_INJECTION"
            name                       : "Synthetic neurotoxin injection"
            category                   : "NEUROTOXIN"
            requires_patient_order     : true
            requires_protocol          : true
            requires_good_faith_exam   : true
            active                     : true
          }
        } as $created_procedure
        var.update $procedure_id {
          value = $created_procedure.id
        }
      }
    }

    var $rule_snapshot {
      value = {
        rule_id                        : "TX-NEUROTOXIN-2026-08-20"
        state                          : "TX"
        procedure_category             : "NEUROTOXIN"
        direct_performer_credentials   : ["PHYSICIAN"]
        delegated_path_credentials     : ["RN", "APRN", "PA"]
        credential_interpretation_review: ["AESTHETICIAN", "LVN", "OTHER"]
        required_evidence               : ["provider_license", "authority_pathway", "delegation_and_supervision", "preprocedure_assessment", "product_lot", "comprehension", "board_status"]
        supervision_model               : "Evidence-backed human review"
        citations                       : {
          provider_license          : ["https://www.bon.texas.gov/faq_nursing_practice.asp.html"]
          authority_pathway         : ["https://www.sos.state.tx.us/texreg/archive/January102025/Adopted%20Rules/22.EXAMINING%20BOARDS.html", "https://statutes.capitol.texas.gov/docs/OC/pdf/OC.157.pdf"]
          delegation_and_supervision: ["https://www.sos.state.tx.us/texreg/archive/January102025/Adopted%20Rules/22.EXAMINING%20BOARDS.html", "https://www.bon.texas.gov/faq_nursing_practice.asp.html", "https://statutes.capitol.texas.gov/docs/OC/pdf/OC.157.pdf"]
          preprocedure_assessment   : ["https://www.sos.state.tx.us/texreg/archive/January102025/Adopted%20Rules/22.EXAMINING%20BOARDS.html"]
          product_lot               : ["https://www.fda.gov/drugs/drug-alerts-and-statements/counterfeit-version-botox-found-multiple-states"]
          comprehension             : ["https://www.ahrq.gov/health-literacy/professional-training/informed-choice/audio-script.html"]
          board_status              : ["https://www.bon.texas.gov/faq_nursing_practice.asp.html"]
        }
      }
    }

    var $canonical_rule_snapshot {
      value = $rule_snapshot|json_encode
    }
    var $rule_snapshot_sha256 {
      value = $canonical_rule_snapshot|sha256:true|bin2hex
    }

    db.query jurisdiction_rule {
      where = $db.jurisdiction_rule.rule_id == "TX-NEUROTOXIN-2026-08-20"
      return = {type: "single"}
    } as $rule

    conditional {
      if ($rule == null) {
        db.add jurisdiction_rule {
          data = {
            created_at                     : "now"
            rule_id                        : "TX-NEUROTOXIN-2026-08-20"
            state                          : "TX"
            procedure_category             : "NEUROTOXIN"
            direct_performer_credentials   : $rule_snapshot.direct_performer_credentials
            delegated_path_credentials     : $rule_snapshot.delegated_path_credentials
            credential_interpretation_review: $rule_snapshot.credential_interpretation_review
            required_evidence               : $rule_snapshot.required_evidence
            supervision_model               : $rule_snapshot.supervision_model
            citation_urls                   : $rule_snapshot.citations
            source                          : "Human-reviewed Texas primary sources"
            verified_at                     : "now"
            confidence                      : "HIGH"
            rule_snapshot                   : $rule_snapshot
            canonical_rule_snapshot         : $canonical_rule_snapshot
            rule_snapshot_sha256            : $rule_snapshot_sha256
            active                          : true
          }
        } as $created_rule
      }
    }

    security.create_uuid as $encounter_uuid

    db.add encounter {
      data = {
        created_at      : "now"
        public_id       : "SYN-ENC-" ~ $encounter_uuid
        clinic_id       : $clinic_id
        patient_id      : "SYN-PATIENT-001"
        provider_id     : $provider_id
        procedure_id    : $procedure_id
        scheduled_at    : "2026-08-25 15:00:00+0000"
        state           : "DRAFT"
        patient_flags   : {
          practitioner_patient_relationship_established: false
          adequate_medical_record_present               : false
          performer_identity_disclosed                  : false
        }
        practitioner_patient_relationship_established: false
        adequate_medical_record_present               : false
        performer_identity_disclosed                  : false
        preprocedure_evidence_status                  : "MISSING"
        version         : 0
        synthetic       : true
      }
    } as $encounter

    db.add product_lot {
      data = {
        created_at  : "now"
        encounter_id: $encounter.id
        brand       : "Synthetic Neurotoxin"
        lot_no      : "SYN-LOT-001"
        expiry      : "2027-06-30"
        alert_status: "MATCHED_TO_NO_CAPTURED_ALERT"
        confidence  : "HIGH"
        checked_at  : "now"
        source_refs : ["synthetic-cache://serpapi/product-alerts"]
      }
    } as $product_lot

    db.add comprehension {
      data = {
        created_at             : "now"
        encounter_id           : $encounter.id
        question_set_version   : "SYN-TEACHBACK-1"
        rule_snapshot_sha256   : $rule_snapshot_sha256
        items                  : [{id: "SYN-Q1", passed: true}]
        score                  : 4
        threshold              : 4
        passed                 : true
        attempts               : 1
        confidence             : "HIGH"
        completed_at           : "now"
      }
    } as $comprehension

    function.run before_v1_transition {
      input = {
        encounter_id: $encounter.id
        to_state    : "EVIDENCE_PENDING"
        actor       : "Synthetic demo"
        action      : "encounter_opened"
        reason      : "Synthetic demo encounter booked with evidence ready for evaluation."
        payload     : {public_id: $encounter.public_id}
      }
    } as $opened

    function.run before_v1_evaluate_encounter {
      input = {encounter_id: $encounter.id, actor: "Synthetic demo"}
    } as $result
  }

  response = $result
  tags = ["before", "demo", "synthetic-only"]
  guid = "cT8-KZHGIaL50giYhxsVudsqP-E"
}
