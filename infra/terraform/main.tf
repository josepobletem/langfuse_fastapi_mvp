# Genera un id aleatorio local (no requiere cloud)
resource "random_id" "artifact_id" {
  byte_length = 4
}

# Crea un archivo local con contenido generado
# *No* crea directorios: usaremos la raíz del módulo o 'artifacts' relativo.
# Para simplificar, usamos la raíz del módulo.
resource "local_file" "generated_readme" {
  content  = <<-EOT
  ## Local Infra Artifact

  - Project   : ${var.project_name}
  - Artifact  : ${random_id.artifact_id.hex}
  - Purpose   : Probar Terraform sin cuenta cloud (random/local/null providers)

  Puedes borrar este archivo con `terraform destroy`.
  EOT
  filename = "${path.module}/README.generated.md"
}

# Ejemplo de ejecución local que imprime algo (no falla si no existe nada)
resource "null_resource" "echo" {
  triggers = {
    project_name = var.project_name
    artifact     = random_id.artifact_id.hex
  }

  provisioner "local-exec" {
    command = "echo \"[INFO] Setup local for ${var.project_name} (${random_id.artifact_id.hex})\""
  }
}

output "artifact_id" {
  description = "Identificador aleatorio generado localmente."
  value       = random_id.artifact_id.hex
}

output "generated_file" {
  description = "Ruta del archivo generado localmente."
  value       = local_file.generated_readme.filename
}
