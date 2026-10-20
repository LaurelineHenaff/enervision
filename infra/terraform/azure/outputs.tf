output "resource_group_name" {
  description = "Groupe de ressources personnel."
  value       = data.azurerm_resource_group.main.name
}

output "api_private_ip" {
  description = "IP privée statique attendue pour la VM qui expose l'API."
  value       = local.api_private_ip
}
