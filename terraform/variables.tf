variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "animai-api"
}

variable "image_name" {
  description = "Name of the Docker image"
  type        = string
  default     = "animai"
}

# Environment variables for the application
variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API Key"
  type        = string
  sensitive   = true
}

variable "langsmith_project" {
  description = "LangSmith Project Name"
  type        = string
  default     = "manimation-dev"
}

variable "e2b_api_key" {
  description = "E2B API Key"
  type        = string
  sensitive   = true
}

variable "chroma_api_key" {
  description = "ChromaDB API Key"
  type        = string
  sensitive   = true
}

variable "chroma_tenant" {
  description = "ChromaDB Tenant ID"
  type        = string
}

variable "chroma_database" {
  description = "ChromaDB Database Name"
  type        = string
  default     = "manim_docs"
}

variable "account_id" {
  description = "R2 Account ID"
  type        = string
}

variable "access_key_id" {
  description = "R2 Access Key ID"
  type        = string
  sensitive   = true
}

variable "secret_access_key" {
  description = "R2 Secret Access Key"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}

variable "redis_api_key" {
  description = "Redis API Key"
  type        = string
  sensitive   = true
}

# ...existing code...

variable "token_id" {
  description = "Token ID"
  type        = string
  default     = ""
}

variable "token_secret" {
  description = "Token Secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "chroma_openai_api_key" {
  description = "ChromaDB OpenAI API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openpipe_api_key" {
  description = "OpenPipe API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_subscription_key" {
  description = "Azure Subscription Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_service_region" {
  description = "Azure Service Region"
  type        = string
  default     = "eastus"
}

variable "active" {
  description = "Active flag"
  type        = string
  default     = "true"
}

variable "langsmith_tracing" {
  description = "LangSmith Tracing"
  type        = string
  default     = "true"
}