FROM python:3.9.23-alpine3.22

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV GHC_TOKEN=<your-ghc-token>
ENV ORG=<your-org>

COPY . .

CMD [ "python", "./src/app.py" ]
