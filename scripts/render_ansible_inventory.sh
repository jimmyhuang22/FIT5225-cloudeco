#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
INVENTORY_PATH="$PROJECT_ROOT/ansible/inventory.ini"

MASTER_IP="$(terraform -chdir="$TERRAFORM_DIR" output -raw master_public_ip)"
NODE_PUBLIC_IPS="$(terraform -chdir="$TERRAFORM_DIR" output -json node_public_ips)"
WORKER1_IP="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["k8s-worker1"])' <<<"$NODE_PUBLIC_IPS")"
WORKER2_IP="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["k8s-worker2"])' <<<"$NODE_PUBLIC_IPS")"

cat >"$INVENTORY_PATH" <<EOF
[k8s_master]
k8s-master ansible_host=${MASTER_IP} ansible_user=ubuntu

[k8s_workers]
k8s-worker1 ansible_host=${WORKER1_IP} ansible_user=ubuntu
k8s-worker2 ansible_host=${WORKER2_IP} ansible_user=ubuntu

[k8s_cluster:children]
k8s_master
k8s_workers
EOF

echo "Wrote $INVENTORY_PATH"
