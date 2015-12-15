FROM ubuntu:14.04
MAINTAINER @x110dc

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get update -qq && \
  apt-get install -yq language-pack-en-base \
  python-dev \
  python python-pip && \
  dpkg-reconfigure locales
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

EXPOSE 80
COPY *.py /app/
ENTRYPOINT /bin/bash
