output "node_public_ips" {
  description = "Public IPv4 addresses for all Kubernetes nodes."
  value = {
    for name, vm in google_compute_instance.nodes :
    name => vm.network_interface[0].access_config[0].nat_ip
  }
}

output "node_internal_ips" {
  description = "Internal IPv4 addresses for all Kubernetes nodes."
  value = {
    for name, vm in google_compute_instance.nodes :
    name => vm.network_interface[0].network_ip
  }
}

output "master_public_ip" {
  description = "Public IPv4 address of the control-plane node."
  value       = google_compute_instance.nodes["k8s-master"].network_interface[0].access_config[0].nat_ip
}

output "master_internal_ip" {
  description = "Internal IPv4 address of the control-plane node."
  value       = google_compute_instance.nodes["k8s-master"].network_interface[0].network_ip
}

output "instance_ids" {
  description = "GCP instance IDs keyed by Kubernetes node name."
  value = {
    for name, vm in google_compute_instance.nodes :
    name => vm.id
  }
}
