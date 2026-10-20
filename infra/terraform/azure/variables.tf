variable "subscription_id" {
  description = "Identifiant de l'abonnement Azure (az account show)."
  type        = string
}

variable "identifiant" {
  description = "Identifiant de l'apprenant, utilisé pour le groupe de ressources et le tag user."
  type        = string
}

variable "location" {
  description = "Région Azure des ressources."
  type        = string
  default     = "francecentral"
}

variable "index" {
  description = "Index du VNet spoke (10.241.<index>.0/24) : la VM qui expose l'API doit avoir l'IP 10.241.<index>.4."
  type        = number
}
