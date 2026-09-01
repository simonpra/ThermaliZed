import unittest

import numpy as np

from src.utils.functions import to_degrees_c, to_raw


class TemperatureConversionTests(unittest.TestCase):
    def test_scalar_round_trip(self):
        self.assertEqual(to_degrees_c(to_raw(25.0)), 25.0)

    def test_array_conversion_preserves_shape(self):
        raw = np.array([[to_raw(0.0), to_raw(25.0)]], dtype=np.uint16)

        converted = to_degrees_c(raw)

        np.testing.assert_array_equal(converted, np.array([[0.0, 25.0]]))


if __name__ == "__main__":
    unittest.main()
