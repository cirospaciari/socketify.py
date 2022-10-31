FROM pypy:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update
RUN apt install libuv1-dev libssl-dev -y
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD [ "pypy3", "./main.py" ]