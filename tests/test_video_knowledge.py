import unittest

from knowledge_engine.video_knowledge import KnowledgeItem, SourceTimestamp, apply_transfer_test


def _item(**overrides):
    defaults = dict(
        knowledge_type="PRINCIPLE",
        claim="Support-loop distance controls the sharpness of a SubD transition.",
        source=SourceTimestamp("video-x", 100.0, 130.0),
        confidence=0.8,
        supporting_evidence="\"the closer the support loop, the tighter the corner reads\"",
    )
    defaults.update(overrides)
    return KnowledgeItem(**defaults)


class KnowledgeItemTests(unittest.TestCase):
    def test_valid_item_passes(self):
        _item().validate()

    def test_invalid_knowledge_type_rejected(self):
        with self.assertRaises(ValueError):
            _item(knowledge_type="OPINION").validate()

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            _item(status="DONE").validate()

    def test_confidence_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            _item(confidence=1.5).validate()

    def test_empty_claim_rejected(self):
        with self.assertRaises(ValueError):
            _item(claim="   ").validate()

    def test_claim_without_evidence_rejected(self):
        with self.assertRaises(ValueError):
            _item(supporting_evidence="").validate()

    def test_decision_without_reason_rejected(self):
        with self.assertRaises(ValueError):
            _item(knowledge_type="DECISION", reason=None).validate()

    def test_decision_with_reason_passes(self):
        _item(knowledge_type="DECISION", reason="avoids an extra join step").validate()

    def test_end_before_start_rejected(self):
        with self.assertRaises(ValueError):
            _item(source=SourceTimestamp("video-x", 130.0, 100.0)).validate()

    def test_to_dict_round_trips_fields(self):
        item = _item()
        data = item.to_dict()
        self.assertEqual(data["knowledge_type"], "PRINCIPLE")
        self.assertEqual(data["status"], "CAPTURED")
        self.assertEqual(data["source"]["source_id"], "video-x")


class TransferTestTests(unittest.TestCase):
    def test_missing_fields_rejected(self):
        item = _item().to_dict()
        with self.assertRaises(ValueError):
            apply_transfer_test(item, {"target_asset": "mug"})

    def test_same_asset_rejected(self):
        item = _item(captured_while_building="tumbler").to_dict()
        with self.assertRaises(ValueError):
            apply_transfer_test(item, {
                "target_asset": "tumbler",
                "expected_effect": "x",
                "observed_effect": "y",
                "pass": True,
                "evidence_path": "runs/x",
            })

    def test_passing_transfer_validates(self):
        item = _item(captured_while_building="tumbler").to_dict()
        updated = apply_transfer_test(item, {
            "target_asset": "mug",
            "expected_effect": "tighter corner transition",
            "observed_effect": "corner transition matched expectation",
            "pass": True,
            "evidence_path": "runs/2026-08-14_simple-mug/checkpoint.png",
        })
        self.assertEqual(updated["status"], "TRANSFER_VALIDATED")
        self.assertEqual(len(updated["transfer_tests"]), 1)

    def test_failing_transfer_from_captured_is_not_yet_learned(self):
        item = _item().to_dict()
        updated = apply_transfer_test(item, {
            "target_asset": "mug",
            "expected_effect": "tighter corner",
            "observed_effect": "no visible change",
            "pass": False,
            "evidence_path": "runs/2026-08-14_simple-mug/checkpoint.png",
        })
        self.assertEqual(updated["status"], "NOT_YET_LEARNED")

    def test_failing_transfer_from_validated_is_contradicted(self):
        item = _item(status="TRANSFER_VALIDATED").to_dict()
        updated = apply_transfer_test(item, {
            "target_asset": "mug",
            "expected_effect": "tighter corner",
            "observed_effect": "no visible change",
            "pass": False,
            "evidence_path": "runs/2026-08-14_simple-mug/checkpoint.png",
        })
        self.assertEqual(updated["status"], "CONTRADICTED")


if __name__ == "__main__":
    unittest.main()
