variable "project_id" {
  type        = string
  description = "GCP project ID where the assignment infrastructure will be provisioned."
}

variable "region" {
  type        = string
  description = "GCP region for regional resources such as the subnet."
  default     = "australia-southeast1"
}

variable "zone" {
  type        = string
  description = "GCP zone for the Kubernetes virtual machines."
  default     = "australia-southeast1-a"
}

variable "network_name" {
  type        = string
  description = "Name of the custom VPC network."
  default     = "cloudeco-vpc"
}

variable "subnet_name" {
  type        = string
  description = "Name of the subnet used by the Kubernetes nodes."
  default     = "cloudeco-subnet"
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR range for the Kubernetes node subnet."
  default     = "10.10.0.0/24"
}

variable "machine_type" {
  type        = string
  description = "GCP machine type for each Kubernetes VM. The default is 4 vCPU and 8 GB RAM."
  default     = "e2-custom-4-8192"
}

variable "boot_disk_size_gb" {
  type        = number
  description = "Boot disk size in GB for each Kubernetes VM."
  default     = 30
}

variable "admin_cidr" {
  type        = string
  description = "CIDR range allowed to SSH into the Kubernetes nodes, for example 203.0.113.10/32."
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to the public SSH key injected into the ubuntu user metadata."
}

variable "image_project" {
  type        = string
  description = "GCP image project used for VM boot disks."
  default     = "ubuntu-os-cloud"
}

variable "image_family" {
  type        = string
  description = "GCP image family used for VM boot disks."
  default     = "ubuntu-2204-lts"
}

variable "artifact_registry_location" {
  type        = string
  description = "Location of the Artifact Registry Docker repository."
  default     = "australia-southeast1"
}

variable "artifact_registry_repository" {
  type        = string
  description = "Artifact Registry Docker repository containing the API image."
  default     = "fit5225-a1-repo"
}

variable "make_artifact_repo_public" {
  type        = bool
  description = "When true, grants public read access to the Artifact Registry repository for assignment reproducibility."
  default     = true
}

variable "app_nodeport" {
  type        = number
  description = "NodePort exposed by the Kubernetes Service for the FastAPI application."
  default     = 30080
}

variable "kubernetes_version" {
  type        = string
  description = "Minor Kubernetes package repository version used by the VM startup script."
  default     = "v1.35"
}

variable "run_cluster_bootstrap" {
  type        = bool
  description = "When true, terraform apply runs the Ansible bootstrap/deploy script after VM creation."
  default     = false
}
