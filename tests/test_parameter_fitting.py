import unittest

import cv2
import numpy as np

from knowledge_engine.parameter_fitting import fit_bounded_parameters, silhouette_objective


class ParameterFittingTests(unittest.TestCase):
    def test_bounded_shape_parameters_improve_registered_silhouette(self):
        reference = np.zeros((96, 96), dtype=bool)
        reference[20:76, 28:68] = True
        reference[38:58, 40:56] = False

        def render(parameters):
            width, hole_width = parameters
            mask = np.zeros_like(reference, dtype=np.uint8)
            half_width = int(round(width / 2))
            cv2.rectangle(mask, (48 - half_width, 20), (48 + half_width, 75), 1, -1)
            half_hole = int(round(hole_width / 2))
            cv2.rectangle(mask, (48 - half_hole, 38), (48 + half_hole, 57), 0, -1)
            return mask.astype(bool)

        objective = silhouette_objective(reference, render)
        result = fit_bounded_parameters(
            objective, [(20, 60), (4, 30)], initial=[58, 5], seed=7, maxiter=12, popsize=5
        )
        self.assertTrue(result["retain_candidate"])
        self.assertLess(result["candidate_objective"], result["initial_objective"])
        self.assertAlmostEqual(result["retained_parameters"][0], 39, delta=2)
        self.assertAlmostEqual(result["retained_parameters"][1], 15, delta=2)


if __name__ == "__main__":
    unittest.main()
