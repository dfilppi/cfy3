# Docker image for nodecellar
#
# VERSION               0.0.1
FROM      ubuntu:14.04
MAINTAINER dfilppi

# Install dependencies - these must be set before running start.sh
ENV MONGO_HOST undefined
ENV MONGO_PORT 0
ENV NODECELLAR_PORT 0

#ENV INTERVAL 5

ADD node /node
ADD nodecellar /nodecellar

#startup script
ADD start.sh /

RUN chmod +x /start.sh

#RUN apt-get update

#    apt-get install -y python-setuptools wget make pbuilder python-mock python-configobj python-support cdbs git python-psutil && \
#    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python && \
#    git clone https://github.com/python-diamond/Diamond.git && \
#    git clone https://github.com/docker/docker-py.git && \
#    cd /Diamond && \
#    make builddeb && \
#    sudo dpkg -i build/diamond_*_all.deb && \
#    sudo mkdir /usr/share/diamond/collectors/dockercontainer && \
#    find /usr/share/diamond/collectors/  -type f -name "*.py" -print0 | xargs -0 sed -i 's/\/proc/\/host_proc/g' && \
#    cd /docker-py && \
#    python setup.py install && \
#    apt-get autoremove -y git python-setuptools make pbuilder python-mock && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/* && \
#    rm -rf /Diamond /diamond-DockerContainerCollector /docker-py #&& \
#    chmod +x /config_diamond.sh

