"""
phenopackets_fhir
=================
Maps GA4GH Phenopackets v2 documents to FHIR R4 Questionnaire /
QuestionnaireResponse resources.

Covered elements
----------------
* Subject (Individual) — id, sex, date_of_birth, taxonomy, vital_status
* PhenotypicFeature  — type (HPO), excluded, onset, severity, modifiers
* Disease            — term (MONDO/OMIM/ICD), excluded, onset, disease_stage

Usage
-----
    from phenopackets_fhir import build_questionnaire, phenopacket_to_response

    questionnaire = build_questionnaire()
    response      = phenopacket_to_response(phenopacket_dict, questionnaire)
"""

from .questionnaire import build_questionnaire
from .mapper import phenopacket_to_response

__all__ = ["build_questionnaire", "phenopacket_to_response"]
