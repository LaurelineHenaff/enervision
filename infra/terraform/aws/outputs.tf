output "instance_id" {
  description = "Identifiant de l'instance de production (cible du déploiement SSM)."
  value       = aws_instance.main.id
}

output "instance_private_ip" {
  description = "IP privée de l'instance."
  value       = aws_instance.main.private_ip
}

output "instance_public_ip" {
  description = "IP publique de l'instance (vide si le sous-réseau n'en attribue pas)."
  value       = aws_instance.main.public_ip
}

output "deploy_role_arn" {
  description = "Rôle IAM assumé par le workflow de déploiement via OIDC."
  value       = aws_iam_role.deploy.arn
}

output "ami_id" {
  description = "Image Debian 13 retenue."
  value       = aws_instance.main.ami
}

output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}