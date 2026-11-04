# Modified for the unofficial Windows port, 2026-11-04; see ../README.md and windows-port.patch.
if(WIN32)
  add_definitions(-DNOMINMAX -DWIN32_LEAN_AND_MEAN)
  add_definitions(-DSTEGSEEK_VERSION="0.6-win1")
else()
  add_definitions(-DHAVE_DEV_URANDOM -DHAVE_DEV_RANDOM -DHAVE_TERMIOS_H)
  add_definitions(-DSTEGSEEK_VERSION="0.6")
endif()
add_definitions(-DSTEGHIDE_VERSION="0.5.1")

set (sources
	"Arg.cc"
	"Arguments.cc" 
	"AssertionFailed.cc" 
	"AuFile.cc"
	"AuSampleValues.cc"
	"BFSAPHeuristic.cc"
	"BinaryIO.cc"
	"BitString.cc"
	"BmpFile.cc"
	"BmpPaletteSampleValue.cc"
	"BmpRGBSampleValue.cc"
	"BmpSampleValue.cc"
	"Cracker.cc"
	"CvrStgFile.cc"
	"DFSAPHeuristic.cc"
	"DMDConstructionHeuristic.cc"
	"Edge.cc"
	"EdgeIterator.cc"
	"EmbData.cc"
	"Embedder.cc"
	"EncryptionAlgorithm.cc"
	"EncryptionMode.cc"
	"error.cc"
	"Extractor.cc"
	"Graph.cc"
	"JpegFile.cc"
	"JpegSampleValue.cc"
	"MatchingAlgorithm.cc"
	"Matching.cc"
	"MCryptPP.cc"
	"MHashKeyGen.cc"
	"MHashPP.cc"
	"msg.cc"
	"PasswordCracker.cc"
	"ProgressOutput.cc"
	"PseudoRandomSource.cc"
	"RandomSource.cc"
	"RGBTriple.cc"
	"SampleValueAdjacencyList.cc"
	"SampleValue.cc"
	"SeedCracker.cc"
	"Selector.cc"
	"Session.cc"
	"SMDConstructionHeuristic.cc"
	"SteghideError.cc"
	"Terminal.cc"
	"Utils.cc"
	"Vertex.cc"
	"WavChunk.cc"
	"WavChunkHeader.cc"
	"WavChunkUnused.cc"
	"WavFile.cc"
	"WavFormatChunk.cc"
	"WavPCMSampleValue.cc"
	"WKSConstructionHeuristic.cc"
)

file(GLOB headers
    "*.h"
)

add_library(stegseek_lib ${sources} ${headers})
find_path(MCRYPT_INCLUDE_PATH mcrypt.h)
find_path(MHASH_INCLUDE_PATH mhash.h REQUIRED)
find_package(JPEG REQUIRED)
find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)
target_include_directories(stegseek_lib PUBLIC ${MCRYPT_INCLUDE_PATH} ${MHASH_INCLUDE_PATH})

set(CMAKE_CXX_FLAGS_RELEASE "-O2")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -s")

add_executable(stegseek main.cc)

install(TARGETS stegseek EXPORT stegseek DESTINATION bin)

find_library(MCRYPT_LIBRARY mcrypt)
find_library(MHASH_LIBRARY mhash)
find_library(JPEG_LIBRARY jpeg)
target_link_libraries(stegseek_lib PUBLIC Threads::Threads ZLIB::ZLIB ${MCRYPT_LIBRARY} ${MHASH_LIBRARY} JPEG::JPEG)
target_link_libraries(stegseek PRIVATE stegseek_lib)
if(WIN32)
  enable_language(RC)
  target_sources(stegseek PRIVATE windows.rc)
  target_link_libraries(stegseek_lib PUBLIC bcrypt)
  if(MINGW)
    target_link_options(stegseek PRIVATE -static -static-libgcc -static-libstdc++)
  endif()
endif()
