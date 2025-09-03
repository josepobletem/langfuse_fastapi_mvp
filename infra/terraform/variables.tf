variable "project_name" {
  description = "Nombre lógico del proyecto (solo para demo local)."
  type        = string
  default     = "langfuse-fastapi-demo"
}

variable "artifacts_dir" {
  description = "Directorio donde se escriben artefactos locales."
  type        = string
  default     = "artifacts"
}

