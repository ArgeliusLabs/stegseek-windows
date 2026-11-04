# StegSeek for Windows

An unofficial native Windows x64 port of [Rick de Jager's StegSeek](https://github.com/RickdeJager/stegseek), packaged by [Argelius Labs](https://github.com/ArgeliusLabs) for the SEC587 lab and anyone who wants to run StegSeek directly on Windows. Release: **0.6-win1**.

**[Download the Windows ZIP](https://github.com/ArgeliusLabs/stegseek-windows/releases/latest/download/stegseek-0.6-win1-windows-x64.zip)** · [All releases](https://github.com/ArgeliusLabs/stegseek-windows/releases) · [Matching source](https://github.com/ArgeliusLabs/stegseek-windows/releases/latest/download/stegseek-0.6-win1-source.zip)

## Credit to the original projects

**Rick de Jager created [StegSeek](https://github.com/RickdeJager/stegseek)**, including its fast wordlist cracking and seed-search features. StegSeek is based on **[Steghide](https://steghide.sourceforge.net/), created by Stefan Hetzl**, and the work of its contributors. Those projects deserve the credit for the steganography, extraction, and cracking functionality.

Argelius Labs provides the Windows portability changes, precompiled executable, packaging, documentation, and Windows interoperability tests in this repository. This is an unofficial port; it is not an official release or endorsement from either upstream project. The original [credits](CREDITS), [GPL license](COPYING), and [dependency notices](THIRD-PARTY-NOTICES.txt) are preserved.

## Students: run the precompiled version

Extract `stegseek-0.6-win1-windows-x64.zip`, open PowerShell in the extracted folder, and run:

```powershell
# Look for Steghide metadata without knowing the password:
.\stegseek.exe --seed .\image.jpg

# Try passwords from a wordlist and recover the hidden file:
.\stegseek.exe .\image.jpg .\wordlist.txt .\recovered.bin

# Show options:
.\stegseek.exe --help

# Include the inherited Steghide commands:
.\stegseek.exe --help -v
```

The executable runs directly on 64-bit Windows. Students do not need WSL, Python, a compiler, additional DLLs, or an installer. Target: Windows 10 version 1903 or later / Windows 11, x64. ARM64 and older Windows releases have not been tested. This is a command-line program; launch it from a terminal. It does not have a graphical interface.

`--seed` searches the Steghide embedding patterns. It can report a **possible** seed, the size of the embedded data, and the encryption method. It can recover the content without a password only when encryption was disabled at embedding time. Encrypted content still needs a password or a successful wordlist attack. A complete seed scan may take minutes; use `-t 4` to limit it to four threads. Ctrl+C stops a scan.

This detects Steghide data in supported JPEG, BMP, WAV, and AU files. It is not a general detector for every steganography technique, and a possible seed is not proof that recoverable content exists. PNG is not a supported Steghide carrier format. Failure to find a password only means the supplied guesses failed.

Use quoted paths when they contain spaces. Use `-xf` to choose the extracted file, or the default `<carrier filename>.out` is written in the current directory. Existing files prompt before overwrite; `-f` forces overwrite. Exit status is 0 on success, 1 on failure.

## Which wordlist does it use by default?

**When no wordlist is supplied, this Windows build opens `rockyou.txt` in the current working directory.** The filename is `rockyou.txt`, not `rock.txt`. It does not automatically download a list or search other folders. The current working directory is the folder your terminal is in, which may differ from the folder containing `stegseek.exe`.

For example, if the terminal prompt is `C:\tools\stegseek>` and that folder contains `rockyou.txt`, these commands use the same list:

```powershell
.\stegseek.exe --crack ".\image with spaces.jpg"
.\stegseek.exe --crack ".\image with spaces.jpg" "C:\tools\stegseek\rockyou.txt"
```

To use a different list or see the selected list:

```powershell
.\stegseek.exe --crack .\image.jpg "C:\wordlists\my-list.txt" .\recovered.bin
.\stegseek.exe --crack .\image.jpg -v
```

Supply an uncompressed text wordlist with one password per line (LF or CRLF; UTF-8 without a BOM). If `rockyou.txt` is absent and no list is specified, cracking reports that it could not open the wordlist. `--seed` does not use a wordlist and does not discover or cache the encryption password.

The full RockYou wordlist is not bundled. The repository and Windows ZIP include a clearly named `demo-wordlist.txt` with three guesses for the example images. To try the default lookup with the demo, copy that sample to `rockyou.txt` in a separate demo folder. Do not replace your real wordlist with it.

You can get the full list from [RockYou in SecLists](https://github.com/danielmiessler/SecLists/blob/master/Passwords/Leaked-Databases/rockyou.txt.tar.gz). Download the raw archive and extract it until you have `rockyou.txt`; do not pass the `.tar.gz` file to StegSeek. Put `rockyou.txt` in your terminal's current directory, or supply its full path as shown above.

## Try the included examples

The ZIP includes a tiny demonstration: `demo-encrypted.jpg`, `demo-unencrypted.jpg`, and `demo-wordlist.txt`. These files are also in the repository's [`examples/`](examples) directory. Run the following from the extracted Windows ZIP folder:

```powershell
.\stegseek.exe --seed .\demo-unencrypted.jpg .\seed-result.bin
.\stegseek.exe --seed .\demo-encrypted.jpg
.\stegseek.exe .\demo-encrypted.jpg .\demo-wordlist.txt .\cracked-result.bin
```

Both recovered files should match `demo-expected.bin` byte-for-byte. The demo passphrase is `moana5`. The encrypted seed scan reports metadata; the wordlist attack recovers the contents.

## Build from source

The supplied source archive contains the patched upstream source, all four dependency source archives, tests, and build scripts. A Git clone includes the same project source and scripts; the build script downloads the pinned dependency archives if they are missing. The compiler runs on Linux (including Ubuntu under WSL); the result is a Windows PE executable. On Ubuntu 24.04:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends build-essential g++-mingw-w64-x86-64-posix cmake ninja-build curl ca-certificates python3
bash scripts/build-windows.sh
```

The result is `dist/stegseek.exe`. The script checks SHA-256 hashes of the pinned dependency archives before building static libraries. It patches two legacy build issues: libmcrypt's GCC linker flag and mhash's obsolete DLL `main` stub. Build paths should not contain spaces. `JOBS=4 bash scripts/build-windows.sh` limits compiler parallelism. To rebuild dependency libraries after changes, use a fresh source extraction/build directory.

Source baseline: upstream commit `58969789a5724701048d5d5510af84098cc1f1ea`. The bundled `windows-port.patch` records the changes. The port adds Windows console handling and OS random bytes, binary pipe I/O, UTF-8 path support on modern Windows, 64-bit wordlist positioning and metrics, atomic worker flags, safe worker error propagation, and complete coverage of all 2^32 seeds. It retains upstream's steganography and cryptography implementations.

## Validate

From Windows, with Python installed for development only:

```powershell
python .\scripts\test-windows.py
python .\scripts\test-windows.py --full-seed
python .\scripts\test-windows.py --full-seed --large-wordlist
```

The fixtures were created by Ubuntu's unmodified Steghide 0.5.1, independently of this port. They cover encrypted recovery, metadata detection, and unencrypted seed extraction across 15 carrier variants. The native tests also cover binary payloads, standard streams, CRLF/LF wordlists, thread boundaries, missing files, wrong passwords, overwrite protection, and paths with spaces/non-ASCII characters. Tests run with PATH reduced to Windows System32 to exclude accidentally installed third-party DLLs. The full test additionally scans a clean carrier through the seed search space.

To regenerate the fixtures in Linux, install `steghide` and run `python3 scripts/make-fixtures.py`. Embedding uses random bytes, so fixture file hashes can change. To verify Windows-to-Linux interoperability after the native test:

```bash
steghide extract -sf build/windows-embedded.bmp -xf build/linux-recovered.bin -p Win587 -f
cmp tests/fixtures/all-bytes.bin build/linux-recovered.bin
```

## Redistribution

StegSeek/Steghide is GPL-2.0-or-later. Copyright remains with its upstream authors; this is an unofficial port and is not an upstream Windows release. `COPYING` and `CREDITS` are included. The binary statically links libmcrypt 2.5.8, mhash 0.9.9.9, libjpeg-turbo 2.1.5, zlib 1.3.1, and compiler/thread runtimes. See `THIRD-PARTY-NOTICES.txt` and `licenses/` in the release.

Distribute the matching `stegseek-0.6-win1-source.zip` alongside the binary ZIP, with equal access to recipients. It supplies the corresponding source and the scripts needed to rebuild/relink the program and libraries. The executable is unsigned.
