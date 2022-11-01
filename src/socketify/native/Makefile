LIBRARY_NAME := libsocketify
UWS_LIBRARY_NAME := libuwebsockets
CC := clang
CXX := clang++

ARCH := amd64
ifeq ($(PLATFORM), arm64)
	ARCH := arm64
endif
ifeq ($(PLATFORM), arm)
	ARCH := arm64
endif

clean:
	cd ../uWebSockets/uSockets && rm -f *.o *.a *.so
	cd ../uWebSockets/ && rm -f *.o *.a *.so
	rm -f *.o *.a *.so *.dll
#	rm -rf ../uWebSockets/uSockets/boringssl/amd64
#	rm -rf ../uWebSockets/uSockets/boringssl/arm64

windows:
	$(MAKE) clean
	# build boringssl 
	cd ../uWebSockets/uSockets/boringssl && mkdir -p amd64 && cd amd64 && cmake -DCMAKE_BUILD_TYPE=Release -GNinja .. && ninja crypto ssl

	# build lsquic
	cd ../uWebSockets/uSockets/lsquic && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBORINGSSL_DIR=../boringssl -DCMAKE_BUILD_TYPE=Release -DLSQUIC_BIN=Off . && msbuild ALL_BUILD.vcxproj

	# build windows
	cl /MD /W3 /D WIN32_LEAN_AND_MEAN /D \"UWS_WITH_PROXY\" /D \"LIBUS_USE_LIBUV\" /D \"LIBUS_USE_QUIC\" /I ../uWebSockets/uSockets/lsquic/include /I ../uWebSockets/uSockets/lsquic/wincompat /I ../uWebSockets/uSockets/boringssl/include /D \"LIBUS_USE_OPENSSL\" /std:c++17 /I ../uWebSockets/uSockets/src ../uWebSockets/uSockets/src/*.c ../uWebSockets/uSockets/src/crypto/sni_tree.cpp ../uWebSockets/uSockets/src/eventing/*.c ../uWebSockets/uSockets/src/crypto/*.c  /I ../uWebSockets/src /EHsc /Ox /LD /Fe$(LIBRARY_NAME)_windows_amd64.so ./src/$(LIBRARY_NAME).cpp advapi32.lib ../uWebSockets/uSockets/boringssl/amd64/ssl/ssl.lib ../uWebSockets/uSockets/boringssl/amd64/crypto/crypto.lib ../uWebSockets/uSockets/lsquic/src/liblsquic/Debug/lsquic.lib

