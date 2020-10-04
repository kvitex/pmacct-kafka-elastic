FROM python:3.6.11-alpine3.12

WORKDIR /opt/app

RUN apk add build-base
COPY requirements.txt ./
RUN  pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
COPY pmacct-kafka-elastic.py ./
 
CMD [ "/usr/bin/env", "python3", "-u", "pmacct-kafka-elastic.py" ]
