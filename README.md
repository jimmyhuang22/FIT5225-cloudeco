# CloudEco Waste Detection API

FastAPI + YOLO object detection service for FIT5225 Assessment 1. The service exposes CPU-only inference endpoints and is deployed to a kubeadm Kubernetes cluster on three GCP virtual machines for horizontal scaling benchmarks.

## Source Archive

This repository was imported from the existing local CloudEco A1 project on 22 October 2026. Its initial commit records that snapshot; earlier development commits were not available in the local project or submission archive. Benchmark results below are historical assignment results, not a new deployment or benchmark run.

```bash
git clone https://github.com/jimmyhuang22/FIT5225-cloudeco.git
cd FIT5225-cloudeco
```

The repository includes application code, assigned model weights, sample images, infrastructure templates, a Terraform provider lock file, and the final benchmark summary CSV. Local credentials, actual deployment variables, Terraform state, generated Ansible inventory, caches, and temporary benchmark logs are excluded. Deployment requires your own GCP configuration; the original container image reference below is retained as historical assignment configuration.

## API Endpoints

- `GET /healthz`: process health check.
- `GET /readyz`: readiness check. This returns ready only after the YOLO model has loaded and warmup has completed.
- `POST /api/predict`: accepts `{ "uuid": "...", "image": "<base64>" }` and returns detections, boxes, and YOLO timing fields.
- `POST /api/annotate`: accepts the same request body and returns `{ "uuid": "...", "image": "<annotated base64 image>" }`.

Interactive API documentation is available at `/docs` when the service is running.

## Final Benchmark Version

The final submitted version is `v13`:

```text
australia-southeast1-docker.pkg.dev/sigma-icon-489807-g5/fit5225-a1-repo/cloudeco-waste-api:v13
```

v13 reduced the container footprint while preserving the v12-5 benchmark-first runtime profile. The final benchmark sweep is reported in `benchmark_logs/v13_sweep_20260429_123944_summary.csv`; the maximum stable 8-pod point reached 48.02 QPS with 24 concurrent users and 467 ms average latency.

Runtime profile used for the final benchmark:

```text
MODEL_PATH=/app/models/best_model.pt
INFERENCE_MAX_WORKERS=1
IMGSZ=256
CONF_THRESHOLD=0.10
MAX_DET=20
ANNOTATION_MAX_SIDE=320
JPEG_QUALITY=50
```

This is a performance-first configuration. It reduces YOLO input size and annotated image output cost to improve throughput and latency under the 1 vCPU per pod constraint. The earlier balanced profile used a larger `IMGSZ=416`.

## Local Development

Create a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0+cpu torchvision==0.26.0+cpu
pip install -r requirements-dev.txt
```

Run the API locally:

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Smoke test `/api/predict`:

```bash
source .venv/bin/activate
API_URL=http://127.0.0.1:8000/api/predict PYTHONPATH=. python3 scripts/send_test_request.py
```

Smoke test `/api/annotate`:

```bash
source .venv/bin/activate
API_URL=http://127.0.0.1:8000/api/annotate PYTHONPATH=. python3 scripts/send_annotate_request.py
```

## Docker

The Dockerfile uses a multi-stage build, CPU-only dependencies where applicable, a slim Python base image, and a non-root runtime user.

Build and push the final image:

```bash
docker buildx build --platform linux/amd64 \
  -t australia-southeast1-docker.pkg.dev/sigma-icon-489807-g5/fit5225-a1-repo/cloudeco-waste-api:v13 \
  --push .
```

Run locally with Docker:

```bash
docker run --rm -p 8000:8000 \
  australia-southeast1-docker.pkg.dev/sigma-icon-489807-g5/fit5225-a1-repo/cloudeco-waste-api:v13
