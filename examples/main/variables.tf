# Variable 1: Environment name
variable "environment" {
  description = "The deployment environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Variable 2: Instance/VM size
variable "machine_size" {
  description = "The size of the compute instance"
  type        = string
  default     = "small"
}

variable "instance_count" {
  description = "Number of compute instances to create"
  type        = number
  default     = 1
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 5
    error_message = "Instance count must be between 1 and 5."
  }
}

# Variable 4: Enable monitoring
variable "enable_monitoring" {
  description = "Whether to enable monitoring services"
  type        = bool
  default     = false
}

# Variable 5: Common tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "MultiCloudApp"
    ManagedBy = "Terraform"
  }
}

# Cloud-specific variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "East US"
}


variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure tenant ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "unused_variable" {
  description = "This variable is intentionally left unused to test graph behavior"
  type        = string
  default     = "unused"
}
