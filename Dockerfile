# Use a lightweight Python image
FROM python:3.9-slim

WORKDIR /app

# Install dependencies (AWS CLI for local debugging, boto3 for prod)
RUN pip install boto3 pandas awscli && \
    # Clean up to reduce image size
    rm -rf /var/lib/apt/lists/* && \
    pip cache purge

# Copy script
COPY sentra-batch-script.py .

# Set default AWS region (can override via environment variables)
ENV AWS_DEFAULT_REGION=us-east-1

# Entrypoint
CMD ["python", "sentra-batch-script.py"]
