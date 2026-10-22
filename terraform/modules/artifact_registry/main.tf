resource "google_artifact_registry_repository_iam_member" "public_reader" {
  count = var.enable_public_reader ? 1 : 0

  location   = var.location
  repository = var.repository
  role       = "roles/artifactregistry.reader"
  member     = "allUsers"
}
