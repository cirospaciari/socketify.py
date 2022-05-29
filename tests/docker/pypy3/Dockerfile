FROM pypy:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD [ "pypy3", "./main.py" ]