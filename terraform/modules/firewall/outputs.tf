output "firewall_rule_names" {
  description = "Names of firewall rules created for the assignment cluster."
  value = [
    google_compute_firewall.allow_internal.name,
    google_compute_firewall.allow_ssh.name,
    google_compute_firewall.allow_app_nodeport.name,
  ]
}
