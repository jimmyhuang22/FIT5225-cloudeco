resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

data "google_compute_image" "node_image" {
  family  = var.image_family
  project = var.image_project

  depends_on = [google_project_service.apis]
}

locals {
  nodes = {
    "k8s-master" = {
      tags = ["cloudeco-k8s", "cloudeco-master"]
    }
    "k8s-worker1" = {
      tags = ["cloudeco-k8s", "cloudeco-worker"]
    }
    "k8s-worker2" = {
      tags = ["cloudeco-k8s", "cloudeco-worker"]
    }
  }

  app_manifest_hashes = [
    filesha256("${path.module}/../k8s/00-namespace.yaml"),
    filesha256("${path.module}/../k8s/10-deployment.yaml"),
    filesha256("${path.module}/../k8s/20-service.yaml"),
  ]
}

module "network" {
  source = "./modules/network"

  network_name = var.network_name
  region       = var.region
  subnet_name  = var.subnet_name
  subnet_cidr  = var.subnet_cidr

  depends_on = [google_project_service.apis]
}

module "firewall" {
  source = "./modules/firewall"

  network_name = module.network.network_name
  subnet_cidr  = var.subnet_cidr
  admin_cidr   = var.admin_cidr
  app_nodeport = var.app_nodeport

  depends_on = [module.network]
}

module "artifact_registry_access" {
  source = "./modules/artifact_registry"

  enable_public_reader = var.make_artifact_repo_public
  location             = var.artifact_registry_location
  repository           = var.artifact_registry_repository

  depends_on = [google_project_service.apis]
}

module "compute" {
  source = "./modules/compute"

  nodes               = local.nodes
  machine_type        = var.machine_type
  zone                = var.zone
  subnet_id           = module.network.subnet_id
  boot_disk_size_gb   = var.boot_disk_size_gb
  image_self_link     = data.google_compute_image.node_image.self_link
  ssh_public_key_path = var.ssh_public_key_path
  startup_script = templatefile("${path.module}/startup-node.sh.tftpl", {
    kubernetes_version = var.kubernetes_version
  })

  depends_on = [
    module.firewall,
    module.artifact_registry_access,
  ]
}

resource "terraform_data" "cluster_bootstrap" {
  count = var.run_cluster_bootstrap ? 1 : 0

  triggers_replace = [
    join(",", [for name in sort(keys(module.compute.instance_ids)) : module.compute.instance_ids[name]]),
    join(",", local.app_manifest_hashes),
    filesha256("${path.module}/../ansible/site.yml"),
    filesha256("${path.module}/../scripts/bootstrap_cluster.sh"),
    filesha256("${path.module}/../scripts/render_ansible_inventory.sh"),
  ]

  provisioner "local-exec" {
    working_dir = "${path.module}/.."
    command     = "scripts/bootstrap_cluster.sh"
  }

  depends_on = [module.compute]
}
