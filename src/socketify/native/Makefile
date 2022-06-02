LIBRARY_NAME := libsocketify

default:
	$(CC) -c -O3 -luv -flto -fPIC -I ./src ./src/$(LIBRARY_NAME).c
	$(CC) -shared -o $(LIBRARY_NAME).so  $(LIBRARY_NAME).o -luv