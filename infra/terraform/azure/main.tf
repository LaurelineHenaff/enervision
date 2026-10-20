locals {
  resource_group_name = "rg-${var.identifiant}_cours-projet-eadl"
  api_private_ip      = "10.241.${var.index}.4"

  # Le tag user est obligatoire : sans lui la politique refuse la création (403 RequestDisallowedByPolicy).
  tags = {
    user = var.identifiant
  }
}

# Le groupe de ressources personnel est fourni par l'école : on le lit sans le gérer.
data "azurerm_resource_group" "main" {
  name = local.resource_group_name
}
