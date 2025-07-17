# cms/tls_spoofing/SpoofingTlsFingerprint/tls_spoof_wrapper.dockerfile

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir requests python-dotenv && \
    apt-get remove -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the proxy handler script and .env
COPY tls_spoof_wrapper.py /app/
COPY .env /app/

# Expose the port used by the wrapper
EXPOSE 8888

# Use standard proxy handler server
CMD ["python", "tls_spoof_wrapper.py"]
