# phenopackets_fhir

Maps **GA4GH Phenopackets v2** documents to **FHIR R4 Questionnaire / QuestionnaireResponse** resources.

Covered Phenopacket elements: `Subject`, `PhenotypicFeature` (HPO), `Disease` (MONDO / OMIM / ICD).

---

## Setup

No external dependencies — standard library only.

```bash
# Clone or copy the phenopackets_fhir/ folder next to your scripts, then:
cd /path/to/Phenopackets
python3 -c "from phenopackets_fhir import build_questionnaire; print('OK')"
```

---

## Quick start

### 1. Generate the FHIR Questionnaire definition

The Questionnaire is a static template — it describes the form structure (questions, types, answer options). Generate it once and store / publish it.

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
    { "linkId": "phenopacket.id",  "text": "Phenopacket identifier", "type": "string", "required": true },
    {
      "linkId": "subject",
      "text": "Subject (Individual)",
      "type": "group",
      "required": true,
      "item": [
        { "linkId": "subject.id",            "text": "Patient / subject identifier", "type": "string" },
        { "linkId": "subject.date_of_birth", "text": "Date of birth",               "type": "date"   },
        { "linkId": "subject.sex",           "text": "Biological sex",              "type": "choice" },
        ...
      ]
    },
    {
      "linkId": "phenotypic_features",
      "text": "Phenotypic Features",
      "type": "group",
      "repeats": true,
      "item": [ ... ]
    },
    {
      "linkId": "diseases",
      "text": "Diseases",
      "type": "group",
      "repeats": true,
      "item": [ ... ]
    }
  ]
}
```
</details>

---

### 2. Map a Phenopacket to a QuestionnaireResponse

```python
import json
from phenopackets_fhir import build_questionnaire, phenopacket_to_response

# Load your phenopacket
with open("phenopackets_fhir/example_phenopacket.json") as f:
    phenopacket = json.load(f)

# Build both resources
questionnaire = build_questionnaire()
response      = phenopacket_to_response(phenopacket, questionnaire)

print(json.dumps(response, indent=2))
```

<details>
<summary>Output snippet (Marfan syndrome example)</summary>

```json
{
  "resourceType": "QuestionnaireResponse",
  "id": "phenopacket-marfan-001-response",
  "questionnaire": "https://phenopackets.org/fhir/Questionnaire/phenopacket-v2|2.0",
  "status": "completed",
  "subject": { "reference": "Patient/patient-001" },
  "item": [
    { "linkId": "phenopacket.id",          "answer": [{ "valueString": "phenopacket-marfan-001" }] },
    { "linkId": "phenopacket.meta_created_by", "answer": [{ "valueString": "dr.smith@clinic.org" }] },
    {
      "linkId": "subject",
      "item": [
        { "linkId": "subject.id",            "answer": [{ "valueString": "patient-001" }] },
        { "linkId": "subject.date_of_birth", "answer": [{ "valueDate": "1985-07-14" }] },
        { "linkId": "subject.sex",           "answer": [{ "valueCoding": { "code": "MALE" } }] },
        { "linkId": "subject.taxonomy",      "answer": [{ "valueCoding": { "code": "NCBITaxon:9606", "display": "Homo sapiens" } }] }
      ]
    },
    {
      "linkId": "phenotypic_features",
      "item": [
        { "linkId": "phenotypic_feature.type",     "answer": [{ "valueCoding": { "code": "HP:0002751", "display": "Kyphoscoliosis" } }] },
        { "linkId": "phenotypic_feature.excluded", "answer": [{ "valueBoolean": false }] },
        { "linkId": "phenotypic_feature.onset_ontology", "answer": [{ "valueCoding": { "code": "HP:0011463", "display": "Childhood onset" } }] },
        { "linkId": "phenotypic_feature.severity", "answer": [{ "valueCoding": { "code": "HP:0012826", "display": "Moderate" } }] }
      ]
    },
    ...
    {
      "linkId": "diseases",
      "item": [
        { "linkId": "disease.term",    "answer": [{ "valueCoding": { "code": "MONDO:0007947", "display": "Marfan syndrome" } }] },
        { "linkId": "disease.excluded","answer": [{ "valueBoolean": false }] },
        { "linkId": "disease.onset_ontology", "answer": [{ "valueCoding": { "code": "HP:0011463", "display": "Childhood onset" } }] }
      ]
    }
  ]
}
```
</details>

---

## Command-line interface

```bash
# Print the Questionnaire definition
python3 -m phenopackets_fhir.cli questionnaire

# Map a phenopacket file → QuestionnaireResponse
python3 -m phenopackets_fhir.cli map phenopackets_fhir/example_phenopacket.json

# Emit both Questionnaire + QuestionnaireResponse in one JSON object
python3 -m phenopackets_fhir.cli map phenopackets_fhir/example_phenopacket.json --with-questionnaire

# Save output to a file
python3 -m phenopackets_fhir.cli map phenopackets_fhir/example_phenopacket.json > response.json
```

---

## Phenopacket input format

The mapper accepts **protobuf-JSON** (the standard wire format). Field names are `camelCase` as produced by `MessageToJson()` or any GA4GH Phenopacket SDK.

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

### Onset variants

All four Phenopacket `TimeElement` forms are supported:

```json
// Ontology class (HPO age of onset)
"onset": { "ontologyClass": { "id": "HP:0003577", "label": "Congenital onset" } }

// ISO 8601 age
"onset": { "age": { "iso8601duration": "P2Y6M" } }

// Calendar date
"onset": { "timestamp": "2010-03-15T00:00:00Z" }

// Age range (start is used)
"onset": { "ageRange": { "start": { "iso8601duration": "P5Y" }, "end": { "iso8601duration": "P10Y" } } }
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

## File layout

```
Phenopackets/
├── phenopackets_fhir/
│   ├── __init__.py          # Public API: build_questionnaire, phenopacket_to_response
│   ├── questionnaire.py     # FHIR Questionnaire definition builder
│   ├── mapper.py            # Phenopacket → QuestionnaireResponse mapper
│   ├── cli.py               # Command-line interface
│   └── example_phenopacket.json   # Marfan syndrome sample
├── questionnaire.json       # Pre-built Questionnaire output
└── questionnaire_response.json    # Pre-built response for the example
```
