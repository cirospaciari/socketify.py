FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --no-cache  git openssl-dev libffi-dev build-base python3-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD [ "python", "./main.py" ]