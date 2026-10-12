#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo
echo "========================================"
echo " EARTH TREND DETECTIVE — RELEASE CHECK"
echo "========================================"

echo
echo "[1/4] Checking notebook Python syntax..."
python -m py_compile research/earthtrend_detective.py

echo
echo "[2/4] Checking Marimo notebook..."
marimo check research/earthtrend_detective.py

echo
echo "[3/4] Regenerating scientific HTML report..."
python scripts/export_scientific_report.py

echo
echo "[4/4] Running automated release tests..."
python -m unittest tests/test_release_artifacts.py -v

echo
echo "========================================"
echo " PASS: ALL RELEASE CHECKS COMPLETED"
echo "========================================"
echo "Notebook: research/earthtrend_detective.py"
echo "Evidence: data/analysis/earthtrend_final_evidence.json"
echo "Report:   reports/earthtrend_scientific_report.html"
