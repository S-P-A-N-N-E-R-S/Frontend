FROM ubuntu:21.04

# Silence interactive choices for region selection
ENV DEBIAN_FRONTEND=noninteractive

RUN  apt-get update \
     && apt-get install -y software-properties-common wget python3-pip autoconf automake libtool make g++

# install the QGIS Signing Key \
RUN wget -qO - https://qgis.org/downloads/qgis-2021.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import
RUN chmod a+r /etc/apt/trusted.gpg.d/qgis-archive.gpg

# Add QGIS repo
RUN add-apt-repository "deb https://qgis.org/ubuntu-ltr $(lsb_release -c -s) main"
RUN apt-get update

# Install QGIS
RUN apt-get install -y qgis qgis-plugin-grass

# Install protobuf 3.16 manually
WORKDIR /tmp
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.16.0/protobuf-cpp-3.16.0.tar.gz
RUN tar xf protobuf-cpp-3.16.0.tar.gz
WORKDIR protobuf-3.16.0
RUN ./autogen.sh
RUN ./configure
RUN make -j8
RUN make install
RUN ldconfig
WORKDIR /tmp
RUN rm -rf protobuf-3.16.0
