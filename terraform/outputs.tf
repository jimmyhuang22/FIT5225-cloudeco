output "node_public_ips" {
  description = "Public IPv4 addresses for all Kubernetes nodes."
  value       = module.compute.node_public_ips
}

output "node_internal_ips" {
  description = "Internal IPv4 addresses for all Kubernetes nodes."
  value       = module.compute.node_internal_ips
}

output "master_public_ip" {
  description = "Public IPv4 address of the control-plane node."
  value       = module.compute.master_public_ip
}

output "master_internal_ip" {
  description = "Internal IPv4 address of the control-plane node."
  value       = module.compute.master_internal_ip
}

output "app_url_template" {
  description = "NodePort URL template using the control-plane node public IP."
  value       = "http://${module.compute.master_public_ip}:${var.app_nodeport}"
}

output "ssh_commands" {
  description = "Convenience SSH commands for connecting to each node."
  value = {
    for name, ip in module.compute.node_public_ips :
    name => "ssh ubuntu@${ip}"
  }
}

output "resolved_node_image" {
  description = "Ubuntu boot image self link resolved dynamically through a Terraform data source."
  value       = data.google_compute_image.node_image.self_link
}
