#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUILD="$ROOT/build"
PREFIX="$BUILD/prefix"
JOBS=${JOBS:-8}
mkdir -p "$BUILD/deps" "$PREFIX" "$ROOT/dist" "$ROOT/downloads"
cd "$ROOT/downloads"
fetch() {
    local name=$1 url=$2 hash=$3
    if [ ! -f "$name" ]; then curl --fail --location --retry 3 "$url" -o "$name"; fi
    printf '%s  %s\n' "$hash" "$name" | sha256sum --check -
}
fetch libmcrypt-2.5.8.tar.gz https://deb.debian.org/debian/pool/main/libm/libmcrypt/libmcrypt_2.5.8.orig.tar.gz e4eb6c074bbab168ac47b947c195ff8cef9d51a211cdd18ca9c9ef34d27a373e
fetch mhash-0.9.9.9.tar.gz https://deb.debian.org/debian/pool/main/m/mhash/mhash_0.9.9.9.orig.tar.gz 73991e9e54bb392484a510943d4c5d395462181cc4abe53f863edec13c335403
fetch libjpeg-turbo-2.1.5.tar.gz https://deb.debian.org/debian/pool/main/libj/libjpeg-turbo/libjpeg-turbo_2.1.5.orig.tar.gz 254f3642b04e309fee775123133c6464181addc150499561020312ec61c1bf7c
fetch zlib-1.3.1.tar.gz https://zlib.net/fossils/zlib-1.3.1.tar.gz 9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23
for name in libmcrypt-2.5.8 mhash-0.9.9.9 libjpeg-turbo-2.1.5 zlib-1.3.1; do
    if [ ! -d "$BUILD/deps/$name" ]; then
        mkdir -p "$BUILD/deps/$name"
        tar -xzf "$name.tar.gz" --strip-components=1 -C "$BUILD/deps/$name"
    fi
done
export SOURCE_DATE_EPOCH=1727308800
if [ ! -f "$PREFIX/lib/libmcrypt.a" ]; then
    cd "$BUILD/deps/libmcrypt-2.5.8"
    # Old libtool flag is invalid when configure passes it directly to GCC.
    sed -i 's/LDFLAGS="\$LDFLAGS -no-undefined"/LDFLAGS="$LDFLAGS -Wl,--no-undefined"/' configure
    ./configure --build=x86_64-pc-linux-gnu --host=x86_64-w64-mingw32 --prefix="$PREFIX" --disable-shared --enable-static --disable-dynamic-loading CFLAGS='-O2' ac_cv_func_malloc_0_nonnull=yes ac_cv_func_realloc_0_nonnull=yes
    make -j"$JOBS"
    make install
fi
if [ ! -f "$PREFIX/lib/libmhash.a" ]; then
    cd "$BUILD/deps/mhash-0.9.9.9"
    # The legacy DLL stub must not define main in a static library.
    sed -i 's/^#if defined(WIN32) || defined (__CYGWIN__)$/#if 0 \/\* static Windows build: no DLL main stub *\//' lib/mhash.c
    ./configure --build=x86_64-pc-linux-gnu --host=x86_64-w64-mingw32 --prefix="$PREFIX" --disable-shared --enable-static CFLAGS='-O2' ac_cv_func_malloc_0_nonnull=yes ac_cv_func_realloc_0_nonnull=yes
    make -j"$JOBS"
    make install
fi
cmake -S "$BUILD/deps/libjpeg-turbo-2.1.5" -B "$BUILD/jpeg" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$ROOT/scripts/mingw64.cmake" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" -DENABLE_SHARED=OFF -DENABLE_STATIC=ON \
    -DWITH_TURBOJPEG=OFF -DWITH_SIMD=OFF
cmake --build "$BUILD/jpeg" -j "$JOBS"
cmake --install "$BUILD/jpeg"
cmake -S "$BUILD/deps/zlib-1.3.1" -B "$BUILD/zlib" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$ROOT/scripts/mingw64.cmake" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX"
cmake --build "$BUILD/zlib" --target zlibstatic -j "$JOBS"
cp "$BUILD/zlib/libzlibstatic.a" "$PREFIX/lib/libz.a"
cp "$BUILD/deps/zlib-1.3.1/zlib.h" "$BUILD/zlib/zconf.h" "$PREFIX/include/"
cmake -S "$ROOT/upstream" -B "$BUILD/windows" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$ROOT/scripts/mingw64.cmake" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_FIND_ROOT_PATH="$PREFIX;/usr/x86_64-w64-mingw32" \
    -DCMAKE_PREFIX_PATH="$PREFIX" -DBUILD_TESTING=OFF \
    -DMCRYPT_LIBRARY="$PREFIX/lib/libmcrypt.a" -DMHASH_LIBRARY="$PREFIX/lib/libmhash.a" \
    -DJPEG_LIBRARY="$PREFIX/lib/libjpeg.a" -DZLIB_LIBRARY="$PREFIX/lib/libz.a"
cmake --build "$BUILD/windows" -j "$JOBS"
cp "$BUILD/windows/src/stegseek.exe" "$ROOT/dist/stegseek.exe"
x86_64-w64-mingw32-strip "$ROOT/dist/stegseek.exe"
x86_64-w64-mingw32-objdump -p "$ROOT/dist/stegseek.exe" | sed -n '/DLL Name:/p'
sha256sum "$ROOT/dist/stegseek.exe"
