terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  repo_path        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.animai_repo.repository_id}"
  langgraph_image  = "${local.repo_path}/${var.image_name}:latest"
  manim_image      = "${local.repo_path}/manim-worker:latest"
}

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "animai_repo" {
  location      = var.region
  repository_id = "animai-repo"
  description   = "Docker repository for AnimAI"
  format        = "DOCKER"
}

# Cloud Run Service - langgraph-api
resource "google_cloud_run_v2_service" "animai" {
  name     = var.service_name
  location = var.region
  
  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    
    containers {
      image = local.langgraph_image
      
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = true
      }
      
      ports {
        container_port = 8000
      }
      
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      
      env {
        name  = "LANGSMITH_API_KEY"
        value = var.langsmith_api_key
      }
      
      env {
        name  = "LANGSMITH_PROJECT"
        value = var.langsmith_project
      }
      
      env {
        name  = "LANGSMITH_TRACING"
        value = "true"
      }

      env {
        name  = "CHROMA_API_KEY"
        value = var.chroma_api_key
      }
      
      env {
        name  = "CHROMA_TENANT"
        value = var.chroma_tenant
      }
      
      env {
        name  = "CHROMA_DATABASE"
        value = var.chroma_database
      }
      
      env {
        name  = "CHROMA_OPENAI_API_KEY"
        value = var.openai_api_key
      }
      
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
      
      env {
        name  = "REDIS_API_KEY"
        value = var.redis_api_key
      }

      env {
        name  = "MANIM_WORKER_URL"
        value = google_cloud_run_v2_service.manim_worker.uri
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 10
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        timeout_seconds   = 3
        period_seconds    = 30
        failure_threshold = 3
      }
    }
    
    max_instance_request_concurrency = 10
    timeout = "300s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Cloud Run Service - manim-worker
resource "google_cloud_run_v2_service" "manim_worker" {
  name     = "manim-worker"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    max_instance_request_concurrency = 1
    timeout = "900s"

    containers {
      image = local.manim_image

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = true
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "R2_ACCOUNT_ID"
        value = var.r2_account_id
      }

      env {
        name  = "R2_ACCESS_KEY_ID"
        value = var.r2_access_key_id
      }

      env {
        name  = "R2_SECRET_ACCESS_KEY"
        value = var.r2_secret_access_key
      }

      env {
        name  = "R2_BUCKET"
        value = var.r2_bucket
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        timeout_seconds   = 3
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "public_access_animai" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.animai.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "public_access_manim_worker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.manim_worker.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
