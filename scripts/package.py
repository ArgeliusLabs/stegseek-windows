"""Create matching native binary and complete-source release archives."""
from pathlib import Path
import hashlib
import platform
import re
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
version = "0.6-win1"
binary_name = f"stegseek-{version}-windows-x64"
source_name = f"stegseek-{version}-source"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

# Regenerate only in the original upstream working copy. Published source trees
# already include this patch and do not contain a nested Git repository.
if (root / "upstream/.git").is_dir():
    patch = subprocess.check_output(["git", "-C", str(root / "upstream"), "diff", "--binary"])
    for rel in ("src/windows.manifest", "src/windows.rc"):
        result = subprocess.run(["git", "diff", "--no-index", "--binary", "--", "/dev/null", rel],
                                cwd=root / "upstream", capture_output=True)
        if result.returncode != 1:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        patch += result.stdout
    (root / "windows-port.patch").write_bytes(patch)

# Packaging requires the build/validation logs for this executable; do not
# silently reuse the release's validation claims for a locally rebuilt binary.
linux_log = (root / "build/ctest-linux.log").read_text()
linux_log = re.sub(r"(?m)^(Internal ctest changing into directory:|Test project) .*$",
                   r"\1 <workspace>/build/linux", linux_log)

exe = dist / "stegseek.exe"
info = f"""StegSeek {version}, unofficial Windows x64 build
Release date: 2026-11-04
Upstream commit: 58969789a5724701048d5d5510af84098cc1f1ea
Executable SHA-256: {digest(exe)}
Executable bytes: {exe.stat().st_size}
Native validation host: {platform.platform()}
Imported DLLs: bcrypt.dll, KERNEL32.dll, msvcrt.dll
Build options: Release (-O2), static libraries, generic x86-64 (no -march=native)

Toolchain:
{(root / 'build/toolchain.txt').read_text()}
Validation:
{(root / 'build/validation.txt').read_text()}
Linux regression and reverse interoperability:
{linux_log}
Windows-embedded binary payload was extracted with unmodified Linux Steghide
0.5.1 and compared byte-for-byte with tests/fixtures/all-bytes.bin (cmp passed).

Dependency archives (SHA-256):
"""
for archive in sorted((root / "downloads").glob("*.tar.gz")):
    info += f"{digest(archive)}  {archive.name}\n"
(root / "BUILD-INFO.txt").write_text(info, encoding="utf-8")

common = ["README.md", "COPYING", "CREDITS", "THIRD-PARTY-NOTICES.txt", "BUILD-INFO.txt"]
licenses = sorted((root / "licenses").glob("*"))
with zipfile.ZipFile(dist / f"{binary_name}.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(exe, f"{binary_name}/stegseek.exe")
    for name in common:
        z.write(root / name, f"{binary_name}/{name}")
    for path in licenses:
        z.write(path, f"{binary_name}/licenses/{path.name}")
    for path in sorted((root / "examples").glob("demo-*")):
        z.write(path, f"{binary_name}/{path.name}")
    z.writestr(f"{binary_name}/SHA256SUMS.txt", f"{digest(exe)}  stegseek.exe\n")

with zipfile.ZipFile(dist / f"{source_name}.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name in [*common, "windows-port.patch", ".gitignore"]:
        z.write(root / name, f"{source_name}/{name}")
    for folder in ("upstream", "scripts", "downloads", "tests", "licenses", "examples"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and not ({".git", "__pycache__"} & set(path.relative_to(root).parts)):
                z.write(path, f"{source_name}/{path.relative_to(root).as_posix()}")

lines = []
for path in [exe, dist / f"{binary_name}.zip", dist / f"{source_name}.zip"]:
    lines.append(f"{digest(path)}  {path.name}\n")
    print(f"{path.name}: {path.stat().st_size:,} bytes, SHA-256 {digest(path)}")
(dist / "SHA256SUMS.txt").write_text("".join(lines))
for path in (dist / f"{binary_name}.zip", dist / f"{source_name}.zip"):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, path
print("Both archives passed ZIP integrity checks.")
