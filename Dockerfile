#################################################
# Dockerfile for certbot-dns-norisnetwork image #
#################################################

FROM python:3.10.10-alpine3.17

LABEL image.maintainer="noris network <support@noris.de>"
LABEL image.url="https://github.com/noris-network/certbot-dns-norisnetwork"

# Build-time variable set by --build-arg
ARG BUILD_VERSION

# Install specific version of our PyPI library
RUN pip install certbot-dns-norisnetwork==${BUILD_VERSION}

ENTRYPOINT [ "certbot" ]
