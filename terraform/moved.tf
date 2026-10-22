moved {
  from = google_compute_network.vpc
  to   = module.network.google_compute_network.vpc
}

moved {
  from = google_compute_subnetwork.subnet
  to   = module.network.google_compute_subnetwork.subnet
}

moved {
  from = google_compute_firewall.allow_internal
  to   = module.firewall.google_compute_firewall.allow_internal
}

moved {
  from = google_compute_firewall.allow_ssh
  to   = module.firewall.google_compute_firewall.allow_ssh
}

moved {
  from = google_compute_firewall.allow_app_nodeport
  to   = module.firewall.google_compute_firewall.allow_app_nodeport
}

moved {
  from = google_artifact_registry_repository_iam_member.public_reader[0]
  to   = module.artifact_registry_access.google_artifact_registry_repository_iam_member.public_reader[0]
}

moved {
  from = google_compute_instance.nodes["k8s-master"]
  to   = module.compute.google_compute_instance.nodes["k8s-master"]
}

moved {
  from = google_compute_instance.nodes["k8s-worker1"]
  to   = module.compute.google_compute_instance.nodes["k8s-worker1"]
}

moved {
  from = google_compute_instance.nodes["k8s-worker2"]
  to   = module.compute.google_compute_instance.nodes["k8s-worker2"]
}
