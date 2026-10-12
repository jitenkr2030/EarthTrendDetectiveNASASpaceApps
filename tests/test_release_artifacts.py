import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/analysis/earthtrend_final_evidence.json"
REPORT = ROOT / "reports/earthtrend_scientific_report.html"
FIGURES = ROOT / "data/analysis/figures"

EXPECTED_FIGURES = [
    "earthtrend_when_timeline.png",
    "earthtrend_where_rainfall_link.png",
    "earthtrend_extreme_events.png",
    "earthtrend_rainfall_link.png",
    "earthtrend_final_finding.png",
]


class TestEarthTrendReleaseArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EVIDENCE.is_file():
            raise FileNotFoundError(f"Evidence JSON missing: {EVIDENCE}")
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_is_valid_json_object(self):
        self.assertIsInstance(self.evidence, dict)
        self.assertEqual(self.evidence.get("project"), "EarthTrend Detective")

    def test_evidence_status_passes(self):
        self.assertEqual(self.evidence.get("status"), "PASS")

    def test_required_evidence_sections_exist(self):
        for key in ("DATA", "EVIDENCE", "INTERPRETATION", "LIMITATIONS"):
            with self.subTest(section=key):
                self.assertIn(key, self.evidence)

    def test_all_expected_evidence_groups_exist(self):
        groups = self.evidence.get("EVIDENCE", {})
        expected = (
            "LONG_TERM_TREND",
            "SEASONAL_TREND",
            "SPATIAL_TREND",
            "EXTREME_EVENTS",
            "RAINFALL_SAME_MONTH",
            "RAINFALL_LAG",
            "RAINFALL_SEASONAL",
            "RAINFALL_AUTOCORRELATION_AWARE",
            "RAINFALL_SPATIAL",
            "SPATIAL_SENSITIVITY",
        )
        for key in expected:
            with self.subTest(evidence_group=key):
                self.assertIn(key, groups)

    def test_final_interpretation_is_present(self):
        interpretation = self.evidence.get("INTERPRETATION", {})
        self.assertTrue(interpretation.get("final_finding"))
        self.assertIn("causality_statement", interpretation)

    def test_limitations_are_documented(self):
        limitations = self.evidence.get("LIMITATIONS")
        self.assertIsInstance(limitations, list)
        self.assertGreater(len(limitations), 0)

    def test_all_five_figures_exist(self):
        for filename in EXPECTED_FIGURES:
            with self.subTest(figure=filename):
                path = FIGURES / filename
                self.assertTrue(path.is_file(), f"Missing figure: {path}")
                self.assertGreater(path.stat().st_size, 0)

    def test_report_exists_and_is_standalone(self):
        self.assertTrue(REPORT.is_file(), f"Missing report: {REPORT}")
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", report.lower())
        self.assertIn("Scientific Methodology", report)
        self.assertIn("Limitations", report)
        self.assertIn("does not establish causality", report)

    def test_all_five_figures_are_embedded(self):
        report = REPORT.read_text(encoding="utf-8")
        self.assertGreaterEqual(report.count("data:image/png;base64,"), 5)

    def test_notebook_contains_download_control(self):
        notebook = ROOT / "research/earthtrend_detective.py"
        self.assertTrue(notebook.is_file())
        source = notebook.read_text(encoding="utf-8")
        self.assertIn("Download Scientific Report", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
