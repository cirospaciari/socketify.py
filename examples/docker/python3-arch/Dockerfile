FROM archlinux:latest

WORKDIR /usr/src/app

COPY requirements.txt ./


RUN yes | pacman -Sy python python-pip libuv openssl git
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD [ "python", "./main.py" ]