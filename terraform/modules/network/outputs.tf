output "network_name" {
  description = "Name of the created VPC network."
  value       = google_compute_network.vpc.name
}

output "network_id" {
  description = "ID of the created VPC network."
  value       = google_compute_network.vpc.id
}

output "subnet_id" {
  description = "ID of the created subnet."
  value       = google_compute_subnetwork.subnet.id
}
