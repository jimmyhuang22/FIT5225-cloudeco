#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANSIBLE_DIR="$PROJECT_ROOT/ansible"

export ANSIBLE_CONFIG="${ANSIBLE_CONFIG:-$ANSIBLE_DIR/ansible.cfg}"
export ANSIBLE_HOME="${ANSIBLE_HOME:-$PROJECT_ROOT/.ansible-home}"
export ANSIBLE_LOCAL_TEMP="${ANSIBLE_LOCAL_TEMP:-$PROJECT_ROOT/.ansible-tmp}"
export ANSIBLE_REMOTE_TEMP="${ANSIBLE_REMOTE_TEMP:-/tmp/.ansible-ubuntu}"
export ANSIBLE_HOST_KEY_CHECKING="${ANSIBLE_HOST_KEY_CHECKING:-False}"

mkdir -p "$ANSIBLE_HOME" "$ANSIBLE_LOCAL_TEMP"

echo "==> Rendering Ansible inventory from Terraform outputs"
"$PROJECT_ROOT/scripts/render_ansible_inventory.sh"

echo "==> Removing stale SSH host keys for Terraform-managed node IPs"
node_public_ips_json="$(terraform -chdir="$PROJECT_ROOT/terraform" output -json node_public_ips)"
while IFS= read -r ip; do
  ssh-keygen -R "$ip" >/dev/null 2>&1 || true
done < <(python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin).values()))' <<<"$node_public_ips_json")

echo "==> Waiting for SSH on all Kubernetes nodes"
ansible -i "$ANSIBLE_DIR/inventory.ini" k8s_cluster \
  -m ansible.builtin.wait_for_connection \
  -a "timeout=600 sleep=5 connect_timeout=10"

echo "==> Checking Ansible connectivity"
ansible -i "$ANSIBLE_DIR/inventory.ini" k8s_cluster -m ping

echo "==> Checking Ansible playbook syntax"
ansible-playbook -i "$ANSIBLE_DIR/inventory.ini" --syntax-check "$ANSIBLE_DIR/site.yml"

echo "==> Bootstrapping Kubernetes and deploying CloudEco"
ansible-playbook -i "$ANSIBLE_DIR/inventory.ini" "$ANSIBLE_DIR/site.yml"
