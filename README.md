# Sentra

A central AI-driven security watcher

## Commands

- Recommended Local Image Name - `sentra/main/batch-script`
- Build docker script
  - in local - `docker build -t container_name .`
- Run docker script
  - in local inside docker - `docker run --rm --env-file .env container_name`
  - in local interpretor - `python3 securityhub-csv.py`
- Push docker image
  - Tag your docker image - `docker tag YOUR_LOCAL_IMAGE:tag YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_REPO_NAME:tag`
  - Authenticate to aws ecr in local terminal - `aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com`
  - Push to ECR - `docker push YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_REPO_NAME:tag`
  - Register batch job defenition - `aws batch register-job-definition --cli-input-json file://FILE_NAME.json`
