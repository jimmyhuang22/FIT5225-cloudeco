variable "nodes" {
  type = map(object({
    tags = list(string)
  }))
  description = "Kubernetes VM definitions keyed by node name."
}

variable "machine_type" {
  type        = string
  description = "GCP machine type for each Kubernetes VM."
}

variable "zone" {
  type        = string
  description = "GCP zone for the Kubernetes VMs."
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID attached to each Kubernetes VM."
}

variable "boot_disk_size_gb" {
  type        = number
  description = "Boot disk size in GB for each Kubernetes VM."
}

variable "image_self_link" {
  type        = string
  description = "Self link of the boot image resolved by a Terraform data source."
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to the public SSH key injected into the ubuntu user metadata."
}

variable "startup_script" {
  type        = string
  description = "Startup script used to install Kubernetes node prerequisites."
}
