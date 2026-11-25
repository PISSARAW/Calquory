import json
import unittest

from evidence_bundle import pack, replay_evidence


class EvidenceTests(unittest.TestCase):
    def test_bundle_removes_private_values_preserves_order_and_predicates(self):
        data = {"schema": "timeline.v1", "case_id": "private-abc", "events": [
            {"id": "revaskel-1", "kind": "document", "subject": "sensitive-item",
             "facts": {"expected": "a"*64, "observed": "b"*64}},
            {"id": "mandoryve-1", "kind": "access", "subject": "person",
             "facts": {"expected": 831, "observed": 742}}],
            "timeline": {"status": "consistent", "relations": [
                {"before": "revaskel-1", "after": "mandoryve-1", "evidence": ["private-anchor"]}]}}
        bundle = pack(data)
        for secret in ("private", "sensitive", "person", "831", "742", "a"*64):
            self.assertNotIn(secret, json.dumps(bundle))
        replay = replay_evidence(bundle)
        self.assertEqual([r["result"] for r in replay["observations"]], ["digest_mismatch", "shorter_access"])
        self.assertEqual(replay["relations"], [{"before": "revaskel-1", "after": "mandoryve-1"}])

    def test_duplicate_or_incomplete_chronology_rejected(self):
        row = {"id": "mandoryve-1", "kind": "unavailable"}
        with self.assertRaises(ValueError):
            replay_evidence({"schema": "bundle.v1", "observations": [row, row], "relations": []})
        row2 = dict(row, id="mandoryve-2")
        with self.assertRaises(ValueError):
            replay_evidence({"schema": "bundle.v1", "observations": [row, row2], "relations": []})
