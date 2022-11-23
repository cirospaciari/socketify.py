@REM #download dependences
$ErrorActionPreference = 'SilentlyContinue'
$Env:CC='clang'
$Env:CXX='clang++'

git clone --recursive https://github.com/cirospaciari/socketify.py.git
cd socketify.py\src\socketify\native
vcpkg install libuv:x64-windows-static-md
vcpkg integrate install

cd ..\uWebSockets\uSockets\boringssl 
mkdir amd64 
cd amd64
cmake -DCMAKE_BUILD_TYPE=Release -GNinja .. && ninja crypto ssl

cd ..\..\..\..\
cl /MD /W3 /D /EHsc /Zc:__cplusplus /Ox /DLL /D_WINDLL /LD /D "NOMINMAX" /D "WIN32_LEAN_AND_MEAN" /D "UWS_NO_ZLIB" /D "UWS_WITH_PROXY" /D "LIBUS_USE_LIBUV" /I native/src/ /I uWebSockets/src /I uWebSockets/capi /I uWebSockets/uSockets/boringssl/include /D "LIBUS_USE_OPENSSL" /std:c++20 /I C:\vcpkg\packages\libuv_x64-windows-static-md\include /I uWebSockets/uSockets/src /Felibsocketify_windows_amd64.dll ./native/src/libsocketify.cpp uWebSockets/uSockets/src/*.c uWebSockets/uSockets/src/crypto/*.cpp uWebSockets/uSockets/src/eventing/*.c uWebSockets/uSockets/src/crypto/*.c advapi32.lib uWebSockets/uSockets/boringssl/amd64/ssl/ssl.lib uWebSockets/uSockets/boringssl/amd64/crypto/crypto.lib C:\vcpkg\installed\x64-windows-static-md\lib\uv_a.lib iphlpapi.lib userenv.lib psapi.lib user32.lib