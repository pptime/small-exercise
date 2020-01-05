FROM python:3.6.10-slim-stretch

RUN apt-get update

RUN apt-get install -y bash locales

COPY . /tmp/code/

WORKDIR /tmp/code/

RUN pip install -r requirements.txt && python setup.py install && mkdir /work

WORKDIR /work

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && rm -rf /tmp/code/
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

CMD ["calsum", "--http-address=0.0.0.0", "--app-debug=false", "--enable-auto-fork", "--thread-num=10"]