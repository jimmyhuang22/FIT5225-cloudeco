variable "network_name" {
  type        = string
  description = "Name of the custom VPC network."
}

variable "region" {
  type        = string
  description = "GCP region for the subnet."
}

variable "subnet_name" {
  type        = string
  description = "Name of the subnet used by Kubernetes nodes."
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR range for the Kubernetes node subnet."
}
