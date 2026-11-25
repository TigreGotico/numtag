"""The readings of the shipped lexicons equal the golden file, row for row."""
import unittest

import golden


class TestGolden(unittest.TestCase):
    def test_readings_equal_the_golden_file(self):
        expected, found = golden.stored(), golden.rows()
        self.assertEqual(len(found), len(expected))
        for number, (want, got) in enumerate(zip(expected, found), 1):
            with self.subTest(row=number):
                self.assertEqual(got, want)
