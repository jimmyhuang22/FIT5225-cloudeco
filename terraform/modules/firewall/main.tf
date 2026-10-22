resource "google_compute_firewall" "allow_internal" {
  name    = "cloudeco-allow-internal"
  network = var.network_name

  source_ranges = [var.subnet_cidr]
  target_tags   = ["cloudeco-k8s"]

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "cloudeco-allow-ssh"
  network = var.network_name

  source_ranges = [var.admin_cidr]
  target_tags   = ["cloudeco-k8s"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "allow_app_nodeport" {
  name    = "cloudeco-allow-nodeport"
  network = var.network_name

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["cloudeco-k8s"]

  allow {
    protocol = "tcp"
    ports    = [tostring(var.app_nodeport)]
  }
}
