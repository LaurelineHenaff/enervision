# Stockage des fichiers de données versionnés par DVC (CSV bruts, parquet silver).
# Git ne garde que les petits fichiers .dvc ; les fichiers eux-mêmes vont dans ce bucket.
# Le nom doit correspondre à l'URL du remote dans .dvc/config.

#trivy:ignore:AWS-0132 Chiffrement SSE-S3 suffisant : données d'exercice, sans donnée personnelle
#trivy:ignore:AWS-0089 Pas de journal d'accès : bucket interne à l'équipe, accès tracés par CloudTrail
resource "aws_s3_bucket" "dvc" {
  bucket = var.dvc_bucket_name
}

resource "aws_s3_bucket_public_access_block" "dvc" {
  bucket = aws_s3_bucket.dvc.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "dvc" {
  bucket = aws_s3_bucket.dvc.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

#trivy:ignore:AWS-0132 Voir plus haut
resource "aws_s3_bucket_server_side_encryption_configuration" "dvc" {
  bucket = aws_s3_bucket.dvc.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DVC adresse les fichiers par leur empreinte : un écrasement accidentel reste récupérable.
resource "aws_s3_bucket_versioning" "dvc" {
  bucket = aws_s3_bucket.dvc.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lecture et écriture du bucket pour l'équipe (dvc pull / dvc push).
# Les membres sont ajoutés au groupe à la main, comme les autres accès AWS.
data "aws_iam_policy_document" "dvc_rw" {
  statement {
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.dvc.arn]
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.dvc.arn}/*"]
  }
}

resource "aws_iam_group" "dvc" {
  name = "${var.project}-dvc"
}

resource "aws_iam_group_policy" "dvc_rw" {
  name   = "${var.project}-dvc-rw"
  group  = aws_iam_group.dvc.name
  policy = data.aws_iam_policy_document.dvc_rw.json
}
