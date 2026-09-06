# AI3 — Data Exfiltration via ML

Steganographic data hiding, covert channels, and model watermarking toolkit.

## Overview

This project demonstrates data exfiltration and covert communication techniques using ML model weights and prediction APIs:
- **Weight steganography**: Hide messages in model weight LSBs
- **Covert channels**: Exfiltrate data via prediction API responses
- **Model watermarking**: Embed ownership signatures in weights
- **Data encoding**: Encode arbitrary payloads into weight perturbations

## Features

- **LSB Steganography**: Hide text in least significant bits of model weights
- **Index-Based Steganography**: Target low-magnitude weights for embedding
- **Prediction API Channel**: Encode data in prediction probability distributions
- **Timing Channel**: Encode bits in API response delays
- **Model Watermarking**: Embed and verify ownership signatures
- **Payload Encoding**: Encode arbitrary bytes into weight perturbations

## Installation

```bash
pip install numpy
```

## Usage

```python
from data_exfil import WeightSteganography, CovertChannel, ModelWatermark

# Hide data in weights
steg = WeightSteganography()
w_hidden = steg.embed_lsb(weights, "SECRET MESSAGE")
message = steg.extract_lsb(w_hidden)

# Covert channel via predictions
channel = CovertChannel(num_classes=16)
encoded = channel.sender_encode("exfiltrated data")
decoded = channel.receiver_decode(encoded["predictions"])

# Model watermarking
wm = ModelWatermark(key="owner-key")
w_watermarked = wm.embed_watermark(weights, owner_id="OWNER-001")
result = wm.verify_watermark(w_watermarked, owner_id="OWNER-001")
```

### Running the Demo

```bash
# Offline demo (no network, no external model) — prints full report, exit 0
python3 data_exfil.py

# Tunable experiment
python3 data_exfil.py --seed 7 --rows 200 --cols 200

# JSON report to reports/ (gitignored)
python3 data_exfil.py --output reports/ai3-report.json

# Quiet CI mode + JSON
python3 data_exfil.py --quiet --output reports/ai3-report.json
```

### Exit Codes

- `0` — experiment completed cleanly
- `1` — error (bad arguments / report write failure)

### Live Lab Test Plan

Runs entirely offline — weights, messages, keys, and payloads are generated
locally; nothing is downloaded and no external ML service is queried.

1. **Demo**: `python3 data_exfil.py` — expect four round-trip blocks (LSB steganography, index steganography, prediction/timing covert channel, payload-in-weights encoder) and a watermark block. Exit `0`.
2. **Round trips**: every `round_trip_match` must be `True` — the encoded payload is decoded losslessly from the same weight tensor.
3. **Watermark verification**: `watermark.detected` is `True` for the correct owner and `False` (`wrong_key_detected`) for an impostor.
4. **JSON report**: `python3 data_exfil.py --output reports/ai3-report.json` — verify all `round_trip_match` fields.
5. **Unit tests**: `python3 -m unittest discover -s tests -v` — all pass (LSB/index round trips, prediction/timing channels, watermark owner detection, payload round trip, CLI JSON write).

## Metrics

- Real encode/decode code paths exercised offline: `WeightSteganography.embed_lsb/extract_lsb`, `embed_index/extract_index`, `CovertChannel.sender_encode/receiver_decode` and `timing_channel/decode_timing`, `ModelWatermark.embed_watermark/verify_watermark`, `DataEncoder.encode/decode`
- Every channel reports a `round_trip_match` boolean plus weight-perturbation L2 magnitude
- Watermark reports `correlation`, `cosine_similarity`, `rmse`, `detected`, and owner fingerprint
- 10 unit tests; exit-code contract `0` clean / `1` error
- Zero runtime cloud/network dependencies; offline demo needs only numpy

## Example Output

```
============================================================
  AI3 — Data Exfiltration via ML Demo
============================================================

--- LSB Steganography ---
  Hidden message:  'HIDDEN: Operations room blueprints'
  Extracted:       'HIDDEN: Operations room blueprints'
  Match:           True
  Weight diff L2:  0.000312

--- Prediction API Covert Channel ---
  Message:    'EXFIL: credentials=abc123'
  Decoded:    'EXFIL: credentials=abc123'
  Match:      True

--- Model Watermarking ---
  Owner:         LAB-42
  Correlation:   0.9876
  Cosine sim:    0.9998
  Detected:      True
  Fingerprint:   a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6
```

## How It Works

### LSB Steganography
Modifies the least significant bit of quantized weight values to encode binary data. The perturbation is below floating-point precision thresholds.

### Prediction API Channel
Encodes bits in the probability distribution of model predictions. A high probability for class 1 represents bit=1, high probability for class 0 represents bit=0.

### Model Watermarking
Uses a cryptographic key to select weight indices and embeds a hash-derived pattern. Verification correlates the extracted pattern against the expected owner signature.

## Legal Disclaimer

**IMPORTANT: Read before use.**

This project is provided for **educational and authorized security testing purposes only**.

### Authorization Requirements
- You MUST have explicit written permission before using steganographic or covert channel techniques
- Unauthorized data exfiltration is illegal under federal and state laws
- This tool should ONLY be used on systems you own or have written authorization to test

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA)**: Unauthorized access and data exfiltration is a federal crime
- **Wiretap Act (18 U.S.C. § 2511)**: Covert communication channels may constitute illegal interception
- **GDPR/CCPA**: Hidden data collection may violate privacy regulations
- **State Laws**: Many states have additional computer crime and wiretapping statutes

### Acceptable Use
- Testing data leakage defenses on your own systems
- Authorized red team assessments with written scope
- Academic research in controlled lab environments
- Security education and training

### Prohibited Use
- Exfiltrating data from systems you do not own
- Using covert channels to bypass security controls
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### No Warranty
This software is provided "AS IS" without warranty of any kind. The author is not responsible for any misuse or damage caused by this software.

### Responsible Disclosure
If you discover vulnerabilities using this tool, follow responsible disclosure practices:
1. Report to the vendor/owner privately
2. Allow reasonable time for remediation
3. Do not exploit beyond proof of concept

## License

MIT
