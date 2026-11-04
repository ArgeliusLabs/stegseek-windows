"""Run under Linux with the distro's unmodified steghide, not the port."""
from pathlib import Path
import hashlib
import json
import random
import struct
import subprocess

root = Path(__file__).resolve().parents[1]
fixtures = root / "tests" / "fixtures"
fixtures.mkdir(parents=True, exist_ok=True)
payload = fixtures / "payload.bin"
payload.write_bytes(b"SEC587\r\n\x00\x1a\xff\nStegSeek\n")
samples = root / "upstream" / "tests" / "steghide" / "data"
records = []
for cover in sorted(samples.iterdir()):
    if cover.suffix not in (".jpg", ".bmp", ".wav", ".au"):
        continue
    for label, password, encryption in (("encrypted", "BeepBoop123", []),
                                         ("seed", "moana5", ["-e", "none"]),
                                         ("seed-encrypted", "moana5", [])):
        output = fixtures / (label + "-" + cover.name)
        subprocess.run(["/usr/bin/steghide", "embed", "-ef", str(payload.relative_to(root)),
                        "-cf", str(cover.relative_to(root)), "-sf", str(output.relative_to(root)),
                        "-p", password, "-f", "-q", *encryption], check=True, cwd=root)
        records.append({"file": output.name, "mode": label, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
# A bigger image can carry every byte value and a complete negative seed scan.
pixels = random.Random(587).randbytes(128 * 128 * 3)
header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
header += struct.pack("<IiiHHIIiiII", 40, 128, 128, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
cover = fixtures / "clean.bmp"
cover.write_bytes(header + pixels)
full = fixtures / "all-bytes.bin"
full.write_bytes(bytes(range(256)) * 4)
subprocess.run(["/usr/bin/steghide", "embed", "-ef", str(full.relative_to(root)),
                "-cf", str(cover.relative_to(root)), "-sf", "tests/fixtures/all-bytes.bmp",
                "-p", "BeepBoop123", "-f", "-q"], check=True, cwd=root)
(fixtures / "manifest.json").write_text(json.dumps({"producer": "Ubuntu steghide 0.5.1",
    "payload_sha256": hashlib.sha256(payload.read_bytes()).hexdigest(), "cases": records}, indent=2) + "\n")
print(f"Created {len(records)} independent interoperability fixtures.")
