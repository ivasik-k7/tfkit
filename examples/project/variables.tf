# Project variables
variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "my-terraform-project"
}

variable "environment" {
  description = "The deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# AWS configuration
variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "admin_cidr" {
  description = "CIDR block for administrative access"
  type        = string
  default     = "10.0.0.0/16"
}

# Networking variables
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# Compute variables
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "web_instance_count" {
  description = "Number of web instances to launch"
  type        = number
  default     = 2

  validation {
    condition     = var.web_instance_count >= 1 && var.web_instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

# Database variables
variable "db_allocated_storage" {
  description = "Allocated storage for database in GB"
  type        = number
  default     = 20
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "mydatabase"
  sensitive   = true
}

variable "db_username" {
  description = "Database administrator username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
}

# Domain and SSL variables
variable "domain_name" {
  description = "The domain name for the application"
  type        = string
  default     = "example.com"
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
}

# Feature flags
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable backup for instances"
  type        = bool
  default     = false
}

# Map variables
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "terraform-demo"
    ManagedBy   = "terraform"
    Environment = "dev"
  }
}

variable "instance_tags" {
  description = "Additional tags for instances"
  type        = map(string)
  default = {
    Backup     = "true"
    Monitoring = "true"
  }
}

# List variables
variable "allowed_ports" {
  description = "List of allowed ingress ports"
  type        = list(number)
  default     = [80, 443, 22]
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Object variable
variable "app_config" {
  description = "Application configuration"
  type = object({
    name          = string
    version       = string
    feature_flags = map(bool)
    scaling = object({
      min_size = number
      max_size = number
    })
  })
  default = {
    name    = "myapp"
    version = "1.0.0"
    feature_flags = {
      new_ui    = true
      dark_mode = false
      analytics = true
    }
    scaling = {
      min_size = 1
      max_size = 5
    }
  }
}
