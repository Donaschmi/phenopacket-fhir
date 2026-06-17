"""
FHIR R4 Questionnaire definition that mirrors the Phenopacket v2 schema
for the elements: Subject, PhenotypicFeature, Disease.

The returned dict is a valid FHIR Questionnaire resource that can be
serialised to JSON with ``json.dumps(build_questionnaire(), indent=2)``.
"""

from __future__ import annotations
from typing import Any

QUESTIONNAIRE_ID = "phenopacket-v2"
QUESTIONNAIRE_URL = "https://phenopackets.org/fhir/Questionnaire/phenopacket-v2"
QUESTIONNAIRE_VERSION = "2.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(
    link_id: str,
    text: str,
    item_type: str,
    *,
    required: bool = False,
    repeats: bool = False,
    answer_option: list[dict] | None = None,
    answer_value_set: str | None = None,
    extension: list[dict] | None = None,
    sub_items: list[dict] | None = None,
) -> dict[str, Any]:
    """Build a single Questionnaire.item dict."""
    node: dict[str, Any] = {
        "linkId": link_id,
        "text": text,
        "type": item_type,
    }
    if required:
        node["required"] = True
    if repeats:
        node["repeats"] = True
    if answer_option:
        node["answerOption"] = answer_option
    if answer_value_set:
        node["answerValueSet"] = answer_value_set
    if extension:
        node["extension"] = extension
    if sub_items:
        node["item"] = sub_items
    return node


def _coding_option(system: str, code: str, display: str) -> dict:
    return {"valueCoding": {"system": system, "code": code, "display": display}}


def _hp_onset_options() -> list[dict]:
    """Common HPO onset terms as answerOptions."""
    hp = "http://purl.obolibrary.org/obo/hp.owl"
    return [
        _coding_option(hp, "HP:0003577", "Congenital onset"),
        _coding_option(hp, "HP:0003623", "Neonatal onset"),
        _coding_option(hp, "HP:0003593", "Infantile onset"),
        _coding_option(hp, "HP:0011463", "Childhood onset"),
        _coding_option(hp, "HP:0003621", "Juvenile onset"),
        _coding_option(hp, "HP:0003581", "Adult onset"),
        _coding_option(hp, "HP:0003596", "Middle age onset"),
        _coding_option(hp, "HP:0003584", "Late onset"),
    ]


def _hp_severity_options() -> list[dict]:
    hp = "http://purl.obolibrary.org/obo/hp.owl"
    return [
        _coding_option(hp, "HP:0012827", "Borderline"),
        _coding_option(hp, "HP:0012825", "Mild"),
        _coding_option(hp, "HP:0012826", "Moderate"),
        _coding_option(hp, "HP:0012829", "Severe"),
        _coding_option(hp, "HP:0012828", "Profound"),
    ]


# ---------------------------------------------------------------------------
# Subject group
# ---------------------------------------------------------------------------

