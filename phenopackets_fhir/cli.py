#!/usr/bin/env python3
"""
Command-line interface for the Phenopackets → FHIR mapper.

Usage
-----
# Generate the Questionnaire definition
python -m phenopackets_fhir.cli questionnaire

# Map a phenopacket file to a QuestionnaireResponse
python -m phenopackets_fhir.cli map example_phenopacket.json

# Map and also emit the Questionnaire alongside the response
python -m phenopackets_fhir.cli map example_phenopacket.json --with-questionnaire
"""

import argparse
import json
import sys
from pathlib import Path

from .questionnaire import build_questionnaire
from .mapper import phenopacket_to_response


def cmd_questionnaire(args: argparse.Namespace) -> None:
    q = build_questionnaire()
    print(json.dumps(q, indent=2))


def cmd_map(args: argparse.Namespace) -> None:
    path = Path(args.input)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open() as fh:
        phenopacket = json.load(fh)

    questionnaire = build_questionnaire() if args.with_questionnaire else None
    response = phenopacket_to_response(phenopacket, questionnaire)

    if args.with_questionnaire and questionnaire:
        output = {
            "questionnaire": questionnaire,
            "questionnaireResponse": response,
        }
    else:
        output = response

    print(json.dumps(output, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map GA4GH Phenopackets v2 to FHIR Questionnaire / QuestionnaireResponse"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # questionnaire sub-command
    sub.add_parser("questionnaire", help="Print the FHIR Questionnaire definition")

    # map sub-command
    map_parser = sub.add_parser("map", help="Map a Phenopacket JSON file to QuestionnaireResponse")
    map_parser.add_argument("input", help="Path to the Phenopacket JSON file")
    map_parser.add_argument(
        "--with-questionnaire",
        action="store_true",
        help="Also include the Questionnaire definition in the output",
    )

    args = parser.parse_args()
    if args.command == "questionnaire":
        cmd_questionnaire(args)
    elif args.command == "map":
        cmd_map(args)


if __name__ == "__main__":
    main()
