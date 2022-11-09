FROM python:3.11-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache libuv-dev git zlib-dev openssl-dev libffi-dev build-base make cmake perl go python3-dev libstdc++ gcompat libc6-compat bsd-compat-headers clang musl-dev lld compiler-rt compiler-rt-static
RUN git clone https://github.com/cirospaciari/socketify.py.git
RUN cd ./socketify.py && git submodule update --init --recursive --remote

COPY Makefile ./socketify.py/src/socketify/native/Makefile
RUN cd ./socketify.py/src/socketify/native/ && make alpine
RUN cd ./socketify.py && pip install .

COPY . .

EXPOSE 3000

CMD [ "python", "./main.py" ]