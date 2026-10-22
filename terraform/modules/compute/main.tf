resource "google_compute_instance" "nodes" {
  for_each = var.nodes

  name           = each.key
  machine_type   = var.machine_type
  zone           = var.zone
  tags           = each.value.tags
  can_ip_forward = true

  boot_disk {
    initialize_params {
      image = var.image_self_link
      size  = var.boot_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = var.subnet_id

    access_config {}
  }

  metadata = {
    ssh-keys = "ubuntu:${trimspace(file(pathexpand(var.ssh_public_key_path)))}"
  }

  metadata_startup_script = var.startup_script

  labels = {
    assignment = "fit5225-a1"
    role       = replace(each.key, "k8s-", "")
  }

  lifecycle {
    ignore_changes = [
      boot_disk[0].initialize_params[0].image,
    ]
  }
}