```

## Cloud Deployment Prerequisites

The full cloud deployment requires access to a GCP project. The runner needs permission to create Compute Engine VMs, VPC networking, firewall rules, and Artifact Registry IAM bindings. Local tooling should include Terraform, Docker Buildx, Python 3, and Ansible installed from `requirements-dev.txt`.

Before provisioning, copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and update:

- `project_id`: your GCP project ID.
- `admin_cidr`: your current public IP in CIDR form, for example `203.0.113.10/32`.
- `ssh_public_key_path`: the local SSH public key that Terraform injects into the VM metadata.

The Kubernetes nodes also need access to the container image. This submission uses:

```text
australia-southeast1-docker.pkg.dev/sigma-icon-489807-g5/fit5225-a1-repo/cloudeco-waste-api:v13
```

If deploying in a different GCP project or Artifact Registry repository, build and push the image there first, then update the `image` field in `k8s/10-deployment.yaml`.

## Infrastructure as Code and Cluster Automation

Terraform files are in `terraform/`. They provision the GCP network, firewall rules, optional Artifact Registry public read access, and three Ubuntu VMs:

- `k8s-master`
- `k8s-worker1`
- `k8s-worker2`

Each VM is configured as `e2-custom-4-8192` to satisfy the assignment constraint of 4 vCPU and 8 GB memory per VM.

The Terraform configuration is split into modules:

- `terraform/modules/network`: custom VPC and subnet.
- `terraform/modules/firewall`: internal cluster traffic, SSH access, and NodePort access.
- `terraform/modules/compute`: the control-plane and worker VMs.
- `terraform/modules/artifact_registry`: optional Artifact Registry read access.

Terraform also uses `data.google_compute_image.node_image` to dynamically resolve the Ubuntu boot image self link from the configured image family.

Use `terraform/terraform.tfvars.example` as the template for local values. Update `project_id`, `admin_cidr`, and `ssh_public_key_path` before running Terraform. The example sets `run_cluster_bootstrap = true`, which lets `terraform apply` run the Ansible bootstrap/deploy step after VM creation.

Single-apply infrastructure and cluster deployment:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt

cd terraform
terraform init
terraform apply
terraform output
cd ..
```

With `run_cluster_bootstrap = true`, `terraform apply` creates the GCP infrastructure, renders the Ansible inventory from Terraform outputs, initialises the kubeadm control plane, installs Flannel, joins worker nodes, and deploys the CloudEco Kubernetes manifests. If you only want Terraform to create the cloud resources, set `run_cluster_bootstrap = false` and run Ansible separately.

The tested end-to-end automation path is also provided as a single project-level script:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt

scripts/provision_cluster.sh
```

This script initialises and applies Terraform, renders the Ansible inventory from Terraform outputs, removes stale local SSH host-key entries for the Terraform-managed node IPs, waits for SSH on all nodes, checks Ansible connectivity, validates the playbook syntax, bootstraps Kubernetes, and deploys the CloudEco manifests. It is useful when keeping Terraform cloud provisioning and Ansible cluster automation as visibly separate stages.

The script forces `run_cluster_bootstrap=false` during its Terraform apply step and then runs Ansible itself. This prevents the Terraform `local-exec` bootstrap and the script bootstrap from running twice.

By default, Terraform still asks for confirmation before applying infrastructure changes. To run non-interactively:

```bash
AUTO_APPROVE=1 scripts/provision_cluster.sh
```

If the VMs already exist and only the Ansible bootstrap/deploy path needs to be rerun:

```bash
SKIP_TERRAFORM_APPLY=1 scripts/provision_cluster.sh
```

The same workflow can also be run step by step for troubleshooting:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt

scripts/bootstrap_cluster.sh
```

The inventory generation script reads VM public IPs from Terraform outputs. The Ansible playbook initialises the kubeadm control-plane node, installs Flannel, joins the two worker nodes, copies the Kubernetes manifests, and deploys the application. This path was validated end-to-end in the current environment.

The end-to-end path was tested from a destroyed infrastructure state: `AUTO_APPROVE=1 scripts/provision_cluster.sh` recreated the three VMs, formed the Kubernetes cluster, deployed the API, and returned a ready NodePort service. After provisioning, verify the public API URL with:

