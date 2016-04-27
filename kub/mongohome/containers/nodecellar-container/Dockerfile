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

