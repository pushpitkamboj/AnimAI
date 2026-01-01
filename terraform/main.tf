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

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "animai_repo" {
  location      = var.region
  repository_id = "animai-repo"
  description   = "Docker repository for AnimAI"
  format        = "DOCKER"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "animai" {
  name     = var.service_name
  location = var.region
  
  template {
    # Scaling configuration
    scaling {
      min_instance_count = 0    # Default instances (scale to zero)
      max_instance_count = 10  # Max instances
    }
    
    # Container configuration
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.animai_repo.repository_id}/${var.image_name}:latest"
      
      # Resource limits: 2 CPU, 4GB RAM
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = true  # Allow CPU to be throttled when idle (cost saving)
      }
      
      # Port configuration
      ports {
        container_port = 8000
      }
      
      # Environment variables
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
        name  = "E2B_API_KEY"
        value = var.e2b_api_key
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
        name  = "ACCOUNT_ID"
        value = var.account_id
      }
      
      env {
        name  = "ACCESS_KEY_ID"
        value = var.access_key_id
      }
      
      env {
        name  = "SECRET_ACCESS_KEY"
        value = var.secret_access_key
      }
      
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
      
      env {
        name  = "REDIS_API_KEY"
        value = var.redis_api_key
      }
      
      # Startup probe
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
      
      # Liveness probe
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
    
    # Concurrency: 10 requests per instance
    max_instance_request_concurrency = 10
    
    # Timeout for requests (max 3600 seconds)
    timeout = "300s"
    
    # Service account (optional, uses default if not specified)
    # service_account = google_service_account.animai_sa.email
  }
  
  # Traffic configuration - send all traffic to latest revision
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.animai.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
