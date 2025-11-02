# Production Environment Configuration
environment       = "prod"
machine_size      = "large"
instance_count    = 3
enable_monitoring = true

# Cloud Regions (production-optimized)
aws_region   = "us-east-1"
gcp_region   = "us-west1"
gcp_zone     = "us-west1-a"
azure_region = "West US 2"

# Azure Configuration (prod-specific)
azure_subscription_id = "33333333-3333-3333-3333-333333333333"
azure_tenant_id       = "cccccccc-cccc-cccc-cccc-cccccccccccc"

# Tags
tags = {
  Project     = "MultiCloudApp"
  ManagedBy   = "Terraform"
  Environment = "prod"
  CostCenter  = "prod-789"
  Critical    = "true"
}
