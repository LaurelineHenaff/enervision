# Exposition publique du site, sans nom de domaine : https://<id>.cloudfront.net
#
#   Internet ──HTTPS──▶ CloudFront (certificat *.cloudfront.net) ──HTTP :4000──▶ EC2 (frontend)
#                                                                                 └─ /api/ ──▶ api ──▶ db
#
# Seul le frontend est exposé : il transmet lui-même /api/ à l'API (API_UPSTREAM). L'EC2 n'accepte
# le port 4000 que depuis les adresses de CloudFront ; l'API, l'ETL et la base restent fermés.
# Limite connue : entre CloudFront et l'EC2, le trafic est en HTTP (non chiffré).
# Pour passer plus tard sur un vrai domaine : certificat ACM en us-east-1, aliases et Route 53.

# IP fixe : CloudFront contacte l'instance par son nom DNS public, qui changerait à chaque arrêt.
# Une IP Elastic attachée coûte le même prix que l'IP publique automatique qu'elle remplace.
resource "aws_eip" "instance" {
  instance = aws_instance.main.id
  domain   = "vpc"

  tags = {
    Name = local.name
  }
}

# Port 4000 ouvert aux seuls serveurs de CloudFront (liste d'adresses tenue à jour par AWS).
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_vpc_security_group_ingress_rule" "frontend_cloudfront" {
  security_group_id = aws_security_group.instance.id
  description       = "Frontend (port 4000), depuis CloudFront uniquement"
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
  from_port         = 4000
  to_port           = 4000
  ip_protocol       = "tcp"
}

# Application dynamique : aucun cache, et toute la requête (en-têtes, cookies, Host…) est transmise.
data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewer"
}

# Pas de journaux d'accès (AWS-0010) ni de WAF (AWS-0011) : coût et configuration disproportionnés
# pour une démonstration de deux semaines. Certificat par défaut *.cloudfront.net (AWS-0013) : sans
# domaine à nous, la version minimale de TLS n'est pas réglable ; les navigateurs actuels négocient
# de toute façon TLS 1.2 ou 1.3.
#trivy:ignore:AWS-0010
#trivy:ignore:AWS-0011
#trivy:ignore:AWS-0013
resource "aws_cloudfront_distribution" "site" {
  enabled         = true
  comment         = "EnerVision ${var.environment}"
  price_class     = "PriceClass_100" # serveurs d'Europe et d'Amérique du Nord : les moins chers
  http_version    = "http2and3"
  is_ipv6_enabled = true

  origin {
    origin_id   = "ec2-frontend"
    domain_name = aws_eip.instance.public_dns

    custom_origin_config {
      http_port              = 4000
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 60
    }
  }

  default_cache_behavior {
    target_origin_id         = "ec2-frontend"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD"]
    compress                 = true
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

output "site_url" {
  value = "https://${aws_cloudfront_distribution.site.domain_name}"
}
