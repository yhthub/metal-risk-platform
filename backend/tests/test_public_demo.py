"""Bounded public demo contracts, integrity, real analysis and independent IDs."""
import asyncio
import csv
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.datainput import router
from app.security import ApiGuard
from app.services import data_service, public_demo_service as demo


class PublicDemoTests(unittest.TestCase):
    def test_asset_is_bounded_allowlisted_and_real_public_provenance(self):
        metadata = demo.get_public_demo_metadata()
        self.assertEqual(metadata["rows"], 300)
        self.assertEqual(metadata["eligible_records"], 3739)
        self.assertEqual(len(metadata["columns"]), 23)
        self.assertFalse(metadata["selection"]["imputation"])
        self.assertFalse(metadata["selection"]["winsorization"])
        self.assertFalse(metadata["selection"]["value_recoding"])
        self.assertEqual({item["file"] for item in metadata["source_files"]}, {"DEMO_J.csv", "BPXO_J.csv", "PBCD_J.csv", "SMQ_J.csv", "ALQ_J.csv"})
        self.assertTrue(all(item["url"].startswith("https://wwwn.cdc.gov/") for item in metadata["source_links"]))
        self.assertNotIn("D:/", json.dumps(metadata))
        content = (demo.ASSET_DIR / metadata["sample_filename"]).read_bytes()
        rows = list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
        ids = [float(row["SEQN"]) for row in rows]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertTrue(all(float(row["DEMO_J__RIDAGEYR"]) >= 18 for row in rows))
        self.assertTrue(all(value != "" for row in rows for value in row.values()))
        for row in rows:
            for reading in range(1, 4):
                self.assertGreater(float(row[f"BPXO_J__BPXOSY{reading}"]), float(row[f"BPXO_J__BPXODI{reading}"]))

    def test_missing_or_corrupted_asset_fails_before_import(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(demo, "ASSET_DIR", Path(directory)):
            with self.assertRaises(demo.PublicDemoError):
                demo.get_public_demo_metadata()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            for source in demo.ASSET_DIR.iterdir():
                destination.joinpath(source.name).write_bytes(source.read_bytes())
            destination.joinpath(demo.SAMPLE_NAME).write_bytes(b"SEQN\nforged\n")
            with patch.object(demo, "ASSET_DIR", destination), self.assertRaisesRegex(demo.PublicDemoError, "完整性"):
                demo.get_public_demo_metadata()

    def test_manifest_schema_drift_or_path_injection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            manifest = demo.get_public_demo_metadata()
            manifest["sample_filename"] = "../outside.csv"
            destination.joinpath(demo.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(demo, "ASSET_DIR", destination), self.assertRaisesRegex(demo.PublicDemoError, "规范"):
                demo.get_public_demo_metadata()

    def test_import_uses_existing_real_analysis_and_never_replaces_user_store(self):
        before_data = dict(data_service.data_store)
        before_analysis = dict(data_service.analysis_store)
        try:
            data_service.data_store["existing-user-result"] = "preserved"
            data_service.analysis_store["existing-user-result"] = {"marker": "preserved"}
            with tempfile.TemporaryDirectory() as directory, patch.object(data_service, "UPLOAD_DIR", directory):
                first = asyncio.run(demo.import_public_demo())
                second = asyncio.run(demo.import_public_demo())
                ids = [first["import_result"]["file_id"], second["import_result"]["file_id"]]
                self.assertNotEqual(ids[0], ids[1])
                self.assertEqual(data_service.data_store["existing-user-result"], "preserved")
                self.assertEqual(data_service.analysis_store["existing-user-result"], {"marker": "preserved"})
                self.assertEqual(first["import_result"]["total_records"], 300)
                self.assertEqual(first["analysis"]["kpis"]["analysis_records"], 300)
                self.assertEqual(first["import_result"]["excluded_records"], 0)
                self.assertEqual(first["analysis"]["metadata"]["demo_provenance"]["id"], demo.DEMO_ID)
                for file_id in ids:
                    saved = json.loads(Path(directory, f"{file_id}_analysis.json").read_text(encoding="utf-8"))
                    self.assertEqual(saved["metadata"]["demo_provenance"]["rows"], 300)
                self.assertEqual(first["analysis"]["kpis"], second["analysis"]["kpis"])
        finally:
            data_service.data_store.clear()
            data_service.data_store.update(before_data)
            data_service.analysis_store.clear()
            data_service.analysis_store.update(before_analysis)

    def test_api_routes_use_shared_auth_and_return_bounded_metadata(self):
        app = FastAPI()
        app.middleware("http")(ApiGuard())
        app.include_router(router)
        with patch.dict(os.environ, {"RAG_API_KEY": "test-demo-key", "RAG_API_KEYS": "", "RAG_REQUIRE_API_KEY": "true"}):
            # Explicit list precedence is tested with the configured nonempty key.
            with patch.dict(os.environ, {"RAG_API_KEYS": "test-demo-key"}), TestClient(app) as client:
                self.assertEqual(client.get("/api/datainput/demo").status_code, 401)
                response = client.get("/api/datainput/demo", headers={"Authorization": "Bearer test-demo-key"})
                self.assertEqual(response.status_code, 200)
                self.assertLess(len(response.content), 64 * 1024)
                self.assertEqual(response.json()["rows"], 300)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertNotIn("preview", response.json())
                self.assertEqual(client.post("/api/datainput/demo/import").status_code, 401)

    def test_authenticated_post_returns_real_analysis_with_no_store_and_nosniff(self):
        app = FastAPI()
        app.middleware("http")(ApiGuard())
        app.include_router(router)
        before_data = dict(data_service.data_store)
        before_analysis = dict(data_service.analysis_store)
        try:
            with patch.dict(os.environ, {"RAG_API_KEYS": "test-demo-key", "RAG_REQUIRE_API_KEY": "true"}), tempfile.TemporaryDirectory() as directory, patch.object(data_service, "UPLOAD_DIR", directory), TestClient(app) as client:
                response = client.post("/api/datainput/demo/import", headers={"Authorization": "Bearer test-demo-key"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["analysis"]["kpis"]["analysis_records"], 300)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        finally:
            data_service.data_store.clear()
            data_service.data_store.update(before_data)
            data_service.analysis_store.clear()
            data_service.analysis_store.update(before_analysis)

    def test_unavailable_asset_api_does_not_return_fake_demo(self):
        app = FastAPI()
        app.include_router(router)
        with tempfile.TemporaryDirectory() as directory, patch.object(demo, "ASSET_DIR", Path(directory)), TestClient(app) as client:
            response = client.get("/api/datainput/demo")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            response = client.post("/api/datainput/demo/import")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")


if __name__ == "__main__":
    unittest.main()
