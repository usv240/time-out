// Post-schema binding: preprocedure_evidence_status.
// Dependency order: gate is compiled before its callers.
// Pure, deterministic Texas neurotoxin Gate. No network calls and no short-circuiting.
// The result is a pre-procedure safety determination for human review, never a legality decision.
function before_v1_gate {
  input {
    json encounter
    json provider
    json authority_evidence
    json procedure
    json product_lot
    json comprehension
    json rule_snapshot
    enum preprocedure_evidence_status {
      values = ["MISSING", "COMPLETE"]
    }
  
    text canonical_rule_snapshot
  }

  stack {
    var $findings {
      value = []
    }
  
    var $has_block {
      value = false
    }
  
    var $has_review {
      value = false
    }
  
    var $provider_facts {
      value = {
        state         : $input.provider.license_state
        license_status: $input.provider.license_status
        expires_on    : $input.provider.license_expires
        scheduled_on  : $input.encounter.scheduled_on
        confidence    : $input.provider.evidence_confidence
      }
    }
  
    conditional {
      if ($input.provider.evidence_confidence == "LOW") {
        array.push $findings {
          value = {
            check_id     : "provider_license"
            status       : "REVIEW"
            summary      : "Licence evidence is low-confidence."
            citation_urls: $input.rule_snapshot.citations.provider_license
            facts        : $provider_facts
          }
        }
      
        var.update $has_review {
          value = true
        }
      }
    
      elseif ($input.provider.license_state != $input.rule_snapshot.state || $input.provider.license_status != "ACTIVE" || $input.provider.license_expires < $input.encounter.scheduled_on) {
        array.push $findings {
          value = {
            check_id     : "provider_license"
            status       : "BLOCK"
            summary      : "Provider licence evidence is not active, in-state, and unexpired."
            citation_urls: $input.rule_snapshot.citations.provider_license
            facts        : $provider_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "provider_license"
            status       : "PASS"
            summary      : "Provider licence evidence is active, in-state, and unexpired."
            citation_urls: $input.rule_snapshot.citations.provider_license
            facts        : $provider_facts
          }
        }
      }
    }
  
    var $direct_performer {
      value = $input.provider.credential_type
        |in:$input.rule_snapshot.direct_performer_credentials
    }
  
    var $delegated_performer {
      value = $input.provider.credential_type
        |in:$input.rule_snapshot.delegated_path_credentials
    }
  
    var $interpretation_review {
      value = $input.provider.credential_type
        |in:$input.rule_snapshot.credential_interpretation_review
    }
  
    var $authority_facts {
      value = {
        credential                      : $input.provider.credential_type
        training_documented             : $input.authority_evidence.training_documented
        complication_training_documented: $input.authority_evidence.complication_training
      }
    }
  
    conditional {
      if ($direct_performer) {
        array.push $findings {
          value = {
            check_id     : "authority_pathway"
            status       : "PASS"
            summary      : "Credential follows the direct physician pathway."
            citation_urls: $input.rule_snapshot.citations.authority_pathway
            facts        : $authority_facts
          }
        }
      }
    
      elseif ($interpretation_review) {
        array.push $findings {
          value = {
            check_id     : "authority_pathway"
            status       : "REVIEW"
            summary      : "This title alone neither establishes nor disproves delegated authority; reviewer must assess the other licence and delegation rules."
            citation_urls: $input.rule_snapshot.citations.authority_pathway
            facts        : $authority_facts
          }
        }
      
        var.update $has_review {
          value = true
        }
      }
    
      elseif ($delegated_performer == false) {
        array.push $findings {
          value = {
            check_id     : "authority_pathway"
            status       : "BLOCK"
            summary      : "Credential is not mapped to a reviewed Texas authority pathway."
            citation_urls: $input.rule_snapshot.citations.authority_pathway
            facts        : $authority_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      elseif ($input.authority_evidence.training_documented == false || $input.authority_evidence.complication_training == false) {
        array.push $findings {
          value = {
            check_id     : "authority_pathway"
            status       : "BLOCK"
            summary      : "Required procedure and complication-response training is not documented."
            citation_urls: $input.rule_snapshot.citations.authority_pathway
            facts        : $authority_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "authority_pathway"
            status       : "PASS"
            summary      : "Delegated-performer training evidence is documented."
            citation_urls: $input.rule_snapshot.citations.authority_pathway
            facts        : $authority_facts
          }
        }
      }
    }
  
    var $supervision_facts {
      value = {
        delegation_required                      : ($direct_performer == false)
        delegation_document_present              : ($input.authority_evidence.delegation_agreement_id != "")
        protocol_signed_and_dated                : ($input.authority_evidence.protocol_id != "")
        delegating_physician_active              : $input.authority_evidence.delegating_physician_active
        patient_specific_order_present           : $input.authority_evidence.patient_specific_order_present
        order_contains_drug_dose_strength_route  : $input.authority_evidence.order_contains_drug_dose_strength_route
        supervisor_onsite                        : $input.authority_evidence.supervisor_onsite
        supervisor_immediately_available         : $input.authority_evidence.supervisor_immediately_available
        physician_emergency_appointment_available: $input.authority_evidence.physician_emergency_appointment_available
        bls_person_present                       : $input.authority_evidence.bls_current
      }
    }
  
    conditional {
      if ($direct_performer) {
        array.push $findings {
          value = {
            check_id     : "delegation_and_supervision"
            status       : "PASS"
            summary      : "No delegation is asserted for the physician performer."
            citation_urls: $input.rule_snapshot.citations.delegation_and_supervision
            facts        : $supervision_facts
          }
        }
      }
    
      elseif ($input.authority_evidence.delegation_agreement_id != "" && $input.authority_evidence.protocol_id != "" && $input.authority_evidence.delegating_physician_active && $input.authority_evidence.patient_specific_order_present && $input.authority_evidence.order_contains_drug_dose_strength_route && $input.authority_evidence.bls_current && ($input.authority_evidence.supervisor_onsite || $input.authority_evidence.supervisor_immediately_available) && $input.authority_evidence.physician_emergency_appointment_available) {
        array.push $findings {
          value = {
            check_id     : "delegation_and_supervision"
            status       : "PASS"
            summary      : "Delegation, order, BLS, and availability evidence is complete."
            citation_urls: $input.rule_snapshot.citations.delegation_and_supervision
            facts        : $supervision_facts
          }
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "delegation_and_supervision"
            status       : "BLOCK"
            summary      : "Delegation, order, BLS, or required availability evidence is incomplete."
            citation_urls: $input.rule_snapshot.citations.delegation_and_supervision
            facts        : $supervision_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    }
  
    var $patient_flags {
      value = $input.encounter
        |get:"patient_flags":"{}"
        |json_decode
    }
  
    var $assessment_facts {
      value = {
        practitioner_patient_relationship_established: ($input.preprocedure_evidence_status == "COMPLETE")
        adequate_medical_record_present              : ($input.preprocedure_evidence_status == "COMPLETE")
        performer_identity_disclosed                 : ($input.preprocedure_evidence_status == "COMPLETE")
        good_faith_exam_label_status                 : "REVIEW"
      }
    }
  
    conditional {
      if (($input.preprocedure_evidence_status == "COMPLETE") && ($input.preprocedure_evidence_status == "COMPLETE") && ($input.preprocedure_evidence_status == "COMPLETE")) {
        array.push $findings {
          value = {
            check_id     : "preprocedure_assessment"
            status       : "PASS"
            summary      : "The explicit Chapter 169 pre-procedure evidence is present."
            citation_urls: $input.rule_snapshot.citations.preprocedure_assessment
            facts        : $assessment_facts
          }
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "preprocedure_assessment"
            status       : "BLOCK"
            summary      : "Practitioner-patient relationship, medical record, or performer disclosure evidence is missing."
            citation_urls: $input.rule_snapshot.citations.preprocedure_assessment
            facts        : $assessment_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    }
  
    var $lot_facts {
      value = {
        verified  : ($input.product_lot.lot_no != "")
        alerted   : ($input.product_lot.alert_status == "CONFIRMED_ALERT")
        confidence: $input.product_lot.confidence
      }
    }
  
    conditional {
      if ($input.product_lot.confidence == "LOW") {
        array.push $findings {
          value = {
            check_id     : "product_lot"
            status       : "REVIEW"
            summary      : "Product-lot evidence is low-confidence."
            citation_urls: $input.rule_snapshot.citations.product_lot
            facts        : $lot_facts
          }
        }
      
        var.update $has_review {
          value = true
        }
      }
    
      elseif ($input.product_lot.lot_no == "" || $input.product_lot.alert_status == "CONFIRMED_ALERT") {
        array.push $findings {
          value = {
            check_id     : "product_lot"
            status       : "BLOCK"
            summary      : "Product lot is unverified or has an active alert."
            citation_urls: $input.rule_snapshot.citations.product_lot
            facts        : $lot_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "product_lot"
            status       : "PASS"
            summary      : "Product lot is captured and has no matched alert in the captured search; this is not authenticity verification."
            citation_urls: $input.rule_snapshot.citations.product_lot
            facts        : $lot_facts
          }
        }
      }
    }
  
    var $comprehension_facts {
      value = {
        recorded  : ($input.comprehension.completed_at != null)
        score     : $input.comprehension.score
        threshold : $input.comprehension.threshold
        confidence: $input.comprehension.confidence
      }
    }
  
    conditional {
      if ($input.comprehension.confidence == "LOW") {
        array.push $findings {
          value = {
            check_id     : "comprehension"
            status       : "REVIEW"
            summary      : "Comprehension evidence is low-confidence."
            citation_urls: $input.rule_snapshot.citations.comprehension
            facts        : $comprehension_facts
          }
        }
      
        var.update $has_review {
          value = true
        }
      }
    
      elseif ($input.comprehension.completed_at == null || $input.comprehension.passed == false || $input.comprehension.score < $input.comprehension.threshold) {
        array.push $findings {
          value = {
            check_id     : "comprehension"
            status       : "BLOCK"
            summary      : "Comprehension was not recorded or did not meet the configured threshold."
            citation_urls: $input.rule_snapshot.citations.comprehension
            facts        : $comprehension_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "comprehension"
            status       : "PASS"
            summary      : "Comprehension evidence meets the configured threshold."
            citation_urls: $input.rule_snapshot.citations.comprehension
            facts        : $comprehension_facts
          }
        }
      }
    }
  
    var $discipline_facts {
      value = {disciplinary_status: $input.provider.board_status}
    }
  
    conditional {
      if ($input.provider.board_status == "CLEAR") {
        array.push $findings {
          value = {
            check_id     : "board_status"
            status       : "PASS"
            summary      : "Captured disciplinary status is clear."
            citation_urls: $input.rule_snapshot.citations.board_status
            facts        : $discipline_facts
          }
        }
      }
    
      elseif ($input.provider.board_status == "ACTION") {
        array.push $findings {
          value = {
            check_id     : "board_status"
            status       : "BLOCK"
            summary      : "Captured disciplinary status reports an action."
            citation_urls: $input.rule_snapshot.citations.board_status
            facts        : $discipline_facts
          }
        }
      
        var.update $has_block {
          value = true
        }
      }
    
      else {
        array.push $findings {
          value = {
            check_id     : "board_status"
            status       : "REVIEW"
            summary      : "Disciplinary status is unknown or stale."
            citation_urls: $input.rule_snapshot.citations.board_status
            facts        : $discipline_facts
          }
        }
      
        var.update $has_review {
          value = true
        }
      }
    }
  
    var $verdict {
      value = $has_block ? "BLOCKED" : ($has_review ? "REVIEW" : "CLEAR")
    }
  
    var $snapshot_sha256 {
      value = $input.canonical_rule_snapshot|sha256:true|bin2hex
    }
  }

  response = {
    verdict                : $verdict
    determination_scope    : "Pre-procedure safety determination for human review"
    findings               : $findings
    rule_snapshot          : $input.rule_snapshot
    canonical_rule_snapshot: $input.canonical_rule_snapshot
    rule_snapshot_sha256   : $snapshot_sha256
  }

  tags = ["before", "gate", "deterministic", "no-network"]
  guid = "jp_LJgL0n8ZND8ViDfQhd_KUIhw"
}