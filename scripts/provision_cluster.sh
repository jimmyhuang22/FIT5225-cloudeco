#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

AUTO_APPROVE="${AUTO_APPROVE:-0}"
SKIP_TERRAFORM_APPLY="${SKIP_TERRAFORM_APPLY:-0}"

echo "==> Initialising Terraform"
terraform -chdir="$TERRAFORM_DIR" init

if [[ "$SKIP_TERRAFORM_APPLY" == "1" ]]; then
  echo "==> Skipping Terraform apply because SKIP_TERRAFORM_APPLY=1"
else
  echo "==> Applying Terraform infrastructure"
  if [[ "$AUTO_APPROVE" == "1" ]]; then
    terraform -chdir="$TERRAFORM_DIR" apply -auto-approve -var=run_cluster_bootstrap=false
  else
    terraform -chdir="$TERRAFORM_DIR" apply -var=run_cluster_bootstrap=false
  fi
fi

echo "==> Terraform outputs"
terraform -chdir="$TERRAFORM_DIR" output

echo "==> Running Ansible cluster bootstrap"
"$PROJECT_ROOT/scripts/bootstrap_cluster.sh"

echo "==> Provisioning complete"