def _subject_items() -> list[dict]:
    sex_system = "https://phenopackets.org/schema/sex"
    karyotype_system = "https://phenopackets.org/schema/karyotypic-sex"

    return [
        _item("subject.id", "Patient / subject identifier", "string", required=True),
        _item("subject.date_of_birth", "Date of birth", "date"),
        _item(
            "subject.sex",
            "Biological sex",
            "choice",
            answer_option=[
                _coding_option(sex_system, "UNKNOWN_SEX", "Unknown"),
                _coding_option(sex_system, "FEMALE", "Female"),
                _coding_option(sex_system, "MALE", "Male"),
                _coding_option(sex_system, "OTHER_SEX", "Other"),
            ],
        ),
        _item(
            "subject.karyotypic_sex",
            "Karyotypic sex",
            "choice",
            answer_option=[
                _coding_option(karyotype_system, "UNKNOWN_KARYOTYPE", "Unknown karyotype"),
                _coding_option(karyotype_system, "XX", "XX"),
                _coding_option(karyotype_system, "XY", "XY"),
                _coding_option(karyotype_system, "XO", "XO"),
                _coding_option(karyotype_system, "XXY", "XXY"),
                _coding_option(karyotype_system, "XXX", "XXX"),
                _coding_option(karyotype_system, "XXYY", "XXYY"),
                _coding_option(karyotype_system, "XXXY", "XXXY"),
                _coding_option(karyotype_system, "XXXX", "XXXX"),
                _coding_option(karyotype_system, "XYY", "XYY"),
                _coding_option(karyotype_system, "OTHER_KARYOTYPE", "Other"),
            ],
        ),
        _item(
            "subject.taxonomy",
            "Taxonomy (NCBITaxon)",
            "open-choice",
            answer_option=[
                _coding_option("http://purl.obolibrary.org/obo/ncbitaxon.owl", "NCBITaxon:9606", "Homo sapiens"),
            ],
        ),
        _item(
            "subject.vital_status",
            "Vital status",
            "choice",
            answer_option=[
                _coding_option("https://phenopackets.org/schema/vital-status", "UNKNOWN_STATUS", "Unknown"),
                _coding_option("https://phenopackets.org/schema/vital-status", "ALIVE", "Alive"),
                _coding_option("https://phenopackets.org/schema/vital-status", "DECEASED", "Deceased"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Phenotypic feature group (repeats)
# ---------------------------------------------------------------------------

def _phenotypic_feature_items() -> list[dict]:
    """Items inside one PhenotypicFeature repeat block."""
    return [
        _item(
            "phenotypic_feature.type",
            "HPO term (type)",
            "open-choice",
            required=True,
            answer_value_set="http://purl.obolibrary.org/obo/hp.owl",
        ),
        _item("phenotypic_feature.excluded", "Excluded (negated observation)", "boolean"),
        _item(
            "phenotypic_feature.onset_ontology",
            "Onset (ontology class)",
            "choice",
            answer_option=_hp_onset_options(),
        ),
        _item("phenotypic_feature.onset_age", "Onset (ISO 8601 age, e.g. P2Y3M)", "string"),
        _item("phenotypic_feature.onset_date", "Onset (date)", "date"),
        _item(
            "phenotypic_feature.severity",
            "Severity (HPO)",
            "choice",
            answer_option=_hp_severity_options(),
        ),
        _item(
            "phenotypic_feature.modifiers",
            "Clinical modifiers (HPO, multiple allowed)",
            "open-choice",
            repeats=True,
            answer_value_set="http://purl.obolibrary.org/obo/hp.owl",
        ),
    ]


# ---------------------------------------------------------------------------
# Disease group (repeats)
# ---------------------------------------------------------------------------

def _disease_items() -> list[dict]:
    """Items inside one Disease repeat block."""
    mondo = "http://purl.obolibrary.org/obo/mondo.owl"
    omim = "https://www.omim.org"

    return [
        _item(
            "disease.term",
            "Disease term (MONDO / OMIM / ICD)",
            "open-choice",
            required=True,
            answer_option=[
                _coding_option(mondo, "MONDO:0000001", "disease or disorder (pick a specific term)"),
                _coding_option(omim, "OMIM:000000", "OMIM entry (enter correct code)"),
            ],
        ),
        _item("disease.excluded", "Excluded (rule-out diagnosis)", "boolean"),
        _item(
            "disease.onset_ontology",
            "Onset (ontology class)",
            "choice",
            answer_option=_hp_onset_options(),
        ),
        _item("disease.onset_age", "Onset (ISO 8601 age)", "string"),
        _item("disease.onset_date", "Onset (date)", "date"),
        _item(
            "disease.disease_stage",
            "Disease stage (e.g. TNM, cancer staging)",
            "open-choice",
            repeats=True,
        ),
        _item(
            "disease.primary_site",
            "Primary anatomical site",
            "open-choice",
        ),
        _item(
            "disease.laterality",
            "Laterality",
            "choice",
            answer_option=[
                _coding_option("http://purl.obolibrary.org/obo/hp.owl", "HP:0012834", "Right"),
                _coding_option("http://purl.obolibrary.org/obo/hp.owl", "HP:0012835", "Left"),
                _coding_option("http://purl.obolibrary.org/obo/hp.owl", "HP:0012833", "Unilateral"),
                _coding_option("http://purl.obolibrary.org/obo/hp.owl", "HP:0012832", "Bilateral"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_questionnaire() -> dict[str, Any]:
    """
    Return a FHIR R4 Questionnaire resource (as a Python dict) that captures
    the Phenopacket v2 elements: Subject, PhenotypicFeature, Disease.
    """
    return {
        "resourceType": "Questionnaire",
        "id": QUESTIONNAIRE_ID,
        "url": QUESTIONNAIRE_URL,
        "version": QUESTIONNAIRE_VERSION,
        "name": "PhenopacketV2",
        "title": "GA4GH Phenopacket v2 — Clinical Phenotyping Form",
        "status": "active",
        "experimental": True,
        "date": "2024-01-01",
        "publisher": "GA4GH / Phenopackets",
        "description": (
            "FHIR Questionnaire representation of the GA4GH Phenopacket v2 schema, "
            "covering Subject (Individual), PhenotypicFeatures (HPO), and Diseases."
        ),
        "item": [
            # ── Phenopacket-level metadata ──────────────────────────────────
            _item("phenopacket.id", "Phenopacket identifier", "string", required=True),
            _item("phenopacket.meta_created_by", "Created by", "string"),
            _item("phenopacket.meta_created", "Created (ISO 8601)", "dateTime"),

            # ── Subject ──────────────────────────────────────────────────────
            _item(
                "subject",
                "Subject (Individual)",
                "group",
                required=True,
                sub_items=_subject_items(),
            ),

            # ── Phenotypic features ──────────────────────────────────────────
            _item(
                "phenotypic_features",
                "Phenotypic Features",
                "group",
                repeats=True,
                sub_items=_phenotypic_feature_items(),
            ),

            # ── Diseases ────────────────────────────────────────────────────
            _item(
                "diseases",
                "Diseases",
                "group",
                repeats=True,
                sub_items=_disease_items(),
            ),
        ],
    }
