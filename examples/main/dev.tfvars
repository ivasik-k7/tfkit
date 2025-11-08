# Development Environment Configuration
environment       = "dev"
machine_size      = "small"
instance_count    = 1
enable_monitoring = false

# Cloud Regions
aws_region   = "us-east-1"
gcp_region   = "us-central1"
gcp_zone     = "us-central1-a"
azure_region = "East US"

# Azure Configuration (dev-specific)
azure_subscription_id = "11111111-1111-1111-1111-111111111111"
azure_tenant_id       = "aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

# Tags
tags = {
  Project     = "MultiCloudApp"
  ManagedBy   = "Terraform"
  Environment = "dev"
  CostCenter  = "dev-123"
}