```bash
APP_URL=$(terraform -chdir=terraform output -raw app_url_template)
curl "$APP_URL/healthz"
curl "$APP_URL/readyz"
```

The live URL is generated from Terraform outputs because GCP ephemeral external IPs may change if the VMs are destroyed and recreated. At demo time, run `terraform -chdir=terraform output -raw app_url_template` to obtain the current public NodePort URL. To preserve the URL between sessions, stop/start the VMs instead of destroying and recreating the Terraform-managed resources.

## Kubernetes Deployment

Kubernetes manifests are in `k8s/`:

- `k8s/00-namespace.yaml`
- `k8s/10-deployment.yaml`
- `k8s/20-service.yaml`

If not using Ansible, apply the manifests manually from the control-plane node:

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/cloudeco-waste-api -n cloudeco --timeout=180s
kubectl get pods -n cloudeco -o wide
```

The Deployment sets each pod to exactly 1 vCPU:

```yaml
resources:
  requests:
    cpu: "1"
  limits:
    cpu: "1"
```

The Service exposes the API through NodePort `30080`:

```text
http://<node-external-ip>:30080
```

Check readiness:

```bash
curl http://<node-external-ip>:30080/readyz
```

Scale replicas:

```bash
kubectl scale deployment/cloudeco-waste-api --replicas=1 -n cloudeco
kubectl scale deployment/cloudeco-waste-api --replicas=2 -n cloudeco
kubectl scale deployment/cloudeco-waste-api --replicas=4 -n cloudeco
kubectl scale deployment/cloudeco-waste-api --replicas=8 -n cloudeco
kubectl rollout status deployment/cloudeco-waste-api -n cloudeco --timeout=180s
kubectl get pods -n cloudeco -o wide
```

## 8-Pod Scheduling Note

Each application pod requests exactly 1 CPU. In this kubeadm cluster, the two worker nodes may not have enough allocatable CPU to schedule all 8 benchmark pods after Kubernetes and system overhead. For the 8-pod benchmark only, the control-plane node was temporarily allowed to participate in workload scheduling.

If required before the 8-pod benchmark:

```bash
kubectl taint nodes k8s-master node-role.kubernetes.io/control-plane:NoSchedule-
```

After benchmarking, the control-plane taint can be restored:

```bash
kubectl taint nodes k8s-master node-role.kubernetes.io/control-plane:NoSchedule
```

The final 8-pod benchmark used the control-plane node, with 3 pods on master and 5 pods across the two workers. The exact worker split may vary by rollout, so record `kubectl get pods -n cloudeco -o wide` when reporting final results.

## Benchmarking With Locust

The Locust script is `locust/locustfile.py`. It uses:

- `FastHttpUser`
- `wait_time = constant(0)`
- default image `samples/benchmark_640.jpg`
- mixed workload `/api/predict : /api/annotate = 3 : 1`
- response validation for required fields, UUID correlation, count consistency, and annotated image base64 validity

Install Locust dependencies:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Set the benchmark host:

```bash
export BENCH_HOST=http://<node-external-ip>:30080
curl "$BENCH_HOST/readyz"
```

Run headless Locust:

```bash
locust -f locust/locustfile.py --host "$BENCH_HOST" \
  --headless -u 24 -r 4 -t 45s --only-summary
```

Run the Locust web UI:

```bash
locust -f locust/locustfile.py --host "$BENCH_HOST"
```

Then open:

```text
http://localhost:8089
```

Suggested benchmark sweep:

```text
1 pod:  users 1, 2, 4, 6, 8
2 pods: users 2, 4, 8, 12, 16
4 pods: users 4, 8, 16, 24, 32
8 pods: users 8, 16, 24, 32, 48, 64
```

For reproducible logs:

```bash
mkdir -p benchmark_logs
locust -f locust/locustfile.py --host "$BENCH_HOST" \
  --headless -u 24 -r 4 -t 45s --only-summary \
  2>&1 | tee benchmark_logs/r8_u24.txt
