variable "enable_public_reader" {
  type        = bool
  description = "When true, grants public read access to the Artifact Registry repository."
}

variable "location" {
  type        = string
  description = "Location of the Artifact Registry Docker repository."
}

variable "repository" {
  type        = string
  description = "Artifact Registry Docker repository containing the API image."
}
