# Texas neurotoxin authority — primary-source foundation

Verified 2026-08-18. Scope: Texas, nonsurgical cosmetic neurotoxin injection.
This is a source map for a human-reviewed safety workflow, not legal advice.

## The source-backed answer

Texas does **not** publish a closed credential list for cosmetic injectors. Texas
Occupations Code §157.001 permits a physician to delegate a medical act to a
qualified, properly trained person under the physician's supervision when the
physician determines it can be performed safely, it is performed customarily,
and no other statute is violated. The physician remains responsible. Effective
January 9, 2025, 22 TAC §169.25 expressly classifies cosmetic injections as
medical acts that can be delegated and supervised.

| Performer path | What the primary sources support | Gate treatment |
|---|---|---|
| Texas physician | May perform within medical practice and standard of care. | Direct path, subject to active licence and other safety evidence. |
| PA | §169.25(b) recognizes a PA acting under physician supervision at the physician's practice. | Delegated/supervised path. |
| APRN | No full practice authority. Cosmetic diagnosis, ordering, and Botox/Restylane require physician delegation; role and population focus still limit scope. | Delegated path; role/population mismatch or missing prescriptive authority is `REVIEW`/`BLOCKED` as the evidence warrants. |
| RN | BON gives no blanket yes/no. The individual RN must determine scope based on education, competence, ability to manage complications, an appropriate patient order (including dose/strength/route), and appropriate medical supervision. | May clear only when every one of those facts and Chapter 169 evidence is documented. |
| LVN | BON likewise requires individual scope, education/competence, an appropriate order, nursing and medical supervision. | Not implemented as a clear hero path; unresolved evidence routes to `REVIEW`. |
| Aesthetician or other title | §157.001/§169.25 use “qualified and properly trained person,” but delegation must not violate another statute. The two requested boards do not resolve how a cosmetology licence interacts with this delegation in every fact pattern. | **REVIEW on title alone.** Missing training, order, protocol, or supervision can still produce an evidence-backed `BLOCKED` encounter. |

The prior task language—`credential ∈ permitted_credentials`—was therefore not
safe to implement. The seed now distinguishes a direct physician path, reviewed
delegated paths, and credential titles requiring interpretation.

## Supervision and encounter prerequisites

Under 22 TAC §169.26, the delegating physician must ensure the performer has
training in technique and pre/post care, infection control, contraindications,
and recognition/acute management of complications; the performer must sign and
date a written protocol. Before the act, a physician, PA, or APRN acting under
physician delegation must establish the practitioner-patient relationship,
maintain an adequate medical record, disclose the performer's identity/title,
and ensure someone trained in BLS is present while the patient is onsite.

During the procedure, a physician, PA, or APRN must be onsite **or** immediately
available for emergency consultation; if necessary, the physician must be able
to conduct an emergency appointment. Calling this simply `ONSITE` would be wrong,
so the seed uses `ONSITE_OR_IMMEDIATELY_AVAILABLE`.

## Which document is required?

Two concepts must not be collapsed:

1. For a delegated cosmetic act, §169.27 requires a physician-developed written
   order or a facility order reviewed and approved in writing by the physician.
   It must identify the delegating physician and contain patient-selection
   criteria, appropriate-care instructions, complication/injury/emergency
   procedures, and a feedback route to the physician/PA/APRN. Section 169.26
   separately requires the performer to sign and date a written protocol.
2. If an APRN or PA is delegated authority to **prescribe/order** the drug, Texas
   Occupations Code §157.0512 requires a prescriptive authority agreement. TMB's
   current summary lists nine minimum elements: annual written/signed/dated
   review; party identities/licences; practice and locations; permitted or
   prohibited drug/device categories; consultation/referral plan; emergency
   plan; communication process; alternate physician(s), if used; and a quality
   assurance plan with chart review and documented monthly meetings.

The RN administration hero path does not silently substitute a prescriptive
authority agreement for the patient-specific order and Chapter 169 protocol.

## Explicit REVIEW items

- **“Good-faith exam” terminology:** §169.26 expressly requires a
  practitioner-patient relationship and adequate medical record but does not use
  that label. The Gate verifies the express elements and preserves the label as
  `REVIEW`; it does not invent an extra requirement or claim none can exist.
- **Credential-only aesthetician conclusion:** requires analysis beyond the two
  boards requested, including other licensing law and the exact facts. `REVIEW`.
- **Individual RN scope:** BON says two RNs can reach different answers. A generic
  RN credential can never substitute for person-specific competence evidence.

## Primary sources

- [Texas Register: adopted 22 TAC §§169.25–169.28](https://www.sos.state.tx.us/texreg/archive/January102025/Adopted%20Rules/22.EXAMINING%20BOARDS.html)
- [Texas Occupations Code Chapter 157](https://statutes.capitol.texas.gov/docs/OC/pdf/OC.157.pdf)
- [Texas BON: Cosmetic Procedures for RNs and LVNs](https://www.bon.texas.gov/faq_nursing_practice.asp.html)
- [Texas BON: Cosmetic Procedures for APRNs](https://www.bon.texas.gov/faq_practice_aprn.asp.html)
- [Texas TMB: Prescribing and Supervision](https://www.tmb.texas.gov/index.php/apply-renew/physician/prescribing-and-supervision)

