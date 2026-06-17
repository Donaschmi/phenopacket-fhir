import json
from phenopackets_fhir import build_questionnaire, phenopacket_to_response

# Load your phenopacket
with open("phenopackets_fhir/example_phenopacket.json") as f:
    phenopacket = json.load(f)

# Build both resources
questionnaire = build_questionnaire()
response      = phenopacket_to_response(phenopacket, questionnaire)

print(json.dumps(response, indent=2))
