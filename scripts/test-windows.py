"""Exercise the real native executable with independent Linux Steghide fixtures."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("--exe", type=Path, default=Path("dist/stegseek.exe"))
parser.add_argument("--full-seed", action="store_true", help="Scan all 2^32 seeds on a clean file")
parser.add_argument("--large-wordlist", action="store_true", help="Test offsets beyond 4 GiB using a sparse file")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
exe = args.exe.resolve()
fixtures = root / "tests" / "fixtures"
expected = (fixtures / "payload.bin").read_bytes()
env = dict(os.environ)
if os.name == "nt":
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
count = 0
started = time.monotonic()

def run(*cmd, code=0, data=None, timeout=30):
    global count
    p = subprocess.run([str(exe), *map(str, cmd)], input=data, capture_output=True,
                       env=env, timeout=timeout, cwd=work)
    assert p.returncode == code, (cmd, p.returncode, p.stderr.decode(errors="replace"))
    count += 1
    return p

with tempfile.TemporaryDirectory(prefix="stegseek test ", dir=root / "build") as temp:
    work = Path(temp)
    assert b"0.6-win1" in run("--version").stderr
    run("--help")
    words = work / "words.txt"
    words.write_bytes(b"wrong\r\nBeepBoop123\r\nincorrect\r\n")
    for case in json.loads((fixtures / "manifest.json").read_text())["cases"]:
        path = fixtures / case["file"]
        if case["mode"] == "encrypted":
            assert run(path, words, "-", "-t", "3", "-s").stdout == expected
            assert run("--extract", path, "-", "-p", "BeepBoop123").stdout == expected
        elif case["mode"] == "seed":
            p = run("--seed", path, "-", "-t", "3")
            assert p.stdout == expected
            assert b"00000291" in p.stderr
        else:
            p = run("--seed", path, "-", "-t", "3")
            assert not p.stdout
            assert b"00000291" in p.stderr and b"rijndael-128" in p.stderr
    full = (fixtures / "all-bytes.bin").read_bytes()
    encrypted = fixtures / "all-bytes.bmp"
    assert run(encrypted, words, "-", "-t", "4", "-s").stdout == full
    assert run("--extract", "-", "-", "-p", "BeepBoop123", data=encrypted.read_bytes()).stdout == full
    for ending in (b"\n", b"\r\n"):
        for threads in (1, 3, 20):
            words.write_bytes(ending.join([b"wrong", b"BeepBoop123", b"nope"]))
            assert run(encrypted, words, "-", "-t", threads, "-s").stdout == full
    words.write_bytes(b"wrong\r\nnope\r\n")
    run(encrypted, words, "-", "-s", code=1)
    words.write_bytes(b"")
    run(encrypted, words, "-", "-s", code=1)
    run(encrypted, work / "missing.txt", code=1)
    run(work / "missing.jpg", words, code=1)
    run("--seed", fixtures / "payload.bin", code=1)
    run(encrypted, "-t", "0", code=1)
    # Windows paths containing spaces and non-ASCII characters.
    named = work / "caf\u00e9 \u5b66\u751f.bmp"
    shutil.copyfile(encrypted, named)
    out = work / "recovered \u00e9.bin"
    run("--extract", named, out, "-p", "BeepBoop123")
    assert out.read_bytes() == full
    # Preserve existing files when overwrite is declined.
    out.write_bytes(b"keep me")
    run("--extract", encrypted, out, "-p", "BeepBoop123", data=b"n\n", code=1)
    assert out.read_bytes() == b"keep me"
    run("--extract", encrypted, out, "-p", "BeepBoop123", "-f")
    assert out.read_bytes() == full
    # Embed on Windows; a separate Linux check validates the persistent output.
    windows_fixture = root / "build" / "windows-embedded.bmp"
    run("--embed", fixtures / "all-bytes.bin", fixtures / "clean.bmp", windows_fixture,
        "-p", "Win587", "-f")
    assert run("--extract", windows_fixture, "-", "-p", "Win587").stdout == full
    if args.large_wordlist:
        # Keep this transient sparse file outside OneDrive/workspace sync folders.
        import ctypes
        import msvcrt
        from ctypes import wintypes
        with tempfile.TemporaryDirectory(prefix="stegseek-large-") as large_temp:
            large = Path(large_temp) / "words.txt"
            with large.open("w+b") as stream:
                ioctl = ctypes.WinDLL("kernel32", use_last_error=True).DeviceIoControl
                ioctl.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
                ioctl.restype = wintypes.BOOL
                returned = wintypes.DWORD()
                if not ioctl(msvcrt.get_osfhandle(stream.fileno()), 0x900C4, None, 0,
                             None, 0, ctypes.byref(returned), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                total = (1 << 33) + 128
                stream.truncate(total)
                stream.seek(total // 2)
                stream.write(b"BeepBoop123\r\n")
            assert run(encrypted, large, "-", "-t", "2", "-s").stdout == full
    if args.full_seed:
        p = run("--seed", fixtures / "clean.bmp", "-t", "8", "--accessible", code=1, timeout=1800)
        assert b"Could not find a valid seed" in p.stderr
elapsed = time.monotonic() - started
print(f"PASS: {count} native executable checks in {elapsed:.1f}s "
      f"(full seed scan: {args.full_seed}, >4 GiB wordlist offset: {args.large_wordlist})")
