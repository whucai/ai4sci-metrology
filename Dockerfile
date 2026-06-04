# Dockerfile for AI Reproducibility Metrology
# Minimal reproduction environment: Python 3.11 + scientific packages
#
# Build:  docker build -t ai4sci-metrology .
# Run:    docker run --rm ai4sci-metrology python scripts/run_docker_reproduction.py

FROM python:3.11-slim

RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scipy \
    requests

WORKDIR /app

# Copy source code
COPY src/ src/
COPY scripts/run_docker_reproduction.py scripts/

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "scripts/run_docker_reproduction.py"]
