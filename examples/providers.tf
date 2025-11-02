# AWS Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.35"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "google" {
  project = "your-gcp-project-id"
  region  = var.gcp_region
  zone    = var.gcp_zone
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
}

provider "tfe" {
  hostname = "app.terraform.io"
  # token    = var.tfe_token
}
