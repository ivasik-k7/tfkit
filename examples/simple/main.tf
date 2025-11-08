# providers.tf
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Three providers - one with alias
provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
}

provider "random" {}

provider "null" {}

# variables.tf
variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "secondary_region" {
  description = "Secondary AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

# locals.tf with nested structure
locals {
  common_tags = {
    Environment = var.environment
    Project     = "demo-project"
    ManagedBy   = "terraform"
  }

  naming = {
    prefix = "demo-${var.environment}"
    suffix = {
      primary   = "primary"
      secondary = "secondary"
      resources = {
        instance = "ec2"
        bucket   = "s3"
        network  = "vpc"
      }
    }
  }

  config = {
    instances = {
      count = var.instance_count
      type  = "t3.micro"
      ami = {
        us-east-1 = "ami-0c02fb55956c7d316"
        us-west-2 = "ami-0c02fb55956c7d316"
      }
    }
    networking = {
      cidr_blocks = {
        primary   = "10.0.1.0/24"
        secondary = "10.0.2.0/24"
      }
    }
  }

  # Using nested locals
  instance_name = "${local.naming.prefix}-${local.naming.suffix.resources.instance}-${local.naming.suffix.primary}"
  bucket_name   = "${local.naming.prefix}-${local.naming.suffix.resources.bucket}-${local.config.instances.count}"
}

# data.tf
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# outputs.tf
output "primary_region" {
  description = "Primary AWS region"
  value       = var.aws_region
}

output "secondary_region" {
  description = "Secondary AWS region"
  value       = var.secondary_region
}

output "instance_configuration" {
  description = "Instance configuration details"
  value = {
    name  = local.instance_name
    count = local.config.instances.count
    type  = local.config.instances.type
  }
}

output "naming_convention" {
  description = "Naming convention details"
  value = {
    prefix        = local.naming.prefix
    instance_name = local.instance_name
    bucket_name   = local.bucket_name
  }
}

output "availability_zones" {
  description = "Available AZs in primary region"
  value       = data.aws_availability_zones.available.names
}

output "current_account_id" {
  description = "Current AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# resources.tf (optional - to make it more complete)
resource "random_pet" "bucket_suffix" {
  length = 2
}

resource "null_resource" "example" {
  triggers = {
    instance_count = var.instance_count
    environment    = var.environment
  }
}
