FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    freecad \
    poppler-utils \
    imagemagick \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy scripts so the container can run the export script
COPY . /workspace

ENTRYPOINT ["python3", "scripts/export_dxf.py"]
