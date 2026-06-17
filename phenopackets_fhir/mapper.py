"""
Phenopacket v2 → FHIR R4 QuestionnaireResponse mapper.

Given a Phenopacket dict (parsed from JSON/protobuf-JSON) and the
corresponding FHIR Questionnaire, this module produces a populated
QuestionnaireResponse resource.

Supported Phenopacket elements
-------------------------------
* Top-level metadata  (id, meta.created_by, meta.created)
* subject             (Individual: id, sex, date_of_birth, karyotypic_sex,
                       taxonomy, vital_status)
* phenotypic_features (type, excluded, onset, severity, modifiers)
* diseases            (term, excluded, onset, disease_stage, primary_site,
                       laterality)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .questionnaire import QUESTIONNAIRE_URL, QUESTIONNAIRE_VERSION


# ---------------------------------------------------------------------------
# Answer value constructors
# ---------------------------------------------------------------------------

def _val_str(v: str) -> dict:
    return {"valueString": v}

def _val_bool(v: bool) -> dict:
    return {"valueBoolean": v}

def _val_date(v: str) -> dict:
    # Accepts ISO 8601 date or datetime; trim to date part if needed.
    return {"valueDate": v[:10] if v else v}

def _val_datetime(v: str) -> dict:
    return {"valueDateTime": v}

def _val_coding(ontology_class: dict) -> dict:
    """Convert a Phenopacket OntologyClass {id, label} to a FHIR Coding answer."""
    # OntologyClass.id looks like "HP:0001234" or "MONDO:0007947"
    system = _ontology_system(ontology_class.get("id", ""))
    return {
        "valueCoding": {
            "system": system,
            "code": ontology_class.get("id", ""),
            "display": ontology_class.get("label", ""),
        }
    }


def _ontology_system(term_id: str) -> str:
    """Map a compact prefix to a canonical URI."""
    prefix = term_id.split(":")[0].upper() if ":" in term_id else ""
    SYSTEMS: dict[str, str] = {
        "HP":         "http://purl.obolibrary.org/obo/hp.owl",
        "MONDO":      "http://purl.obolibrary.org/obo/mondo.owl",
        "OMIM":       "https://www.omim.org",
        "NCBITAXON":  "http://purl.obolibrary.org/obo/ncbitaxon.owl",
        "ORPHA":      "http://www.orpha.net",
        "UBERON":     "http://purl.obolibrary.org/obo/uberon.owl",
        "ICD10":      "http://hl7.org/fhir/sid/icd-10",
        "ICD11":      "http://hl7.org/fhir/sid/icd-11",
        "SNOMEDCT":   "http://snomed.info/sct",
        "LOINC":      "http://loinc.org",
    }
    return SYSTEMS.get(prefix, "urn:phenopackets:ontology")


# ---------------------------------------------------------------------------
# Response item constructors
# ---------------------------------------------------------------------------

def _ri(link_id: str, text: str, answers: list[dict] | None = None,
        sub_items: list[dict] | None = None) -> dict[str, Any]:
    """Build a QuestionnaireResponse.item node."""
    node: dict[str, Any] = {"linkId": link_id, "text": text}
    if answers:
        node["answer"] = answers
    if sub_items:
        node["item"] = sub_items
    return node


# ---------------------------------------------------------------------------
# Time element resolution
# ---------------------------------------------------------------------------

def _resolve_onset(time_element: dict | None) -> tuple[dict | None, str | None, str | None]:
    """
    Return (ontology_class_answer, age_str, date_str) from a Phenopacket
    TimeElement, any of which may be None.
    """
    if not time_element:
        return None, None, None

    # OntologyClass onset (e.g. HP:0003577 Congenital onset)
    if "ontologyClass" in time_element:
        return _val_coding(time_element["ontologyClass"]), None, None

    # ISO 8601 age string  (e.g. "P2Y3M")
    if "age" in time_element:
        age_val = time_element["age"]
        if isinstance(age_val, dict):
            age_str = age_val.get("iso8601duration", "")
        else:
            age_str = str(age_val)
        return None, age_str, None

    # Age range — use start for simplicity
    if "ageRange" in time_element:
        start = time_element["ageRange"].get("start", {})
        if isinstance(start, dict):
            return None, start.get("iso8601duration"), None

    # Timestamp
    if "timestamp" in time_element:
        return None, None, time_element["timestamp"]

    # Gestational age — represent as a string note
    if "gestationalAge" in time_element:
        ga = time_element["gestationalAge"]
        weeks = ga.get("weeks", "")
        days = ga.get("days", 0)
        return None, f"GA {weeks}w{days}d", None

    return None, None, None


# ---------------------------------------------------------------------------
# Top-level element mappers
# ---------------------------------------------------------------------------

def _map_subject(subject: dict) -> dict:
    sub_items: list[dict] = []

    if subject.get("id"):
        sub_items.append(_ri("subject.id", "Patient / subject identifier",
                              [_val_str(subject["id"])]))

    if subject.get("dateOfBirth"):
        sub_items.append(_ri("subject.date_of_birth", "Date of birth",
                              [_val_date(subject["dateOfBirth"])]))

    if subject.get("sex"):
        sex_system = "https://phenopackets.org/schema/sex"
        sex_code = subject["sex"]
        sub_items.append(_ri("subject.sex", "Biological sex", [{
            "valueCoding": {"system": sex_system, "code": sex_code, "display": sex_code}
        }]))

    if subject.get("karyotypicSex"):
        ks = subject["karyotypicSex"]
        sub_items.append(_ri("subject.karyotypic_sex", "Karyotypic sex", [{
            "valueCoding": {
                "system": "https://phenopackets.org/schema/karyotypic-sex",
                "code": ks, "display": ks,
            }
        }]))

    if subject.get("taxonomy"):
        sub_items.append(_ri("subject.taxonomy", "Taxonomy (NCBITaxon)",
                              [_val_coding(subject["taxonomy"])]))

    if subject.get("vitalStatus"):
        vs = subject["vitalStatus"]
        status_code = vs.get("status", "UNKNOWN_STATUS") if isinstance(vs, dict) else str(vs)
        sub_items.append(_ri("subject.vital_status", "Vital status", [{
            "valueCoding": {
                "system": "https://phenopackets.org/schema/vital-status",
                "code": status_code, "display": status_code,
            }
        }]))

    return _ri("subject", "Subject (Individual)", sub_items=sub_items)


def _map_phenotypic_feature(pf: dict) -> dict:
    sub_items: list[dict] = []

    if pf.get("type"):
        sub_items.append(_ri("phenotypic_feature.type", "HPO term (type)",
                              [_val_coding(pf["type"])]))

    if "excluded" in pf:
        sub_items.append(_ri("phenotypic_feature.excluded",
                              "Excluded (negated observation)",
                              [_val_bool(pf["excluded"])]))

    onset_coding, onset_age, onset_date = _resolve_onset(pf.get("onset"))
    if onset_coding:
        sub_items.append(_ri("phenotypic_feature.onset_ontology",
                              "Onset (ontology class)", [onset_coding]))
    if onset_age:
        sub_items.append(_ri("phenotypic_feature.onset_age",
                              "Onset (ISO 8601 age, e.g. P2Y3M)", [_val_str(onset_age)]))
    if onset_date:
        sub_items.append(_ri("phenotypic_feature.onset_date",
                              "Onset (date)", [_val_date(onset_date)]))

    if pf.get("severity"):
        sub_items.append(_ri("phenotypic_feature.severity", "Severity (HPO)",
                              [_val_coding(pf["severity"])]))

    if pf.get("modifiers"):
        answers = [_val_coding(m) for m in pf["modifiers"]]
        sub_items.append(_ri("phenotypic_feature.modifiers",
                              "Clinical modifiers (HPO, multiple allowed)", answers))

    return _ri("phenotypic_features", "Phenotypic Features", sub_items=sub_items)


def _map_disease(disease: dict) -> dict:
    sub_items: list[dict] = []

    if disease.get("term"):
        sub_items.append(_ri("disease.term", "Disease term (MONDO / OMIM / ICD)",
                              [_val_coding(disease["term"])]))

    if "excluded" in disease:
        sub_items.append(_ri("disease.excluded", "Excluded (rule-out diagnosis)",
                              [_val_bool(disease["excluded"])]))

    onset_coding, onset_age, onset_date = _resolve_onset(disease.get("onset"))
    if onset_coding:
        sub_items.append(_ri("disease.onset_ontology", "Onset (ontology class)", [onset_coding]))
    if onset_age:
        sub_items.append(_ri("disease.onset_age", "Onset (ISO 8601 age)", [_val_str(onset_age)]))
    if onset_date:
        sub_items.append(_ri("disease.onset_date", "Onset (date)", [_val_date(onset_date)]))

    if disease.get("diseaseStage"):
        answers = [_val_coding(s) for s in disease["diseaseStage"]]
        sub_items.append(_ri("disease.disease_stage",
                              "Disease stage (e.g. TNM, cancer staging)", answers))

    if disease.get("primarySite"):
        sub_items.append(_ri("disease.primary_site", "Primary anatomical site",
                              [_val_coding(disease["primarySite"])]))

    if disease.get("laterality"):
        sub_items.append(_ri("disease.laterality", "Laterality",
                              [_val_coding(disease["laterality"])]))

    return _ri("diseases", "Diseases", sub_items=sub_items)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def phenopacket_to_response(
    phenopacket: dict[str, Any],
    questionnaire: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convert a Phenopacket v2 dict into a FHIR R4 QuestionnaireResponse dict.

    Parameters
    ----------
    phenopacket:
        Parsed Phenopacket JSON as a Python dict (protobuf-JSON or plain JSON).
    questionnaire:
        Optional: the Questionnaire dict returned by ``build_questionnaire()``.
        If provided, the response's ``questionnaire`` field will reference it.

    Returns
    -------
    dict
        A FHIR R4 QuestionnaireResponse resource.
    """
    # Build the canonical reference URL for the Questionnaire
    q_ref = (
        questionnaire.get("url", QUESTIONNAIRE_URL)
        if questionnaire
        else QUESTIONNAIRE_URL
    )
    q_version = (
        questionnaire.get("version", QUESTIONNAIRE_VERSION)
        if questionnaire
        else QUESTIONNAIRE_VERSION
    )

    # Top-level response metadata
    pp_id = phenopacket.get("id", "")
    meta = phenopacket.get("metaData", {})

    top_items: list[dict] = []

    if pp_id:
        top_items.append(_ri("phenopacket.id", "Phenopacket identifier",
                              [_val_str(pp_id)]))

    if meta.get("createdBy"):
        top_items.append(_ri("phenopacket.meta_created_by", "Created by",
                              [_val_str(meta["createdBy"])]))

    if meta.get("created"):
        top_items.append(_ri("phenopacket.meta_created", "Created (ISO 8601)",
                              [_val_datetime(meta["created"])]))

    # Subject
    if phenopacket.get("subject"):
        top_items.append(_map_subject(phenopacket["subject"]))

    # Phenotypic features (one response group per feature)
    for pf in phenopacket.get("phenotypicFeatures", []):
        top_items.append(_map_phenotypic_feature(pf))

    # Diseases (one response group per disease)
    for disease in phenopacket.get("diseases", []):
        top_items.append(_map_disease(disease))

    # Assemble the QuestionnaireResponse
    response: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "id": f"{pp_id}-response" if pp_id else "phenopacket-response",
        "questionnaire": f"{q_ref}|{q_version}",
        "status": "completed",
        "authored": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "item": top_items,
    }

    # If subject has an id, add a FHIR subject reference
    subject_id = phenopacket.get("subject", {}).get("id")
    if subject_id:
        response["subject"] = {"reference": f"Patient/{subject_id}"}

    return response
