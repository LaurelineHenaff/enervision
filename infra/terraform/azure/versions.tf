terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # L'état doit être partagé par l'équipe (ex. Storage Account Azure) pour éviter
  # les ressources en double. À activer une fois le Storage Account créé :
  #
  # backend "azurerm" {
  #   resource_group_name  = "..."
  #   storage_account_name = "..."
  #   container_name       = "tfstate"
  #   key                  = "enervision-azure.tfstate"
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
