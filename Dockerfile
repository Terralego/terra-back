FROM ubuntu:bionic
ARG  requirements=requirements.txt
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir /code
ADD apt.txt /code/apt.txt

# project dependencies
RUN apt-get update
RUN apt-get install -y $(grep -vE "^\s*#" /code/apt.txt  | tr "\n" " ") && apt-get clean all && apt-get autoclean
RUN apt-get upgrade -y
RUN useradd -ms /bin/bash django --uid 1000
WORKDIR /code

ADD *requirements.txt /code/
ADD manage.py /code/manage.py
ADD tox.ini /code/tox.ini
ADD .coveragerc /code/.coveragerc
ADD setup.py /code/setup.py
ADD README.md /code/README.md

ADD terracommon /code/terracommon
ADD private /code/private
RUN chown django:django -R /code
USER django
RUN python3.6 -m venv venv
RUN /code/venv/bin/pip3.6 install setuptools wheel -U
RUN /code/venv/bin/pip3.6 install --no-cache-dir -r ./${requirements} --upgrade
USER django
RUN mkdir -p /code/public/static /code/public/media
