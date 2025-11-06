# --------------------------------------------------------------------------
# Terraform Variable Definition File (terraform.tfvars)
# This file provides default input values for the variables defined in
# the main configuration.
# --------------------------------------------------------------------------

# Variable 1: Environment name (REQUIRED, must be 'dev', 'staging', or 'prod')
environment = "staging"

# Variable 2: Instance/VM size (Defaults to "small", explicitly set here)
machine_size = "medium"

# Variable 3: Number of instances (Defaults to 1, explicitly set here)
instance_count = 3

# Variable 4: Enable monitoring (Defaults to false, explicitly set here)
enable_monitoring = true

# Variable 5: Common tags (Merged with default tags)
tags = {
  Project   = "MultiCloudApp"
  ManagedBy = "Terraform"
  Owner     = "EngineeringTeam"
}

# Cloud-specific variables

# AWS
aws_region = "eu-west-1"

# GCP
gcp_region = "europe-west3"
gcp_zone   = "europe-west3-a"

# Azure
azure_region          = "West Europe"
azure_subscription_id = "00000000-0000-0000-0000-000000000000" # Replace with your actual ID
azure_tenant_id       = "11111111-1111-1111-1111-111111111111" # Replace with your actual ID

# Unused variable (retains default "unused", but explicitly set here for clarity)
unused_variable = "test-graph-ignore"
