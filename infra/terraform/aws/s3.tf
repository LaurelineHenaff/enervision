# Stockage S3 de la production : un seul bucket, un préfixe par usage.
#   dvc/      remote DVC (jeux de données et modèles versionnés), alimenté depuis les postes
#   etl/      fichiers bruts et intermédiaires de l'ETL, écrits par le conteneur etl
#   backups/  sauvegardes de la base (pg_dump), gardées 30 jours
# La base elle-même reste sur le disque de l'instance : PostgreSQL a besoin d'un disque, pas de S3.

resource "aws_s3_bucket" "data" {
  # Le numéro de compte rend le nom unique au monde.
  bucket = "${local.name}-data-${data.aws_caller_identity.current.account_id}"

  # Projet limité dans le temps : terraform destroy vide et supprime le bucket, données comprises.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "expiration-sauvegardes"
    status = "Enabled"

    filter {
      prefix = "backups/"
    }

    expiration {
      days = 30
    }
  }
}

# Droits de l'instance (et de ses conteneurs, voir metadata_options dans main.tf) sur ce bucket :
# lecture et écriture pour l'ETL et les sauvegardes, lecture seule pour DVC. Pas de suppression.
data "aws_iam_policy_document" "instance_s3" {
  statement {
    sid       = "Lister"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn]
  }

  statement {
    sid     = "EtlEtSauvegardes"
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = [
      "${aws_s3_bucket.data.arn}/etl/*",
      "${aws_s3_bucket.data.arn}/backups/*",
    ]
  }

  statement {
    sid       = "LectureDvc"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.data.arn}/dvc/*"]
  }
}

resource "aws_iam_role_policy" "instance_s3" {
  name   = "${local.name}-instance-s3"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.instance_s3.json
}
