"""Offline startup configuration checks; no models, API requests or training."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROBE = """
import json
import sys
from app.services import nhanes_prediction_service as prediction
assert prediction._bundle_cache is None
assert not any(name in sys.modules for name in ('xgboost', 'catboost', 'numpy'))
print(json.dumps({
    'threads': prediction.THREADS,
    'provenance_threads': prediction._provenance()['maximum_cpu_threads'],
    'concurrent_jobs': prediction._provenance()['concurrent_inference_jobs'],
}))
"""


class NhanesCpuThreadTests(unittest.TestCase):
    def probe(self, value=None):
        environment = dict(os.environ)
        environment.pop("NHANES_CPU_THREADS", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        if value is not None:
            environment["NHANES_CPU_THREADS"] = value
        return subprocess.run(
            [sys.executable, "-c", PROBE], cwd=BACKEND_ROOT,
            env=environment, capture_output=True, text=True, timeout=15,
        )

    def test_default_keeps_four_threads(self):
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "threads": 4, "provenance_threads": 4, "concurrent_jobs": 1,
        })

    def test_explicit_limits_one_to_four(self):
        for value in ("1", "2", "3", "4"):
            with self.subTest(value=value):
                result = self.probe(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "threads": int(value), "provenance_threads": int(value), "concurrent_jobs": 1,
                })

    def test_invalid_limit_fails_startup(self):
        for value in ("", "0", "5", "-1", "1.5", "1e0", "true", " 1 "):
            with self.subTest(value=value):
                result = self.probe(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ValueError: NHANES_CPU_THREADS must be an integer from 1 to 4", result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
