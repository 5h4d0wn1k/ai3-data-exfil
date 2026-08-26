"""
AI3 — Data Exfiltration via ML
Steganographic data hiding in model weights, covert channels, and model watermarking.
"""

import numpy as np
import hashlib
import struct


class WeightSteganography:
    """Hide data in neural network model weights using bit-plane encoding."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

    def _text_to_bytes(self, text: str) -> bytes:
        return text.encode('utf-8')

    def _bytes_to_text(self, data: bytes) -> str:
        return data.decode('utf-8')

    def _bytes_to_bits(self, data: bytes) -> list:
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    def _bits_to_bytes(self, bits: list) -> bytes:
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_val = 0
            for bit in bits[i:i + 8]:
                byte_val = (byte_val << 1) | bit
            result.append(byte_val)
        return bytes(result)

    def embed_lsb(self, weights: np.ndarray, message: str) -> np.ndarray:
        w = weights.flatten().copy()
        msg_bytes = self._text_to_bytes(message)
        length = len(msg_bytes)

        length_bytes = struct.pack('>H', length)
        all_data = length_bytes + msg_bytes
        bits = self._bytes_to_bits(all_data)

        if len(bits) > len(w):
            raise ValueError(
                f"Message too long: {len(bits)} bits needed, "
                f"{len(w)} available")

        for i, bit in enumerate(bits):
            int_val = np.float32(w[i]).view(np.uint32)
            int_val = (int_val & ~np.uint32(1)) | np.uint32(bit)
            w[i] = int_val.view(np.float32).astype(np.float64)

        return w.reshape(weights.shape)

    def extract_lsb(self, weights: np.ndarray) -> str:
        w = weights.flatten()

        length_bits = []
        for i in range(16):
            int_val = np.float32(w[i]).view(np.uint32)
            length_bits.append(int(int_val & 1))

        length = struct.unpack('>H', self._bits_to_bytes(length_bits))[0]

        msg_bits = []
        for i in range(16, 16 + length * 8):
            int_val = np.float32(w[i]).view(np.uint32)
            msg_bits.append(int(int_val & 1))

        msg_bytes = self._bits_to_bytes(msg_bits)
        return self._bytes_to_text(msg_bytes)

    def embed_index(self, weights: np.ndarray,
                    secret_data: bytes) -> np.ndarray:
        w = weights.flatten().copy()
        bits = self._bytes_to_bits(secret_data)

        rng = np.random.RandomState(42)
        candidates = rng.choice(len(w), size=len(w), replace=False)
        indices = candidates[:len(bits)]

        for i, bit in enumerate(bits):
            int_val = np.float32(w[indices[i]]).view(np.uint32)
            int_val = (int_val & ~np.uint32(1)) | np.uint32(bit)
            w[indices[i]] = int_val.view(np.float32).astype(np.float64)

        return w.reshape(weights.shape)

    def extract_index(self, weights: np.ndarray,
                      data_len: int) -> bytes:
        w = weights.flatten()
        num_bits = data_len * 8

        rng = np.random.RandomState(42)
        candidates = rng.choice(len(w), size=len(w), replace=False)
        indices = candidates[:num_bits]

        bits = []
        for i in range(num_bits):
            int_val = np.float32(w[indices[i]]).view(np.uint32)
            bits.append(int(int_val & 1))

        return self._bits_to_bytes(bits)


class CovertChannel:
    """Simulate covert communication via ML prediction API responses."""

    def __init__(self, num_classes: int = 16, seed: int = 42):
        self.num_classes = num_classes
        self.rng = np.random.RandomState(seed)

    def encode_message(self, message: str) -> list:
        bits = []
        for byte in message.encode('utf-8'):
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    def decode_message(self, bits: list) -> str:
        chars = []
        for i in range(0, len(bits), 8):
            byte_val = 0
            for bit in bits[i:i + 8]:
                byte_val = (byte_val << 1) | bit
            chars.append(chr(byte_val))
        return ''.join(chars)

    def sender_encode(self, message: str) -> dict:
        bits = self.encode_message(message)
        predictions = []
        for bit in bits:
            probs = np.ones(self.num_classes) * 0.05
            if bit == 1:
                probs[1] = 0.9
            else:
                probs[0] = 0.9
            probs /= probs.sum()
            predictions.append(probs)
        return {
            "bits": bits,
            "predictions": predictions,
            "num_bits": len(bits),
        }

    def receiver_decode(self, predictions: list,
                        threshold: float = 0.5) -> str:
        bits = []
        for probs in predictions:
            if probs[1] > threshold:
                bits.append(1)
            else:
                bits.append(0)
        return self.decode_message(bits)

    def timing_channel(self, message: str,
                       base_delay: float = 0.001) -> dict:
        bits = self.encode_message(message)
        delays = []
        for bit in bits:
            if bit == 1:
                delay = base_delay * 3
            else:
                delay = base_delay
            delays.append(delay)
        return {"bits": bits, "delays": delays, "base_delay": base_delay}

    def decode_timing(self, delays: list,
                      threshold: float = 0.002) -> str:
        bits = [1 if d > threshold else 0 for d in delays]
        return self.decode_message(bits)


class ModelWatermark:
    """Embed and verify watermarks in model weights."""

    def __init__(self, key: str = "secret-key-123", seed: int = 42):
        self.key = key
        self.rng = np.random.RandomState(seed)

    def _key_to_indices(self, key: str, size: int,
                        num_indices: int = 64) -> np.ndarray:
        digest = hashlib.sha256(key.encode()).digest()
        seed_val = struct.unpack('<I', digest[:4])[0]
        rng = np.random.RandomState(seed_val)
        return rng.choice(size, size=min(num_indices, size), replace=False)

    def embed_watermark(self, weights: np.ndarray,
                        owner_id: str = "OWNER-001") -> np.ndarray:
        w = weights.copy()
        w_flat = w.flatten()
        indices = self._key_to_indices(self.key, len(w_flat))
        digest = hashlib.sha256(owner_id.encode()).digest()
        pattern = np.frombuffer(digest, dtype=np.uint8).astype(np.float64)
        pattern = (pattern / 255.0) * 2.0 - 1.0

        pattern_tiled = np.tile(pattern, len(indices) // len(pattern) + 1)
        pattern_tiled = pattern_tiled[:len(indices)]

        for i, idx in enumerate(indices):
            w_flat[idx] += pattern_tiled[i]

        return w_flat.reshape(w.shape)

    def verify_watermark(self, weights: np.ndarray,
                         owner_id: str = "OWNER-001") -> dict:
        w_flat = weights.flatten()
        indices = self._key_to_indices(self.key, len(w_flat))
        digest = hashlib.sha256(owner_id.encode()).digest()
        pattern = np.frombuffer(digest, dtype=np.uint8).astype(np.float64)
        pattern = (pattern / 255.0) * 2.0 - 1.0

        pattern_tiled = np.tile(pattern, len(indices) // len(pattern) + 1)
        expected = pattern_tiled[:len(indices)]

        extracted = np.array([w_flat[idx] for idx in indices])
        diff = extracted - expected

        correlation = np.corrcoef(extracted, expected)[0, 1]
        cosine_sim = (np.dot(extracted, expected) /
                      (np.linalg.norm(extracted) *
                       np.linalg.norm(expected) + 1e-12))
        rmse = np.sqrt(np.mean(diff ** 2))

        return {
            "correlation": float(correlation),
            "cosine_similarity": float(cosine_sim),
            "rmse": float(rmse),
            "detected": bool(correlation > 0.3),
        }

    def extract_fingerprint(self, weights: np.ndarray) -> str:
        w_flat = weights.flatten()
        indices = self._key_to_indices(self.key, len(w_flat), num_indices=32)
        values = np.array([w_flat[idx] for idx in indices])
        quantized = ((values * 1e6).astype(int) % 256).astype(np.uint8)
        return hashlib.md5(quantized.tobytes()).hexdigest()


class DataEncoder:
    """Encode arbitrary data into model weight perturbations."""

    def __init__(self, scale: float = 1e6):
        self.scale = scale

    def encode(self, weights: np.ndarray,
               payload: bytes) -> np.ndarray:
        w = weights.flatten().copy()
        payload_bits = []
        for byte in payload:
            for i in range(7, -1, -1):
                payload_bits.append((byte >> i) & 1)

        length_bytes = struct.pack('>H', len(payload))
        length_bits = []
        for byte in length_bytes:
            for i in range(7, -1, -1):
                length_bits.append((byte >> i) & 1)

        all_bits = length_bits + payload_bits

        if len(all_bits) > len(w):
            raise ValueError("Payload too large for model capacity")

        for i, bit in enumerate(all_bits):
            int_val = np.float32(w[i]).view(np.uint32)
            int_val = (int_val & ~np.uint32(1)) | np.uint32(bit)
            w[i] = int_val.view(np.float32).astype(np.float64)

        return w.reshape(weights.shape)

    def decode(self, weights: np.ndarray) -> bytes:
        w = weights.flatten()

        length_bits = []
        for i in range(16):
            int_val = np.float32(w[i]).view(np.uint32)
            length_bits.append(int(int_val & 1))

        payload_len = struct.unpack('>H', self._bits_to_bytes(length_bits))[0]

        payload_bits = []
        for i in range(16, 16 + payload_len * 8):
            int_val = np.float32(w[i]).view(np.uint32)
            payload_bits.append(int(int_val & 1))

        return self._bits_to_bytes(payload_bits)

    @staticmethod
    def _bits_to_bytes(bits: list) -> bytes:
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_val = 0
            for bit in bits[i:i + 8]:
                byte_val = (byte_val << 1) | bit
            result.append(byte_val)
        return bytes(result)


def main():
    print("=" * 60)
    print("  AI3 — Data Exfiltration via ML Demo")
    print("=" * 60)

    np.random.seed(0)
    weights = np.random.randn(100, 100).astype(np.float64)

    print("\n--- LSB Steganography ---")
    steg = WeightSteganography()
    secret = "HIDDEN: Operations room blueprints"
    w_steg = steg.embed_lsb(weights, secret)
    extracted = steg.extract_lsb(w_steg)
    print(f"  Hidden message:  '{secret}'")
    print(f"  Extracted:       '{extracted}'")
    print(f"  Match:           {extracted == secret}")
    print(f"  Weight diff L2:  {np.sqrt(np.sum((w_steg - weights)**2)):.6f}")

    print("\n--- Index-Based Steganography ---")
    secret_bytes = b"TOP SECRET: 42.3601,-71.0589"
    w_idx = steg.embed_index(weights, secret_bytes)
    extracted_bytes = steg.extract_index(w_idx, len(secret_bytes))
    print(f"  Hidden:    {secret_bytes}")
    print(f"  Extracted: {extracted_bytes}")
    print(f"  Match:     {extracted_bytes == secret_bytes}")

    print("\n--- Prediction API Covert Channel ---")
    channel = CovertChannel(num_classes=16)
    msg = "EXFIL: credentials=abc123"
    encoded = channel.sender_encode(msg)
    decoded = channel.receiver_decode(encoded["predictions"])
    print(f"  Message:    '{msg}'")
    print(f"  Decoded:    '{decoded}'")
    print(f"  Bits:       {encoded['num_bits']}")
    print(f"  Match:      {decoded == msg}")

    print("\n--- Timing Covert Channel ---")
    timing = channel.timing_channel(msg, base_delay=0.001)
    timing_decoded = channel.decode_timing(timing["delays"],
                                           threshold=0.002)
    print(f"  Message:    '{msg}'")
    print(f"  Decoded:    '{timing_decoded}'")
    print(f"  Match:      {timing_decoded == msg}")

    print("\n--- Model Watermarking ---")
    wm = ModelWatermark(key="my-secret-key")
    w_watermarked = wm.embed_watermark(weights, owner_id="LAB-42")
    result = wm.verify_watermark(w_watermarked, owner_id="LAB-42")
    fingerprint = wm.extract_fingerprint(w_watermarked)
    print(f"  Owner:         LAB-42")
    print(f"  Correlation:   {result['correlation']:.4f}")
    print(f"  Cosine sim:    {result['cosine_similarity']:.4f}")
    print(f"  RMSE:          {result['rmse']:.8f}")
    print(f"  Detected:      {result['detected']}")
    print(f"  Fingerprint:   {fingerprint}")

    wrong_key_wm = wm.verify_watermark(w_watermarked, owner_id="WRONG")
    print(f"  Wrong key:     detected={wrong_key_wm['detected']}")

    print("\n--- Data Encoder (Payload in Weights) ---")
    encoder = DataEncoder()
    payload = b"SENSITIVE: model-v3-secret-data"
    w_encoded = encoder.encode(weights, payload)
    decoded_payload = encoder.decode(w_encoded)
    print(f"  Payload:    {payload}")
    print(f"  Decoded:    {decoded_payload}")
    print(f"  Match:      {decoded_payload == payload}")
    print(f"  Weight L2:  {np.sqrt(np.sum((w_encoded - weights)**2)):.6f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
