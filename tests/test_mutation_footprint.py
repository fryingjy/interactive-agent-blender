import unittest

from blender_ops.mutation_footprint import audit_vertex_footprint


class MutationFootprintTests(unittest.TestCase):
    def test_local_edit_preserves_protected_vertices(self):
        before = {1: (0, 0, 0), 2: (1, 0, 0), 3: (2, 0, 0)}
        after = {1: (0, 1, 0), 2: (1, 0, 0), 3: (2, 0, 0)}
        result = audit_vertex_footprint(before, after, {1})
        self.assertTrue(result["pass"])
        self.assertEqual(result["moved_existing_vertex_ids"], [1])

    def test_unexpected_remote_edit_blocks_footprint(self):
        before = {1: (0, 0, 0), 2: (1, 0, 0)}
        after = {1: (0, 1, 0), 2: (1, 0, 1)}
        result = audit_vertex_footprint(before, after, {1})
        self.assertFalse(result["pass"])
        self.assertEqual(result["unexpected_moved_vertex_ids"], [2])

    def test_unexpected_protected_deletion_blocks_footprint(self):
        before = {1: (0, 0, 0), 2: (1, 0, 0), 3: (2, 0, 0)}
        after = {1: (0, 0, 0), 3: (2, 0, 0)}
        result = audit_vertex_footprint(before, after, {1})
        self.assertFalse(result["pass"])
        self.assertEqual(result["removed_existing_vertex_ids"], [2])
        self.assertEqual(result["unexpected_removed_vertex_ids"], [2])

    def test_unscoped_audit_is_explicitly_not_enforced(self):
        result = audit_vertex_footprint({1: (0, 0, 0)}, {1: (9, 9, 9)}, None)
        self.assertTrue(result["pass"])
        self.assertFalse(result["enforced"])


if __name__ == "__main__":
    unittest.main()
