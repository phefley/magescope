FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive 
# Setup the environment
RUN apt update && apt install -y python3 python3-pip python-pandas chromium-chromedriver

RUN mkdir /opt/magescope
COPY requirements.txt /opt/magescope/
COPY ./lib/ /opt/magescope/lib/

WORKDIR /opt/magescope/
RUN pip3 install -r requirements.txt

COPY magescope.py /opt/magescope/
RUN chmod +x magescope.py

ENTRYPOINT ["./magescope.py", "--driver", "/usr/bin/chromedriver"]

