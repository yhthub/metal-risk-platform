"""Tiny SQLite fixtures: source fidelity, bounded read-only local retrieval."""
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app.services.corpus_retrieval_service import CorpusUnavailable
from app.services.local_evidence_service import DATABASES, LocalEvidenceRetrievalService, query_terms
from app.services.rag_agent_service import select_evidence, evidence_context


class LocalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for source, (filename, _) in DATABASES.items():
            with closing(sqlite3.connect(self.root / filename)) as conn:
                conn.executescript('''
                    CREATE TABLE evidence_documents(document_id TEXT PRIMARY KEY,title TEXT,source_url TEXT,
                      doi_or_standard_no TEXT,source_channel TEXT,document_type TEXT,study_design TEXT,
                      evidence_priority TEXT,source_verified INTEGER,workflow_state TEXT);
                    CREATE TABLE evidence_chunks(id INTEGER PRIMARY KEY,chunk_id TEXT,document_id TEXT,
                      text TEXT,section_title TEXT,page INTEGER,clause_no TEXT,source_text_hash TEXT);
                    CREATE VIRTUAL TABLE evidence_chunks_fts USING fts5(text,section_title,
                      content='evidence_chunks',content_rowid='id',tokenize='trigram');
                ''')
                conn.execute('INSERT INTO evidence_documents VALUES(?,?,?,?,?,?,?,?,?,?)',
                             ('D1','镉暴露与肾损伤','https://example.org/original','GBZ 1—2020',
                              source,'historical_label',None,'P1',0,'imported'))
                text = '职业性镉中毒与职业接触，涉及肾损伤和肾小管功能。' * 12
                conn.execute('INSERT INTO evidence_chunks VALUES(?,?,?,?,?,?,?,?)',
                             (1,'C1','D1',text,'原文章节',4,'3.2','source-hash'))
                conn.execute("INSERT INTO evidence_chunks_fts(evidence_chunks_fts) VALUES('rebuild')")
                conn.commit()
        self.service = LocalEvidenceRetrievalService(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_native_chinese_retrieval_preserves_real_metadata_and_db_bytes(self):
        before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        self.assertTrue(self.service.status()['ready'])
        result = self.service.search('镉肾损伤',top_k=3)
        self.assertEqual(result['mode'],'bm25')
        self.assertFalse(result['degraded'])
        self.assertEqual(result['dense_hits'],[])
        self.assertEqual(len({h['chunk_id'] for h in result['hits']}),3)
        for hit in result['hits']:
            self.assertEqual(hit['original_chunk_id'],'C1')
            self.assertEqual(hit['standard_no_or_doi'],'GBZ 1—2020')
            self.assertIsNone(hit['doi'])
            self.assertEqual(hit['page'],4)
            self.assertLess(hit['bm25_score'],0)
            self.assertFalse(hit['metadata_quality_verified'])
        selected = select_evidence(result['hits'],3,result['diagnostics']['query_terms'])
        self.assertTrue(selected)
        context,cards=evidence_context(selected,3500,result['diagnostics']['query_terms'])
        self.assertIn('肾损伤',context)
        self.assertEqual(cards[0]['standard_no_or_doi'],'GBZ 1—2020')
        after = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        self.assertEqual(before,after)

    def test_sources_dense_rejection_and_unknown_concept(self):
        result=self.service.search('镉肾损伤',sources=['scientific'])
        self.assertEqual({h['source'] for h in result['hits']},{'scientific'})
        with self.assertRaises(ValueError):self.service.search('cadmium',mode='hybrid')
        with self.assertRaises(ValueError):self.service.search('cadmium',sources=['pubmed'])
        result=self.service.search('quazylophenezn42 kidney')
        self.assertFalse(select_evidence(result['hits'],3,result['diagnostics']['query_terms']))

    def test_missing_db_does_not_create_file_and_requests_are_serial(self):
        db=self.root/'scientific_evidence.db';db.unlink()
        self.assertFalse(self.service.status()['ready'])
        with self.assertRaises(CorpusUnavailable):self.service.search('cadmium')
        self.assertFalse(db.exists())
        self.service.capacity.acquire()
        try:
            with self.assertRaises(CorpusUnavailable):self.service.search('cadmium')
        finally:self.service.capacity.release()

    def test_long_query_preserves_tail_and_over_limit_skips_database(self):
        query = ('cadmium kidney injury exposure blood pressure hypertension diabetes cancer '
                 'anemia osteoporosis cognition cardiovascular inflammation chelation pregnancy '
                 'workers adults without quazylophenezn42')
        terms, _ = query_terms(query)
        self.assertIn('without', terms)
        self.assertIn('quazylophenezn42', terms)
        result = self.service.search(query)
        self.assertIn('quazylophenezn42', result['diagnostics']['query_terms'])
        self.assertFalse(select_evidence(result['hits'], 3, result['diagnostics']['query_terms']))
        query += ' alpha beta gamma delta epsilon zeta 未知条件'
        with patch.object(self.service, '_connect', side_effect=AssertionError('must not query')):
            result = self.service.search(query)
        self.assertTrue(result['diagnostics']['query_limit_exceeded'])
        self.assertIn('未知条件', result['diagnostics']['query_terms'])
        self.assertEqual(result['hits'], [])
        self.assertEqual(result['sparse_hits'], [])


if __name__ == '__main__':unittest.main()
