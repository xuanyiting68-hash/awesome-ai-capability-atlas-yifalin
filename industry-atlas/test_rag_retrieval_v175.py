#!/usr/bin/env python3
"""V1.7.5 frozen-source retrieval tests: deterministic offline mock, no API."""
from dataclasses import replace
import unittest
from provider_contract_v174 import ContractError
from rag_retrieval_v175 import load_reference_data, phrase_hit, retrieve, mock_research, topic_matches

RECORDS, TOPICS = load_reference_data()

class RetrievalV175(unittest.TestCase):
    def test_frozen_scope(self):
        self.assertEqual(len(RECORDS), 133)
        self.assertEqual(len(TOPICS), 15)
        self.assertTrue(all(x.get("approved") is False for x in RECORDS))
    def test_ascii_word_boundary(self):
        self.assertFalse(phrase_hit("orbital lighting", "it"))
        self.assertFalse(phrase_hit("modeling", "model"))
        self.assertTrue(phrase_hit("IT Software", "it"))
        self.assertTrue(phrase_hit("Quant research", "quant"))
        self.assertTrue(phrase_hit("back-testing", "back testing"))
    def test_topic_match_sanity(self):
        self.assertIn("backtest", topic_matches("回测 Python 策略", TOPICS))
        self.assertNotIn("backtest", topic_matches("你好", TOPICS))
    def test_quant_backtest_sources(self):
        names={x.title.lower() for x in retrieve("证券资管量化回测策略", "s02", RECORDS, TOPICS, 8)}
        self.assertIn("backtrader", names)
        self.assertIn("vectorbt", names)
    def test_finance_papers_source(self):
        names={x.title.lower() for x in retrieve("投研论文 PDF 文档整理", "s02", RECORDS, TOPICS, 8)}
        self.assertIn("markitdown", names)
    def test_education_rag_source(self):
        names={x.title.lower() for x in retrieve("学校课程知识库 RAG 检索", "s06", RECORDS, TOPICS, 8)}
        self.assertTrue("ragflow" in names or "llama_index" in names)
    def test_marketing_source(self):
        names={x.title.lower() for x in retrieve("营销客户分群与获客", "s27", RECORDS, TOPICS, 8)}
        self.assertIn("mautic", names)
    def test_dev_agents_source(self):
        names={x.title.lower() for x in retrieve("软件开发 Agent 编程", "s30", RECORDS, TOPICS, 8)}
        self.assertTrue("codex" in names or "opencode" in names)
    def test_sector_empty_and_unknown(self):
        self.assertEqual(retrieve("证券资管量化回测", "s21", RECORDS, TOPICS), [])
        self.assertEqual(retrieve("星际香蕉风铃神秘舞台", "s02", RECORDS, TOPICS), [])
    def test_approved_input_not_auto_promoted(self):
        injected=dict(RECORDS[0], approved=True)
        names=retrieve("语音课程", "s06", [injected], TOPICS)
        self.assertEqual(names, [])
    def test_private_evidence_is_rejected(self):
        bad=dict(RECORDS[0],source_url="https://127.0.0.1/local")
        self.assertEqual(retrieve("语音课程", "s06", [bad], TOPICS), [])
    def test_dedup_and_bound(self):
        source=next(x for x in RECORDS if x["name"].lower()=="backtrader")
        dup=dict(source,id="copy-1")
        result=retrieve("量化回测", "s02", [source,dup], TOPICS, 4)
        self.assertEqual(len(result), 1)
        with self.assertRaises(ContractError):
            retrieve("量化回测", "s02", RECORDS, TOPICS, 999)
    def test_source_identity_is_stable(self):
        one=retrieve("量化回测", "s02", RECORDS, TOPICS, 8)
        two=retrieve("量化回测", "s02", list(reversed(RECORDS)), TOPICS, 8)
        self.assertEqual([(x.evidence_id,x.record_id) for x in one],[(x.evidence_id,x.record_id) for x in two])
    def test_mock_citation_ids_are_grounded(self):
        out=mock_research("量化回测", "s02", "s02-d01", RECORDS, TOPICS)
        self.assertEqual(out["mode"], "offline-mock")
        self.assertEqual(out["billed_usd"], 0.0)
        self.assertTrue(set(out["citation_ids"]).issubset({x["id"] for x in out["sources"]}))
        self.assertTrue(all(x["approval"]=="unapproved" for x in out["sources"]))
    def test_no_evidence_abstains(self):
        r=mock_research("香蕉神秘星球", "s21", "s21-d01", RECORDS, TOPICS)
        self.assertEqual(r["citation_ids"],[])
        self.assertEqual(r["source_count"],0)
        self.assertIn("暂无可核实来源",r["answer"])
    def test_cross_sector_contract(self):
        with self.assertRaises(ContractError):
            mock_research("量化回测", "s02", "s09-d02", RECORDS, TOPICS)
    def test_task_limit(self):
        with self.assertRaises(ContractError):
            retrieve("x"*401, "s02", RECORDS, TOPICS)
    def test_labelled_synthetic_hit_at_8_and_abstention(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parent
        cases=json.loads((root/"rag_eval_cases_v175.json").read_text(encoding="utf-8"))["cases"]
        positive=empty=0
        self.assertEqual(len(cases),12)
        for c in cases:
            with self.subTest(id=c["id"]):
                hits=retrieve(c["task"],c["sector_id"],RECORDS,TOPICS,8)
                if c["expect_empty"]:
                    empty+=1
                    self.assertEqual(hits,[],c["id"])
                else:
                    positive+=1
                    matched={x.title.lower() for x in hits}
                    expected={n.lower() for n in c["expected_any"]}
                    self.assertTrue(matched & expected,(c["id"],matched,expected))
        print("V1.7.5 synthetic frozen-source hit@8: %d/%d; no-evidence abstention: %d/%d (NOT field precision)"%(positive,positive,empty,empty))

if __name__=="__main__":
    unittest.main()
