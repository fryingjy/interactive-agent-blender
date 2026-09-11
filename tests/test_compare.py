import unittest
import numpy as np
from modeler.compare import metrics


class ComparisonTests(unittest.TestCase):
    def test_identical_is_not_acceptance(self):
        result=metrics(np.ones((3,3)), np.ones((3,3)))
        self.assertEqual(result['iou'], 1)
        self.assertFalse(result['quality_accepted'])

    def test_missing_and_extra(self):
        result=metrics(np.array([[1,1,0]]), np.array([[0,1,1]]))
        self.assertAlmostEqual(result['iou'], 1/3)
        self.assertEqual(result['missing_pixels'], 1)
        self.assertEqual(result['extra_pixels'], 1)

    def test_invalid_masks(self):
        with self.assertRaises(ValueError): metrics(np.zeros((2,2)),np.ones((2,2)))
        with self.assertRaises(ValueError): metrics(np.ones((2,3)),np.ones((2,2)))
