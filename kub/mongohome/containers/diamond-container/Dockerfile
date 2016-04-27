# Docker image containing the Diamond collector
#
# VERSION               0.0.1
FROM      ubuntu:14.04
MAINTAINER dfilppi

#add diamond config dir
ADD diamond /diamond
ADD patch /patch

#startup script
ADD start.sh /
ADD config.py /

RUN apt-get update && \
    apt-get install -y python-setuptools wget make pbuilder python-mock python-configobj python-support cdbs git python-psutil && \
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python && \
    git clone -b v4.0 https://github.com/python-diamond/Diamond.git && \
    cd /Diamond && \
    make builddeb && \
    sudo dpkg -i build/diamond_*_all.deb && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python ./get-pip.py && \
    pip install pika && \
    cp /patch/classes.py /usr/lib/pymodules/python2.7/diamond/utils && \
    apt-get autoremove -y git python-setuptools make pbuilder python-mock && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /Diamond /diamond-DockerContainerCollector /docker-py

