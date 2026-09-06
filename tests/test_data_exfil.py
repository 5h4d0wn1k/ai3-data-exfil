"""AI3 data-exfiltration engine tests — real code paths, offline, stdlib only."""

import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_exfil import (  # noqa: E402
    CovertChannel,
    DataEncoder,
    ModelWatermark,
    WeightSteganography,
    run_experiment,
)


class TestSteganography(unittest.TestCase):
    def setUp(self):
        self.weights = np.random.randn(50, 50).astype(np.float64)
        self.steg = WeightSteganography(seed=1)

    def test_lsb_round_trip(self):
        secret = "round trip works"
        hidden = self.steg.embed_lsb(self.weights, secret)
        self.assertEqual(self.steg.extract_lsb(hidden), secret)

    def test_lsb_preserves_shape(self):
        hidden = self.steg.embed_lsb(self.weights, "abc")
        self.assertEqual(hidden.shape, self.weights.shape)

    def test_index_round_trip(self):
        payload = b"INDEX-EXFIL-DATA"
        hidden = self.steg.embed_index(self.weights, payload)
        self.assertEqual(self.steg.extract_index(hidden, len(payload)), payload)


class TestCovertChannel(unittest.TestCase):
    def test_prediction_channel_round_trip(self):
        channel = CovertChannel(num_classes=16, seed=1)
        enc = channel.sender_encode("HELLO-EXFIL")
        self.assertEqual(channel.receiver_decode(enc["predictions"]), "HELLO-EXFIL")

    def test_timing_channel_round_trip(self):
        channel = CovertChannel(num_classes=16, seed=1)
        enc = channel.timing_channel("TIMING-MSG", base_delay=0.001)
        self.assertEqual(channel.decode_timing(enc["delays"], threshold=0.002),
                         "TIMING-MSG")


class TestWatermark(unittest.TestCase):
    def test_watermark_detected_with_correct_owner(self):
        weights = np.random.RandomState(2).randn(40, 40).astype(np.float64)
        wm = ModelWatermark(key="test-key", seed=1)
        marked = wm.embed_watermark(weights, owner_id="LAB-7")
        verification = wm.verify_watermark(marked, owner_id="LAB-7")
        self.assertTrue(verification["detected"])

    def test_watermark_not_detected_with_wrong_owner(self):
        weights = np.random.RandomState(2).randn(40, 40).astype(np.float64)
        wm = ModelWatermark(key="test-key", seed=1)
        marked = wm.embed_watermark(weights, owner_id="LAB-7")
        wrong = wm.verify_watermark(marked, owner_id="WRONG")
        self.assertFalse(wrong["detected"])


class TestDataEncoder(unittest.TestCase):
    def test_payload_round_trip(self):
        weights = np.random.RandomState(3).randn(60, 60).astype(np.float64)
        encoder = DataEncoder()
        payload = b"payload-12345"
        encoded = encoder.encode(weights, payload)
        self.assertEqual(encoder.decode(encoded), payload)


class TestRunExperiment(unittest.TestCase):
    def test_returns_structured_results(self):
        r = run_experiment(seed=1, weight_rows=40, weight_cols=40)
        self.assertTrue(r["lsb_steganography"]["round_trip_match"])
        self.assertTrue(r["index_steganography"]["round_trip_match"])
        self.assertTrue(r["covert_channel"]["round_trip_match"])
        self.assertTrue(r["covert_channel"]["timing_match"])
        self.assertTrue(r["watermark"]["detected"])
        self.assertFalse(r["watermark"]["wrong_key_detected"])
        self.assertTrue(r["payload_encoder"]["round_trip_match"])


class TestCLI(unittest.TestCase):
    def test_cli_writes_json_report_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "report.json")
            from data_exfil import main
            code = main(["--seed", "1", "--rows", "30", "--cols", "30",
                         "--output", out, "--quiet"])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["weights_shape"], [30, 30])


if __name__ == "__main__":
    unittest.main()