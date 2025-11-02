environment       = "dev"
machine_size      = "medium"
instance_count    = 2
enable_monitoring = true

aws_region   = "us-west-2"
gcp_region   = "europe-west1"
gcp_zone     = "europe-west1-b"
azure_region = "West Europe"

tags = {
  Project     = "MultiCloudDeployment"
  Environment = "dev"
  Owner       = "cloud-team"
  CostCenter  = "CLOUD-2024"
  Application = "WebApp"
}
