# phenopacket-fhir

[![PyPI version](https://img.shields.io/pypi/v/phenopacket-fhir.svg)](https://pypi.org/project/phenopacket-fhir/)
[![Python versions](https://img.shields.io/pypi/pyversions/phenopacket-fhir.svg)](https://pypi.org/project/phenopacket-fhir/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Donaschmi/phenopacket-fhir/actions/workflows/tests.yml/badge.svg)](https://github.com/Donaschmi/phenopacket-fhir/actions)

```bash
pip install phenopacket-fhir
```

Maps **GA4GH Phenopackets v2** documents to **FHIR R4 Questionnaire / QuestionnaireResponse** resources.

Covered Phenopacket elements: `Subject`, `PhenotypicFeature` (HPO), `Disease` (MONDO / OMIM / ICD).
Zero runtime dependencies — stdlib only, Python ≥ 3.9.

---

## Installation

```bash
pip install phenopacket-fhir
```

Or for development (includes pytest):

```bash
pip install "phenopacket-fhir[dev]"
```

---

## Quick start

### 1. Generate the FHIR Questionnaire definition

The Questionnaire is a static template describing the form structure (questions, types, answer options). Generate it once and store or publish it.

```python
import json
from phenopackets_fhir import build_questionnaire

questionnaire = build_questionnaire()
print(json.dumps(questionnaire, indent=2))
```

<details>
<summary>Output snippet</summary>

```json
{
  "resourceType": "Questionnaire",
  "id": "phenopacket-v2",
  "url": "https://phenopackets.org/fhir/Questionnaire/phenopacket-v2",
  "version": "2.0",
  "title": "GA4GH Phenopacket v2 — Clinical Phenotyping Form",
  "status": "active",
  "item": [
    { "linkId": "phenopacket.id", "text": "Phenopacket identifier", "type": "string", "required": true },
    {
      "linkId": "subject",
      "text": "Subject (Individual)",
      "type": "group",
      "required": true,
      "item": [
        { "linkId": "subject.id",            "text": "Patient / subject identifier", "type": "string" },
        { "linkId": "subject.date_of_birth", "text": "Date of birth",               "type": "date"   },
        { "linkId": "subject.sex",           "text": "Biological sex",              "type": "choice" }
      ]
    },
    { "linkId": "phenotypic_features", "type": "group", "repeats": true, "item": [ ... ] },
    { "linkId": "diseases",            "type": "group", "repeats": true, "item": [ ... ] }
  ]
}
```
</details>

---

### 2. Map a Phenopacket to a QuestionnaireResponse

```python
import json
from phenopackets_fhir import build_questionnaire, phenopacket_to_response

phenopacket = {
    "id": "my-phenopacket-01",
    "subject": { "id": "patient-42", "sex": "FEMALE", "dateOfBirth": "1990-03-15" },
    "phenotypicFeatures": [
        {
            "type": { "id": "HP:0001250", "label": "Seizure" },
            "onset": { "ontologyClass": { "id": "HP:0003593", "label": "Infantile onset" } },
            "severity": { "id": "HP:0012826", "label": "Moderate" }
        }
    ],
    "diseases": [
        { "term": { "id": "MONDO:0005027", "label": "Epilepsy" }, "excluded": False }
    ],
    "metaData": { "phenopacketSchemaVersion": "2.0", "createdBy": "dr.jones" }
}

questionnaire = build_questionnaire()
response      = phenopacket_to_response(phenopacket, questionnaire)

print(json.dumps(response, indent=2))
```

<details>
<summary>Output snippet</summary>

```json
{
  "resourceType": "QuestionnaireResponse",
  "id": "my-phenopacket-01-response",
  "questionnaire": "https://phenopackets.org/fhir/Questionnaire/phenopacket-v2|2.0",
  "status": "completed",
  "subject": { "reference": "Patient/patient-42" },
  "item": [
    { "linkId": "phenopacket.id", "answer": [{ "valueString": "my-phenopacket-01" }] },
    {
      "linkId": "subject",
      "item": [
        { "linkId": "subject.id",            "answer": [{ "valueString": "patient-42" }] },
        { "linkId": "subject.date_of_birth", "answer": [{ "valueDate": "1990-03-15" }] },
        { "linkId": "subject.sex",           "answer": [{ "valueCoding": { "code": "FEMALE" } }] }
      ]
    },
    {
      "linkId": "phenotypic_features",
      "item": [
        { "linkId": "phenotypic_feature.type",           "answer": [{ "valueCoding": { "code": "HP:0001250", "display": "Seizure" } }] },
        { "linkId": "phenotypic_feature.onset_ontology", "answer": [{ "valueCoding": { "code": "HP:0003593", "display": "Infantile onset" } }] },
        { "linkId": "phenotypic_feature.severity",       "answer": [{ "valueCoding": { "code": "HP:0012826", "display": "Moderate" } }] }
      ]
    },
    {
      "linkId": "diseases",
      "item": [
        { "linkId": "disease.term",     "answer": [{ "valueCoding": { "code": "MONDO:0005027", "display": "Epilepsy" } }] },
        { "linkId": "disease.excluded", "answer": [{ "valueBoolean": false }] }
      ]
    }
  ]
}
```
</details>

---

### 3. Load from a JSON file

```python
import json
from phenopackets_fhir import build_questionnaire, phenopacket_to_response

with open("my_phenopacket.json") as f:
    phenopacket = json.load(f)

response = phenopacket_to_response(phenopacket, build_questionnaire())

with open("response.json", "w") as f:
    json.dump(response, f, indent=2)
```

---

## Command-line interface

After `pip install phenopacket-fhir` a `phenopacket-fhir` command is available:

```bash
# Print the Questionnaire definition
phenopacket-fhir questionnaire

# Map a phenopacket file → QuestionnaireResponse
phenopacket-fhir map my_phenopacket.json

# Emit both Questionnaire + QuestionnaireResponse together
phenopacket-fhir map my_phenopacket.json --with-questionnaire

# Save to a file
phenopacket-fhir map my_phenopacket.json > response.json
```

You can also invoke it as a module if you prefer:

```bash
python -m phenopackets_fhir.cli map my_phenopacket.json
```

---

## Phenopacket input format

The mapper accepts **protobuf-JSON** (the standard Phenopacket wire format). Field names are `camelCase` as produced by `MessageToJson()` or any GA4GH Phenopacket SDK.

### Minimal valid input

```json
{
  "id": "my-phenopacket-01",
  "subject": { "id": "patient-42", "sex": "FEMALE" },
  "phenotypicFeatures": [
    { "type": { "id": "HP:0001250", "label": "Seizure" } }
  ],
  "diseases": [
    { "term": { "id": "MONDO:0005027", "label": "Epilepsy" } }
  ],
  "metaData": { "phenopacketSchemaVersion": "2.0" }
}
```

### Supported onset variants

All five Phenopacket `TimeElement` forms are handled:

```json
{ "onset": { "ontologyClass":  { "id": "HP:0003577", "label": "Congenital onset" } } }
{ "onset": { "age":            { "iso8601duration": "P2Y6M" } } }
{ "onset": { "ageRange":       { "start": { "iso8601duration": "P5Y" }, "end": { "iso8601duration": "P10Y" } } } }
{ "onset": { "timestamp":      "2010-03-15T00:00:00Z" } }
{ "onset": { "gestationalAge": { "weeks": 32, "days": 3 } } }
```

---

## Questionnaire structure

| linkId | Type | Repeats | Notes |
|---|---|---|---|
| `phenopacket.id` | string | — | Required |
| `phenopacket.meta_created_by` | string | — | |
| `phenopacket.meta_created` | dateTime | — | |
| `subject` | group | — | Required |
| `subject.id` | string | — | |
| `subject.date_of_birth` | date | — | |
| `subject.sex` | choice | — | FEMALE / MALE / OTHER_SEX / UNKNOWN_SEX |
| `subject.karyotypic_sex` | choice | — | XX / XY / XO / XXY … |
| `subject.taxonomy` | open-choice | — | NCBITaxon answerOption |
| `subject.vital_status` | choice | — | ALIVE / DECEASED / UNKNOWN_STATUS |
| `phenotypic_features` | group | ✓ | One group per feature |
| `phenotypic_feature.type` | open-choice | — | HPO value set |
| `phenotypic_feature.excluded` | boolean | — | Negated observation |
| `phenotypic_feature.onset_ontology` | choice | — | HPO onset terms |
| `phenotypic_feature.onset_age` | string | — | ISO 8601 duration |
| `phenotypic_feature.onset_date` | date | — | |
| `phenotypic_feature.severity` | choice | — | HPO severity terms |
| `phenotypic_feature.modifiers` | open-choice | ✓ | HPO modifier terms |
| `diseases` | group | ✓ | One group per disease |
| `disease.term` | open-choice | — | MONDO / OMIM / ICD |
| `disease.excluded` | boolean | — | Rule-out diagnosis |
| `disease.onset_ontology` | choice | — | HPO onset terms |
| `disease.onset_age` | string | — | ISO 8601 duration |
| `disease.onset_date` | date | — | |
| `disease.disease_stage` | open-choice | ✓ | TNM / cancer staging |
| `disease.primary_site` | open-choice | — | Anatomical site |
| `disease.laterality` | choice | — | Right / Left / Unilateral / Bilateral |

---

## Contributing

```bash
git clone https://github.com/Donaschmi/phenopacket-fhir.git
cd phenopacket-fhir
pip install -e ".[dev]"
pytest
```
