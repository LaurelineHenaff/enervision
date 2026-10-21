terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # L'état doit être partagé par l'équipe (bucket S3 avec verrouillage) pour éviter
  # les ressources en double. À activer une fois le bucket créé :
  #
  # backend "s3" {
  #   bucket       = "..."
  #   key          = "enervision-aws.tfstate"
  #   region       = "..."
  #   use_lockfile = true
  #   encrypt      = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}
