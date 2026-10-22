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

output "dvc_bucket" {
  description = "Bucket S3 du remote DVC (url dans .dvc/config : s3://<bucket>/store)."
  value       = aws_s3_bucket.dvc.bucket
}

output "dvc_iam_group" {
  description = "Groupe IAM qui donne accès au bucket DVC en lecture et en écriture."
  value       = aws_iam_group.dvc.name
}