```

## Final Benchmark Summary

Final sweep file:

```text
benchmark_logs/v13_sweep_20260429_123944_summary.csv
```

Summary table used in the PDF report:

| Pods | Max stable users | Stable QPS | Avg ms | QPS/pod | Peak QPS (users, avg ms) |
|---:|---:|---:|---:|---:|---|
| 1 | 4 | 8.62 | 445 | 8.62 | 8.62 (u=4, 445 ms) |
| 2 | 8 | 16.28 | 471 | 8.14 | 16.28 (u=8, 471 ms) |
| 4 | 8 | 22.18 | 346 | 5.54 | 27.72 (u=24, 807 ms) |
| 8 | 24 | 48.02 | 467 | 6.00 | 51.94 (u=32, 589 ms) |

All final reported runs had zero failures.

## Useful Verification Commands

Check pods and placement:

```bash
kubectl get pods -n cloudeco -o wide
```

Check deployment image, environment variables, and resource limits:

```bash
kubectl get deployment cloudeco-waste-api -n cloudeco -o yaml
```

Check service:

```bash
kubectl get service cloudeco-waste-api -n cloudeco -o wide
```

Check node allocatable resources:

```bash
kubectl describe node k8s-master  | sed -n '/Allocatable:/,/System Info:/p'
kubectl describe node k8s-worker1 | sed -n '/Allocatable:/,/System Info:/p'
kubectl describe node k8s-worker2 | sed -n '/Allocatable:/,/System Info:/p'
```

Check control-plane taint:

```bash
kubectl describe node k8s-master | grep -i taint
```

## Key Design Choices

- CPU-bound YOLO work is moved out of the FastAPI async route path into executor-backed service methods.
- Inference worker count is fixed at 1 to match the 1 vCPU per pod resource constraint.
- OpenCV, MKL, and related numeric thread counts are limited in the container environment to reduce oversubscription.
- `/readyz` is tied to model loading and warmup, so Kubernetes only sends traffic to initialised pods.
- The final benchmark profile prioritises throughput and latency; this is documented as a performance-quality trade-off.
- Version v13 reduced the container footprint while keeping the same benchmark-first runtime profile.
- The 8-pod benchmark uses a documented scheduling trade-off because worker-only allocatable CPU is insufficient for eight 1-CPU pods.

## Repository Layout

```text
app/                         FastAPI application source code
app/api/                     API route definitions
app/core/                    Runtime configuration
app/schemas/                 Request and response schemas
app/services/                YOLO inference service
app/utils/                   Image encoding and decoding helpers
models/best_model.pt         Assigned YOLO model weights
samples/benchmark_640.jpg    Standard benchmark image
samples/image_phone.jpeg     Original sample image kept for functional demo/reference
k8s/                         Kubernetes namespace, deployment, and service manifests
locust/locustfile.py         Mixed Locust workload for /api/predict and /api/annotate
locust/locustfile_predict_only.py  Diagnostic predict-only Locust workload
scripts/                     Smoke tests, benchmark helpers, and provisioning scripts
terraform/                   GCP infrastructure provisioning code
ansible/                     kubeadm cluster bootstrap and application deployment playbooks
benchmark_logs/              Final Locust benchmark summary CSV (other local logs are ignored)
Dockerfile                   Multi-stage Docker build definition
requirements.txt             Runtime Python dependencies
requirements-dev.txt         Local development, benchmark, and automation dependencies
README.md                    Project setup, deployment, and benchmark instructions
```

## Notes

The submitted runtime model is `models/best_model.pt`. Unused ONNX, OpenVINO, exported model artifacts, local virtual environments, private SSH keys, service account keys, Terraform state files, real `terraform.tfvars`, real Ansible inventory files, and temporary benchmark outputs are intentionally excluded from the submission package.

The live NodePort URL may change if the Terraform-managed VMs are destroyed and recreated, because this setup uses ephemeral GCP external IPs. Use the Terraform output command below to retrieve the current service URL:

```bash
terraform -chdir=terraform output -raw app_url_template
```
