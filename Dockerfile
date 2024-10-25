#################################################
# Dockerfile for certbot-dns-norisnetwork image #
#################################################

FROM python:3.11-alpine

LABEL image.maintainer="noris network <support@noris.de>"
LABEL image.url="https://github.com/noris-network/certbot-dns-norisnetwork"

RUN pip install -U pip setuptools

# Build-time variable set by --build-arg
ARG BUILD_VERSION

# Install specific version of our PyPI library
RUN pip install certbot-dns-norisnetwork==${BUILD_VERSION}

ENTRYPOINT [ "certbot" ]
