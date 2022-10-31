LIBRARY_NAME := libsocketify
UWS_LIBRARY_NAME := libuwebsockets

clean:
	cd ../uWebSockets/uSockets && rm -f *.o $(LIBRARY_NAME).a $(LIBRARY_NAME).so $(UWS_LIBRARY_NAME).a $(UWS_LIBRARY_NAME).so
	cd ../uWebSockets/ && rm -f *.o $(LIBRARY_NAME).a $(LIBRARY_NAME).so $(UWS_LIBRARY_NAME).a $(UWS_LIBRARY_NAME).so
	rm -f *.o $(LIBRARY_NAME).a $(LIBRARY_NAME).so $(UWS_LIBRARY_NAME).a $(UWS_LIBRARY_NAME).so

shared:

	$(MAKE) clean
	
	cd ../uWebSockets/uSockets && $(CC) -pthread -DLIBUS_USE_OPENSSL -DLIBUS_USE_LIBUV -std=c11 -Isrc -flto -fPIC -O3 -c src/*.c src/eventing/*.c src/crypto/*.c
	cd ../uWebSockets/uSockets && $(CXX) -std=c++17 -flto -fPIC -O3 -c src/crypto/*.cpp 
	cd ../uWebSockets/uSockets && $(AR) rvs uSockets.a *.o

	$(CXX) -c -O3 -std=c++17 -lz -luv -flto -fPIC -I ../uWebSockets/src -I ../uWebSockets/uSockets/src ../uWebSockets/capi/$(UWS_LIBRARY_NAME).cpp 
	$(CXX) -shared -o $(UWS_LIBRARY_NAME).so  $(UWS_LIBRARY_NAME).o ../uWebSockets/uSockets/uSockets.a -fPIC  -lz -luv -lssl -lcrypto

	$(CC) -c -O3 -luv -flto -fPIC -I ./src ./src/$(LIBRARY_NAME).c
	$(CC) -shared -o $(LIBRARY_NAME).so  $(LIBRARY_NAME).o -luv

	rm -f *.o