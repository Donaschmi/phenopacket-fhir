"""
Tests for phenopackets_fhir — Questionnaire builder and Phenopacket mapper.
Run with:  pytest
"""

import json
import pytest
from phenopackets_fhir import build_questionnaire, phenopacket_to_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def questionnaire():
    return build_questionnaire()


MINIMAL_PHENOPACKET = {
    "id": "test-pp-001",
    "subject": {"id": "patient-001", "sex": "FEMALE"},
    "phenotypicFeatures": [
        {"type": {"id": "HP:0001250", "label": "Seizure"}, "excluded": False}
    ],
    "diseases": [
        {"term": {"id": "MONDO:0005027", "label": "Epilepsy"}, "excluded": False}
    ],
    "metaData": {"phenopacketSchemaVersion": "2.0", "createdBy": "tester"},
}

FULL_PHENOPACKET = {
    "id": "test-pp-full",
    "metaData": {
        "created": "2024-01-15T08:00:00Z",
        "createdBy": "dr.house",
        "phenopacketSchemaVersion": "2.0",
    },
    "subject": {
        "id": "patient-full",
        "dateOfBirth": "1990-06-01",
        "sex": "MALE",
        "karyotypicSex": "XY",
        "taxonomy": {"id": "NCBITaxon:9606", "label": "Homo sapiens"},
        "vitalStatus": {"status": "ALIVE"},
    },
    "phenotypicFeatures": [
        {
            "type": {"id": "HP:0002751", "label": "Kyphoscoliosis"},
            "excluded": False,
            "onset": {"ontologyClass": {"id": "HP:0011463", "label": "Childhood onset"}},
            "severity": {"id": "HP:0012826", "label": "Moderate"},
            "modifiers": [{"id": "HP:0012834", "label": "Right"}],
        },
        {
            "type": {"id": "HP:0000545", "label": "Myopia"},
            "excluded": True,
            "onset": {"age": {"iso8601duration": "P10Y"}},
        },
    ],
    "diseases": [
        {
            "term": {"id": "MONDO:0007947", "label": "Marfan syndrome"},
            "excluded": False,
            "onset": {"timestamp": "2001-03-01T00:00:00Z"},
            "diseaseStage": [{"id": "MONDO:0021140", "label": "Early stage"}],
            "laterality": {"id": "HP:0012832", "label": "Bilateral"},
        }
    ],
}


# ---------------------------------------------------------------------------
# Questionnaire tests
# ---------------------------------------------------------------------------

class TestQuestionnaire:
    def test_resource_type(self, questionnaire):
        assert questionnaire["resourceType"] == "Questionnaire"

    def test_required_fields(self, questionnaire):
        for field in ("id", "url", "version", "status", "title", "item"):
            assert field in questionnaire, f"Missing field: {field}"

    def test_status_active(self, questionnaire):
        assert questionnaire["status"] == "active"

    def test_top_level_items(self, questionnaire):
        link_ids = {it["linkId"] for it in questionnaire["item"]}
        assert "phenopacket.id" in link_ids
        assert "subject" in link_ids
        assert "phenotypic_features" in link_ids
        assert "diseases" in link_ids

    def test_subject_group_has_subitems(self, questionnaire):
        subject = next(it for it in questionnaire["item"] if it["linkId"] == "subject")
        assert subject["type"] == "group"
        assert subject.get("required") is True
        sub_ids = {it["linkId"] for it in subject["item"]}
        assert {"subject.id", "subject.sex", "subject.date_of_birth"}.issubset(sub_ids)

    def test_phenotypic_features_repeats(self, questionnaire):
        pf = next(it for it in questionnaire["item"] if it["linkId"] == "phenotypic_features")
        assert pf.get("repeats") is True

    def test_diseases_repeats(self, questionnaire):
        d = next(it for it in questionnaire["item"] if it["linkId"] == "diseases")
        assert d.get("repeats") is True

    def test_sex_answer_options(self, questionnaire):
        subject = next(it for it in questionnaire["item"] if it["linkId"] == "subject")
        sex_item = next(it for it in subject["item"] if it["linkId"] == "subject.sex")
        codes = {opt["valueCoding"]["code"] for opt in sex_item["answerOption"]}
        assert {"FEMALE", "MALE", "UNKNOWN_SEX", "OTHER_SEX"}.issubset(codes)

    def test_serialisable_to_json(self, questionnaire):
        text = json.dumps(questionnaire)
        assert isinstance(text, str)
        assert len(text) > 100


