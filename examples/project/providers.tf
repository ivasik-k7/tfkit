# Main Terraform configuration
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
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  alias  = "primary"
}

provider "aws" {
  region = "us-west-2"
  alias  = "secondary"
}
