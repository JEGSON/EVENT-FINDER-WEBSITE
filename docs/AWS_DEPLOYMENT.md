# AWS Deployment Runbook

This flow ensures `terraform apply` can recreate the stack without any manual steps on the EC2 host. The only runtime inputs Terraform needs are the public container images for the API and web frontend.

## 1. Prerequisites
- AWS account with permissions to manage ECR, IAM, EC2, and the resources in `infra/terraform`.
- AWS CLI v2 configured locally (or credentials available to GitHub Actions).
- (Recommended) GitHub → AWS IAM role for OIDC (`AWS_GITHUB_OIDC_ROLE_ARN` secret). Access keys also work but are less secure.

### Create ECR repositories
```bash
aws ecr create-repository --repository-name event-finder-api
aws ecr create-repository --repository-name event-finder-web
```
Both commands are idempotent—rerunning them simply confirms the repositories exist.

Record your AWS account ID and target region; they form the image URIs:
```
${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-api
${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-web
```

## 2. Configure GitHub Actions
The existing workflow `.github/workflows/docker.yml` now pushes images to both ECR and (optionally) Docker Hub. Populate these repository settings before pushing to `main`:

| Type     | Name                        | Purpose                                                 |
|----------|-----------------------------|---------------------------------------------------------|
| Secret   | `AWS_GITHUB_OIDC_ROLE_ARN`* | IAM role ARN GitHub can assume (preferred).             |
| Secret   | `AWS_ACCESS_KEY_ID`†        | Access key fallback when no OIDC role is supplied.      |
| Secret   | `AWS_SECRET_ACCESS_KEY`†    | Matching secret access key.                             |
| Variable | `AWS_ACCOUNT_ID`            | Your 12-digit AWS account number.                       |
| Variable | `AWS_REGION`                | Region for both Terraform and ECR (e.g. `us-east-1`).   |
| Variable | `PROJECT_NAME`              | Optional; defaults to `event-finder`.                   |


a. *Provide either the OIDC role OR the access keys. OIDC is preferred.*  
b. †Leave the access key pair blank if you use an OIDC role.

If you also want Docker Hub pushes, set `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` (and optional `DOCKERHUB_NAMESPACE`). They are not required for the AWS flow.

## 3. Trigger the Docker build
Push to `main` (or use the “Run workflow” button) to execute the Docker build matrix. On success you will have:
```
${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-api:latest
${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-web:latest
```

Grab the exact tags from the workflow summary if you prefer to pin to a specific commit SHA.

## 4. Feed Terraform the image URIs
You can provide the image strings via `terraform.tfvars`, CLI flags, or repository variables consumed by `.github/workflows/terraform.yml`.

Example `infra/terraform/terraform.tfvars`:
```hcl
aws_region  = "us-east-1"
project_name = "event-finder"
api_image    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-api:latest"
web_image    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/event-finder-web:latest"
ssh_key_name = "eventfinder-key"
allowed_ssh_cidr = "203.0.113.12/32"
```

Or, set repository variables so the Terraform GitHub Action can run unattended:
- `API_IMAGE`
- `WEB_IMAGE`

After that, run Terraform locally or via the workflow:
```bash
cd infra/terraform
terraform init
terraform plan -var "api_image=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/event-finder-api:latest" \
               -var "web_image=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/event-finder-web:latest"
terraform apply
```

## 5. Tear-down / Rebuild checks
- `terraform destroy` removes the EC2 instance and networking; reapply to rebuild from the published images.
- Because the EC2 user data pulls images from ECR, no manual SSH steps are required. Cloud-init runs Docker Compose immediately after boot.

## 6. Optional extras
- Enable lifecycle rules on the ECR repositories to purge old image tags automatically.
- Add a nightly GitHub workflow dispatch to republish images if base dependencies change.
- Layer a CD step that triggers the Terraform workflow after a successful image push.

With these pieces in place, `terraform apply` + an image tag update is all that’s needed for a fresh deployment.