# ---------------------------------------------------------------------------
# QuestionnaireResponse tests
# ---------------------------------------------------------------------------

class TestMapper:
    def test_resource_type(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        assert r["resourceType"] == "QuestionnaireResponse"

    def test_required_fields(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        for field in ("resourceType", "id", "questionnaire", "status", "item"):
            assert field in r

    def test_status_completed(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        assert r["status"] == "completed"

    def test_id_derived_from_phenopacket(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        assert "test-pp-001" in r["id"]

    def test_questionnaire_reference(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        assert "phenopacket-v2" in r["questionnaire"]
        assert "|" in r["questionnaire"]  # canonical|version format

    def test_subject_reference(self, questionnaire):
        r = phenopacket_to_response(MINIMAL_PHENOPACKET, questionnaire)
        assert r["subject"]["reference"] == "Patient/patient-001"

    def test_subject_items_populated(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        subject_group = next(it for it in r["item"] if it["linkId"] == "subject")
        sub_ids = {it["linkId"] for it in subject_group["item"]}
        assert "subject.id" in sub_ids
        assert "subject.sex" in sub_ids
        assert "subject.date_of_birth" in sub_ids
        assert "subject.karyotypic_sex" in sub_ids
        assert "subject.taxonomy" in sub_ids
        assert "subject.vital_status" in sub_ids

    def test_phenotypic_feature_count(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        pf_items = [it for it in r["item"] if it["linkId"] == "phenotypic_features"]
        assert len(pf_items) == 2

    def test_phenotypic_feature_excluded_true(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        # Second feature has excluded=True
        pf2 = [it for it in r["item"] if it["linkId"] == "phenotypic_features"][1]
        excluded_item = next(it for it in pf2["item"] if it["linkId"] == "phenotypic_feature.excluded")
        assert excluded_item["answer"][0]["valueBoolean"] is True

    def test_onset_ontology_class(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        pf1 = [it for it in r["item"] if it["linkId"] == "phenotypic_features"][0]
        onset = next(it for it in pf1["item"] if it["linkId"] == "phenotypic_feature.onset_ontology")
        assert onset["answer"][0]["valueCoding"]["code"] == "HP:0011463"

    def test_onset_age_string(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        pf2 = [it for it in r["item"] if it["linkId"] == "phenotypic_features"][1]
        onset = next(it for it in pf2["item"] if it["linkId"] == "phenotypic_feature.onset_age")
        assert onset["answer"][0]["valueString"] == "P10Y"

    def test_disease_mapped(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        disease = next(it for it in r["item"] if it["linkId"] == "diseases")
        term = next(it for it in disease["item"] if it["linkId"] == "disease.term")
        assert term["answer"][0]["valueCoding"]["code"] == "MONDO:0007947"

    def test_disease_onset_timestamp(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        disease = next(it for it in r["item"] if it["linkId"] == "diseases")
        onset = next(it for it in disease["item"] if it["linkId"] == "disease.onset_date")
        assert "2001" in onset["answer"][0]["valueDate"]

    def test_disease_laterality(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        disease = next(it for it in r["item"] if it["linkId"] == "diseases")
        lat = next(it for it in disease["item"] if it["linkId"] == "disease.laterality")
        assert lat["answer"][0]["valueCoding"]["code"] == "HP:0012832"

    def test_no_questionnaire_arg(self):
        """Mapper works without passing the questionnaire object."""
        r = phenopacket_to_response(MINIMAL_PHENOPACKET)
        assert r["resourceType"] == "QuestionnaireResponse"

    def test_empty_phenopacket(self):
        r = phenopacket_to_response({})
        assert r["resourceType"] == "QuestionnaireResponse"
        assert r["item"] == []

    def test_serialisable_to_json(self, questionnaire):
        r = phenopacket_to_response(FULL_PHENOPACKET, questionnaire)
        text = json.dumps(r)
        assert isinstance(text, str)
