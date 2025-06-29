FROM alpine:3.22.0

RUN apk add --no-cache python3 py3-pip py3-pandas chromium-chromedriver py3-virtualenv

RUN mkdir /opt/magescope
COPY requirements.txt /opt/magescope/
WORKDIR /opt/magescope/

RUN pip3 install -r requirements.txt --break-system-packages

COPY ./lib/ /opt/magescope/lib/

COPY magescope.py /opt/magescope/

ENTRYPOINT ["python", "./magescope.py"]
