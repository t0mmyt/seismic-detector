FROM ubuntu:16.04
LABEL maintainer Tom Taylor <tom+dockerfiles@tomm.yt>

EXPOSE 8000

RUN apt-get -qq update &&\
    DEBIAN_FRONTEND=noninteractive apt-get -yqq install \
      python3 python3-pip && \
      pip3 install --upgrade --no-cache-dir pip numpy && \
    groupadd app && useradd -r -g app app

ARG SEISMIC_VER=1.0
COPY dist/seismic-${SEISMIC_VER}.tar.gz /opt
RUN pip3 install /opt/seismic-${SEISMIC_VER}.tar.gz

USER app
ENTRYPOINT [ "/usr/local/bin/run_gunicorn.sh" ]