macos:
	$(MAKE) clean

	# build boringssl 
	cd ../uWebSockets/uSockets/boringssl && mkdir -p amd64 && cd amd64 && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_DEPLOYMENT_TARGET=10.14 .. && make crypto ssl

    # build boringssl for arm64 (cross compile)
	cd ../uWebSockets/uSockets/boringssl && mkdir -p arm64 && cd arm64 && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 .. && make crypto ssl

	# build lsquic
	cd ../uWebSockets/uSockets/lsquic && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBORINGSSL_DIR=../boringssl -DCMAKE_BUILD_TYPE=Release -DLSQUIC_BIN=Off . && make lsquic

	# build uWebSockets
	cd ../uWebSockets/uSockets && $(CC) -mmacosx-version-min=10.14 -I src -I lsquic/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c11 -O3 -c src/*.c src/eventing/*.c src/crypto/*.c
	cd ../uWebSockets/uSockets && $(CXX) -stdlib=libc++ -mmacosx-version-min=10.14 -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c++17 -O3 -c src/crypto/*.cpp
	cd ../uWebSockets/uSockets && $(AR) rvs uSockets_darwin_amd64.a *.o

	# build uWebSockets for arm64 (cross compile)
	cd ../uWebSockets/uSockets && $(CC) -target arm64-apple-macos11 -I src -I lsquic/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c11 -O3 -c src/*.c src/eventing/*.c src/crypto/*.c
	cd ../uWebSockets/uSockets && $(CXX) -stdlib=libc++ -target arm64-apple-macos11 -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c++17 -O3 -c src/crypto/*.cpp
	cd ../uWebSockets/uSockets && $(AR) rvs uSockets_darwin_arm64.a *.o

	# build CAPI + libsocketify
	$(CXX) -stdlib=libc++ -mmacosx-version-min=10.14 -I ./src -I ../uWebSockets/src -I ../uWebSockets/uSockets/src -I ../uWebSockets/capi -I ../uWebSockets/uSockets/lsquic/include -I ../uWebSockets/uSockets/boringssl/include -pthread -fPIC -std=c++17 -c -O3 ./src/$(LIBRARY_NAME).cpp
	$(CXX) -stdlib=libc++ -mmacosx-version-min=10.14 -shared -undefined dynamic_lookup -o ../$(LIBRARY_NAME)_darwin_amd64.so  $(LIBRARY_NAME).o ../uWebSockets/uSockets/uSockets_darwin_amd64.a ../uWebSockets/uSockets/boringssl/amd64/ssl/libssl.a ../uWebSockets/uSockets/boringssl/amd64/crypto/libcrypto.a ../uWebSockets/uSockets/lsquic/src/liblsquic/liblsquic.a -flto  -fPIC -lz -luv

	# build CAPI + libsocketify for arm64 (cross compile)
	$(CXX) -stdlib=libc++ -target arm64-apple-macos11 -I ./src -I ../uWebSockets/src -I ../uWebSockets/uSockets/src -I ../uWebSockets/capi -I ../uWebSockets/uSockets/lsquic/include -I ../uWebSockets/uSockets/boringssl/include -pthread -fPIC -std=c++17 -c -O3 ./src/$(LIBRARY_NAME).cpp
	$(CXX) -stdlib=libc++ -target arm64-apple-macos11 -shared -undefined dynamic_lookup -o ../$(LIBRARY_NAME)_darwin_arm64.so  $(LIBRARY_NAME).o ../uWebSockets/uSockets/uSockets_darwin_amd64.a ../uWebSockets/uSockets/boringssl/amd64/ssl/libssl.a ../uWebSockets/uSockets/boringssl/amd64/crypto/libcrypto.a ../uWebSockets/uSockets/lsquic/src/liblsquic/liblsquic.a -flto  -fPIC -lz -luv

linux:
	$(MAKE) clean

	# build boringssl
	cd ../uWebSockets/uSockets/boringssl && mkdir -p ${ARCH} && cd ${ARCH} && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release .. && make crypto ssl

	# build lsquic
	cd ../uWebSockets/uSockets/lsquic && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBORINGSSL_DIR=../boringssl -DCMAKE_BUILD_TYPE=Release -DLSQUIC_BIN=Off . && make lsquic

	# build uWebSockets
	cd ../uWebSockets/uSockets && $(CC) -I src -I lsquic/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c11 -O3 -c src/*.c src/eventing/*.c src/crypto/*.c
	cd ../uWebSockets/uSockets && $(CXX) -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c++17 -O3 -c src/crypto/*.cpp
	cd ../uWebSockets/uSockets && $(AR) rvs uSockets_linux_$(ARCH).a *.o

	# build CAPI + libsocketify
	$(CXX) -I ./src -I ../uWebSockets/src -I ../uWebSockets/uSockets/src -I ../uWebSockets/capi -I ../uWebSockets/uSockets/lsquic/include -I ../uWebSockets/uSockets/boringssl/include -pthread -fPIC -std=c++17 -c -O3 ./src/$(LIBRARY_NAME).cpp
	$(CXX) -shared -static-libstdc++ -static-libgcc -s -o ../$(LIBRARY_NAME)_linux_amd64.so  $(LIBRARY_NAME).o ../uWebSockets/uSockets/uSockets_linux_$(ARCH).a ../uWebSockets/uSockets/boringssl/$(ARCH)/ssl/libssl.a ../uWebSockets/uSockets/boringssl/$(ARCH)/crypto/libcrypto.a ../uWebSockets/uSockets/lsquic/src/liblsquic/liblsquic.a -flto  -fPIC -lz -luv