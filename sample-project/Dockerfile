# Use a lightweight Python image
FROM python:3.9-slim

WORKDIR /app

# Install dependencies (AWS CLI for local debugging, boto3 for prod)
RUN pip install boto3 pandas awscli && \
    # Clean up to reduce image size
    rm -rf /var/lib/apt/lists/* && \
    pip cache purge

# Copy script
COPY securityhub-csv.py .

# Set default AWS region (can override via environment variables)
ENV AWS_DEFAULT_REGION=eu-north-1

# ----------------------------
# Fargate-Specific Configurations
# ----------------------------
# 1. Ensure the script uses container credentials (critical for Fargate)
ENV AWS_CONTAINER_CREDENTIALS_RELATIVE_URI=/v2/credentials

# 2. Set Python unbuffered mode for better logging in Fargate
ENV PYTHONUNBUFFERED=1

# 3. (Optional) Reduce boto3 verbosity in prod
ENV AWS_LOG_LEVEL=WARNING

# Entrypoint
CMD ["python", "securityhub-csv.py"]