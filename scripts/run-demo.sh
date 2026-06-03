#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLE="${ROOT}/examples/sequential-vs-random-codes.json"
OUTPUT="${ROOT}/llm-council-output/sequential-vs-random-codes.html"

echo "==> Validating structured council input"
python3 "${ROOT}/scripts/council_tool.py" validate-input "${SAMPLE}"

echo "==> Rendering self-contained HTML artifact"
python3 "${ROOT}/scripts/council_tool.py" render "${SAMPLE}" --output "${OUTPUT}"

echo "==> Validating rendered HTML contract"
python3 "${ROOT}/scripts/council_tool.py" validate-html "${OUTPUT}"

echo "==> Running council tool tests"
python3 -m unittest tests.test_council_tool

echo ""
echo "Demo artifact ready:"
echo "${OUTPUT}"
