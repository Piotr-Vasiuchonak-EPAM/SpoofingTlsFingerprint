# Base image with Python 3.12
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir flask python-dotenv requests && \
    apt-get remove -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy your script and .env loader
COPY tls_spoof_wrapper.py /app/
COPY .env /app/

# Expose the port (from env at runtime)
EXPOSE 8888

# Run the wrapper script
CMD ["python", "tls_spoof_wrapper.py"]
