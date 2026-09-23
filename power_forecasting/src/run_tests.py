"""Run and save the actual unit/integration test result."""
import json
import unittest
from datetime import datetime, timezone
from .input_data import ROOT

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"tested_at": datetime.now(timezone.utc).isoformat(), "tests_run": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
              "success": result.wasSuccessful(), "failure_details": [str(x[0]) + "\n" + x[1] for x in result.failures + result.errors]}
    (ROOT / "reports/tests_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
