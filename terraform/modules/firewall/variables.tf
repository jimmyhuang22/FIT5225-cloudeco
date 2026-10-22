variable "network_name" {
  type        = string
  description = "Name of the VPC network that receives the firewall rules."
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR range allowed for internal Kubernetes node traffic."
}

variable "admin_cidr" {
  type        = string
  description = "CIDR range allowed to SSH into Kubernetes nodes."
}

variable "app_nodeport" {
  type        = number
  description = "NodePort exposed by the Kubernetes Service."
}
