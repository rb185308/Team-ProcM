FROM ubuntu:16.04

MAINTAINER Arpita Agarwal

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

COPY ./requirements.txt /requirements.txt
COPY ./config_file.ini /config_file.ini
WORKDIR /
CMD pip3 install -r requirements.txt
COPY . /
ENTRYPOINT ["python3"]
CMD ["python3 procalive-new.py"]
