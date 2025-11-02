# Staging Environment Configuration
environment       = "staging"
machine_size      = "medium"
instance_count    = 2
enable_monitoring = true

# Cloud Regions
aws_region   = "us-east-1"
gcp_region   = "us-central1"
gcp_zone     = "us-central1-b"
azure_region = "East US 2"

# Azure Configuration (staging-specific)
azure_subscription_id = "22222222-2222-2222-2222-222222222222"
azure_tenant_id       = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

# Tags
tags = {
  Project     = "MultiCloudApp"
  ManagedBy   = "Terraform"
  Environment = "staging"
  CostCenter  = "staging-456"
}
