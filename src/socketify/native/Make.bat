@REM #download dependences
vcpkg install libuv zlib --triplet x64-windows
vcpkg install zlib:x64-windows-static
vcpkg install libevent:x64-windows-static
vcpkg integrate install
cp C:\vcpkg\installed\x64-windows\bin\uv.dll ..\uv.dll
@REM # build boringssl 
cd ../uWebSockets/uSockets/boringssl 
mkdir amd64 
cd amd64
cmake -DCMAKE_BUILD_TYPE=Release -GNinja .. && ninja crypto ssl
cd ../../lsquic
@REM # build lsquic
cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBORINGSSL_DIR=../boringssl -DCMAKE_BUILD_TYPE=Release -DLSQUIC_BIN=Off . && msbuild ALL_BUILD.vcxproj
cd ../../../native

@REM # build uWebSockets
cd ../uWebSockets/uSockets
clang -Wpedantic -Wall -Wextra -Wsign-conversion -Wconversion -D WIN32_LEAN_AND_MEAN -I lsquic/wincompat -I C:/vcpkg/packages/libuv_x64-windows/include -I src -I lsquic/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -std=c11 -O3 -c src/*.c src/eventing/*.c src/crypto/*.c -L C:/vcpkg/packages/libuv_x64-windows/lib
clang++ -Wpedantic -Wall -Wextra -Wsign-conversion -Wconversion -D WIN32_LEAN_AND_MEAN -I lsquic/wincompat -I C:/vcpkg/packages/libuv_x64-windows/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -std=c++2a -O3 -c src/crypto/*.cpp -L C:/vcpkg/packages/zlib_x64-windows/lib
ar rvs uSockets_windows_amd64.a *.o
cd ../../native

@REM # build CAPI + libsocketify
clang++ -Wpedantic -Wall -Wextra -Wsign-conversion -Wconversion -D WIN32_LEAN_AND_MEAN -I C:/vcpkg/packages/zlib_x64-windows/include -I C:/vcpkg/packages/libuv_x64-windows/include -I ./src -I ../uWebSockets/src -I ../uWebSockets/uSockets/src -I ../uWebSockets/capi -I ../uWebSockets/uSockets/lsquic/wincompat -I ../uWebSockets/uSockets/lsquic/include -I ../uWebSockets/uSockets/boringssl/include -pthread -std=c++2a -c -O3 ./src/libsocketify.cpp -L C:/vcpkg/packages/libuv_x64-windows/lib
clang++ -Wpedantic -Wall -Wextra -Wsign-conversion -Wconversion -shared -o ../libsocketify_windows_amd64.so  libsocketify.o ../uWebSockets/uSockets/uSockets_windows_amd64.a ../uWebSockets/uSockets/boringssl/amd64/ssl/ssl.lib ../uWebSockets/uSockets/boringssl/amd64/crypto/crypto.lib C:/vcpkg/packages/zlib_x64-windows/lib/zlib.lib ../uWebSockets/uSockets/lsquic/src/liblsquic/Debug/lsquic.lib -luv -L C:/vcpkg/packages/libuv_x64-windows/lib
