output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.animai.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.animai.name
}

output "manim_worker_url" {
  description = "URL of the manim-worker Cloud Run service"
  value       = google_cloud_run_v2_service.manim_worker.uri
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.animai_repo.repository_id}"
}
