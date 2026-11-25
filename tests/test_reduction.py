import json
import unittest

from calquory import duplicate_delivery, reduce_case


class ReductionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(order_id="sensitive", event=e, email="private@example.invalid")
                     for e in ("created", "delivered", "retry", "delivered")]
        self.policy = {"allow": ["order_id", "event"]}

    def test_minimal_replay_and_disclosure(self):
        result = reduce_case(self.rows, self.policy)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(duplicate_delivery(result["events"]))
        for i in range(len(result["events"])):
            self.assertFalse(duplicate_delivery(result["events"][:i] + result["events"][i + 1:]))
        for secret in ("sensitive", "private@example.invalid", "email"):
            self.assertNotIn(secret, json.dumps(result))

    def test_blocked_policy_emits_no_rows(self):
        self.assertEqual(reduce_case(self.rows, {"allow": ["event"]}), {"status": "blocked_by_policy"})

    def test_unreproducible(self):
        self.assertEqual(reduce_case(self.rows[:2], self.policy), {"status": "not_reproduced"})

    def test_unknown_field_cannot_be_allowed(self):
        with self.assertRaises(ValueError):
            reduce_case(self.rows, {"allow": ["email"]})

    def test_distinct_references_stay_distinct(self):
        self.rows[-1]["order_id"] = "other"
        self.assertFalse(duplicate_delivery(self.rows))
