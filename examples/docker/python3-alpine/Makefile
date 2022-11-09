LIBRARY_NAME := libsocketify
UWS_LIBRARY_NAME := libuwebsockets

ARCH := amd64
ifeq ($(PLATFORM), arm64)
	ARCH := arm64
endif
ifeq ($(PLATFORM), aarch64)
	ARCH := arm64
endif
ifeq ($(PLATFORM), arm)
	ARCH := arm64
endif

clean:
	cd ../uWebSockets/uSockets && rm -f *.o *.a *.so *.obj *.lib *.dll
	cd ../uWebSockets/ && rm -f *.o *.a *.so *.obj *.lib *.dll
	rm -f *.o *.a *.so *.dll *.obj *.lib
	rm -rf ../uWebSockets/uSockets/boringssl/amd64
	rm -rf ../uWebSockets/uSockets/boringssl/vcpkg
	rm -rf ../uWebSockets/uSockets/boringssl/arm64

alpine:
	$(MAKE) clean

	# build boringssl
	cd ../uWebSockets/uSockets/boringssl && mkdir -p $(ARCH) && cd $(ARCH) && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release .. && make crypto ssl

	# build lsquic
	cd ../uWebSockets/uSockets/lsquic && cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBORINGSSL_DIR=../boringssl -DCMAKE_BUILD_TYPE=Release -DLSQUIC_BIN=Off . && make lsquic

	# build uWebSockets
	cd ../uWebSockets/uSockets && $(CC) -I src -I lsquic/include -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c11 -O3 -c src/*.c src/eventing/*.c src/crypto/*.c
	cd ../uWebSockets/uSockets && $(CXX) -I boringssl/include -DUWS_WITH_PROXY -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -DLIBUS_USE_QUIC -pthread -fPIC -std=c++17 -O3 -c src/crypto/*.cpp
	cd ../uWebSockets/uSockets && $(AR) rvs uSockets_linux_$(ARCH).a *.o

	# build CAPI + libsocketify
	$(CXX) -I ./src -I ../uWebSockets/src -I ../uWebSockets/uSockets/src -I ../uWebSockets/capi -I ../uWebSockets/uSockets/lsquic/include -I ../uWebSockets/uSockets/boringssl/include -DUWS_WITH_PROXY -pthread -fPIC -std=c++17 -c -O3 ./src/$(LIBRARY_NAME).cpp
	$(CXX) -shared -static-libstdc++ -static-libgcc -s -o ../$(LIBRARY_NAME)_linux_$(ARCH).so  $(LIBRARY_NAME).o ../uWebSockets/uSockets/uSockets_linux_$(ARCH).a ../uWebSockets/uSockets/boringssl/$(ARCH)/ssl/libssl.a ../uWebSockets/uSockets/boringssl/$(ARCH)/crypto/libcrypto.a ../uWebSockets/uSockets/lsquic/src/liblsquic/liblsquic.a -flto  -fPIC -lz -luv