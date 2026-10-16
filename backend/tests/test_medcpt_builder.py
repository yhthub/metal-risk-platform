"""Builder safety tests operate only on three-row generated fixtures/stubs."""
import json
import importlib.util
import os
import sys
import types
import unittest
from importlib.machinery import ModuleSpec
from pathlib import Path
from unittest.mock import patch

import numpy as np

import test_medcpt_dense as dense_fixture_module
import tools.build_medcpt_index as builder_module
from app.services.medcpt_dense_service import DenseUnavailable, MedcptDenseService
from tools.build_medcpt_index import BuildParameters, GIB, build_index, output_target


class StubIndex:
    def __init__(self, fail_training=False, changed_path=None):
        self.cp = types.SimpleNamespace(seed=0)
        self.pq = types.SimpleNamespace(cp=types.SimpleNamespace(seed=0))
        self.fail_training = fail_training
        self.changed_path = changed_path
        self.ntotal = 0
        self.is_trained = False
        self.vectors = []
        self.ids = []

    def train(self, sample):
        if self.fail_training:
            raise RuntimeError("Fixture training failure")
        self.is_trained = True

    def add_with_ids(self, block, ids):
        self.vectors.extend(block.copy())
        self.ids.extend(ids.tolist())
        self.ntotal += len(ids)
        if self.changed_path:
            stat = self.changed_path.stat()
            os.utime(self.changed_path,ns=(stat.st_atime_ns,stat.st_mtime_ns+1000000000))
            self.changed_path = None

    def search(self, queries, k):
        values = np.asarray(self.vectors) @ queries.T
        scores,ids = [],[]
        for query_scores in values.T:
            selected = np.argsort(-query_scores,kind="stable")[:k]
            scores.append(query_scores[selected])
            ids.append(np.asarray(self.ids,dtype=np.int64)[selected])
        return np.asarray(scores,dtype=np.float32),np.asarray(ids,dtype=np.int64)


def fake_faiss(index):
    module = types.ModuleType("faiss")
    module.__spec__ = ModuleSpec("faiss",loader=None)
    module.__version__ = "fixture-stub-not-real-faiss"
    module.METRIC_INNER_PRODUCT = 0
    module.omp_set_num_threads = lambda threads: None
    module.IndexFlatIP = lambda dims: object()
    module.IndexIVFPQ = lambda *args: index
    module.write_index = lambda unused,path: Path(path).write_bytes(b"fixture-stub-index")
    return module


class BuilderSafetyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = dense_fixture_module.IndependentDenseFixture(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        # Sibling directory, not the corpus itself or a preexisting generation.
        self.output = self.root.parent / (self.root.name + "-ann-output")
        self.params = BuildParameters(nlist=1,pq_m=64,pq_bits=1,nprobe=1,sample_rows=3,block_rows=1,threads=1)

    def tearDown(self):
        # Independent generation is owned solely by this test. Temporarily make
        # its parent test temp directory own it so normal fixture cleanup applies.
        if self.output.exists():
            self.output.rename(self.root / "test-output-owned-for-cleanup")
        self.fixture.tearDown()

    def execute_stub(self,index):
        with patch.dict(sys.modules,{"faiss":fake_faiss(index)}), \
             patch("tools.build_medcpt_index.available_ram_bytes",return_value=16*GIB), \
             patch("tools.build_medcpt_index.shutil.disk_usage",return_value=types.SimpleNamespace(free=16*GIB)):
            return build_index(self.root,self.output,execute=True,parameters=self.params)

    def test_default_plan_has_zero_scans_and_creates_no_generation(self):
        with patch("numpy.load",side_effect=AssertionError("PLAN must not load vectors")):
            plan = build_index(self.root,self.output,parameters=self.params)
        self.assertEqual(plan["state"],"PLAN_ONLY")
        self.assertFalse(plan["execution_performed"])
        self.assertEqual(plan["vectors_scanned"],0)
        self.assertEqual(plan["encoder_calls"],0)
        self.assertFalse(self.output.exists())

    def test_output_escape_and_existing_generation_are_rejected(self):
        for output in (self.root,self.root / "subdir",self.root.parent):
            with self.subTest(output=output),self.assertRaises((ValueError,FileExistsError)):
                output_target(self.root,output)
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            build_index(self.root,self.output,parameters=self.params)

    def test_low_ram_refuses_before_array_scan_or_output_write(self):
        with patch("tools.build_medcpt_index.available_ram_bytes",return_value=2*GIB), \
             patch("tools.build_medcpt_index.shutil.disk_usage",return_value=types.SimpleNamespace(free=16*GIB)), \
             patch("numpy.load",side_effect=AssertionError("No scan under low RAM")):
            with self.assertRaises(DenseUnavailable):
                build_index(self.root,self.output,execute=True,parameters=self.params)
        self.assertFalse(self.output.exists())

    def test_low_disk_refuses_before_output_creation(self):
        with patch("tools.build_medcpt_index.available_ram_bytes",return_value=16*GIB), \
             patch("tools.build_medcpt_index.shutil.disk_usage",return_value=types.SimpleNamespace(free=2*GIB)):
            with self.assertRaises(DenseUnavailable):
                build_index(self.root,self.output,execute=True,parameters=self.params)
        self.assertFalse(self.output.exists())

    def test_invalid_parameter_budgets_are_rejected(self):
        for params in (BuildParameters(sample_rows=600000),BuildParameters(block_rows=16384),
                       BuildParameters(pq_m=17),BuildParameters(min_free_ram_gib=1),
                       BuildParameters(min_free_disk_gib=1),BuildParameters(seed=-1)):
            with self.subTest(params=params),self.assertRaises(ValueError):
                params.validate(24139516)

    def test_training_failure_preserves_failed_generation_not_complete(self):
        with self.assertRaises(RuntimeError):
            self.execute_stub(StubIndex(fail_training=True))
        progress = json.loads((self.output / "BUILD_PROGRESS.json").read_text())
        self.assertEqual(progress["state"],"FAILED")
        self.assertEqual(progress["inserted_rows"],0)
        self.assertFalse((self.output / "medcpt_ivfpq.faiss.json").exists())
        self.assertTrue((self.output / "training_row_ids.npy").exists())

    def test_source_change_retains_partial_without_complete_sidecar(self):
        with self.assertRaises(DenseUnavailable):
            self.execute_stub(StubIndex(changed_path=self.root / "first.npy"))
        progress = json.loads((self.output / "BUILD_PROGRESS.json").read_text())
        self.assertEqual(progress["state"],"FAILED")
        self.assertTrue((self.output / "medcpt_ivfpq.partial.faiss").exists())
        self.assertFalse((self.output / "medcpt_ivfpq.faiss.json").exists())

    def test_sidecar_publication_failure_leaves_no_complete_metadata(self):
        original = builder_module._write_json

        def fail_complete(path,payload):
            if str(path).endswith(".faiss.json"):
                raise OSError("Fixture publication failure")
            return original(path,payload)

        with patch("tools.build_medcpt_index._write_json",side_effect=fail_complete):
            with self.assertRaises(OSError):
                self.execute_stub(StubIndex())
        self.assertEqual(json.loads((self.output / "BUILD_PROGRESS.json").read_text())["state"],"FAILED")
        self.assertFalse((self.output / "medcpt_ivfpq.faiss.json").exists())

    def test_stub_complete_sidecar_matches_runtime_full_axis_contract(self):
        index = StubIndex()
        result = self.execute_stub(index)
        self.assertEqual(result["state"],"COMPLETE")
        self.assertEqual(index.ids,[0,1,2])
        self.assertEqual(result["inserted_rows"],3)
        self.assertEqual(result["ntotal"],3)
        self.assertEqual(result["encoder_calls"],0)
        self.assertEqual(index.cp.seed,self.params.seed)
        self.assertTrue(result["approximate"])
        self.assertFalse(result["semantic_gold_used"])
        service = MedcptDenseService(self.root,index_path=self.output / "medcpt_ivfpq.faiss",query_encoder=self.fixture.encoder)
        self.assertEqual(service._index_metadata(self.fixture.manifest,3)["state"],"COMPLETE")
        sampled = np.load(self.output / "training_row_ids.npy",allow_pickle=False)
        self.assertEqual(sampled.tolist(),[0,1,2])

    @unittest.skipUnless(importlib.util.find_spec("faiss"),"Optional FAISS unavailable; real tiny builder runs only in isolated FAISS test environment")
    def test_actual_faiss_three_row_builder_only(self):
        # This explicitly budget-overridden fixture contains only 3 generated
        # vectors. It never points at E:/... or uses a real model/clinical gold.
        params = BuildParameters(nlist=1,pq_m=1,pq_bits=1,nprobe=1,sample_rows=3,block_rows=1,threads=1)
        with patch("tools.build_medcpt_index.available_ram_bytes",return_value=16*GIB), \
             patch("tools.build_medcpt_index.shutil.disk_usage",return_value=types.SimpleNamespace(free=16*GIB)):
            result = build_index(self.root,self.output,execute=True,parameters=params)
        self.assertEqual(result["state"],"COMPLETE")
        self.assertEqual(result["ntotal"],3)
        self.assertEqual(result["encoder_calls"],0)
        service = MedcptDenseService(self.root,index_path=self.output / "medcpt_ivfpq.faiss",query_encoder=self.fixture.encoder)
        search = service.search("fixture",top_k=2)
        self.assertEqual(search["mode"],"medcpt_faiss_ann")
        self.assertTrue(search["diagnostics"]["approximate"])
        self.assertEqual(search["diagnostics"]["score_semantics"],"approximate_inner_product")


if __name__ == "__main__":
    unittest.main()
