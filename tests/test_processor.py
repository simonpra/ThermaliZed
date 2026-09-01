import unittest

import numpy as np

from src.core.processor import process_thermal_frame


class ThermalProcessorTests(unittest.TestCase):
    def test_calibration_placeholder_is_not_rendered(self):
        frame = np.zeros((384, 256, 2), dtype=np.uint8)
        frame[192:, :, 1] = 0x80

        image, thermal_info, debug_info = process_thermal_frame(
            frame.reshape(-1),
            width=256,
            height=384,
            stride=512,
            params={},
        )

        self.assertIsNone(image)
        self.assertEqual(thermal_info, {})
        self.assertEqual(debug_info, {'frame_status': 'calibrating'})


if __name__ == "__main__":
    unittest.main()
