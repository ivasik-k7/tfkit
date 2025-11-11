
moved {
  from = aws_instance.server_instance
  to   = module.vpc.aws_instance.server
}

moved {
  from = aws_s3_bucket.old_bucket_name
  to   = aws_s3_bucket.new_bucket_name
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

terraform {
  # Version constraint
  required_version = ">= 1.0"

  # Required providers
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

  # Backend configuration (choose one)

  # Local backend (default)
  backend "local" {
    path = "terraform.tfstate"
  }

  # S3 backend example
  # backend "s3" {
  #   bucket         = "my-terraform-state-bucket"
  #   key            = "path/to/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }

  # Azure Storage backend example
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state"
  #   storage_account_name = "tfstate12345"
  #   container_name       = "tfstate"
  #   key                  = "terraform.tfstate"
  # }

  # Terraform Cloud backend
  # backend "remote" {
  #   hostname = "app.terraform.io"
  #   organization = "my-org"
  #
  #   workspaces {
  #     name = "my-workspace"
  #   }
  # }

  # Cloud configuration (for Terraform Cloud/Enterprise)
  cloud {
    organization = "my-organization"

    workspaces {
      name = "my-workspace"
      # OR for tags-based workspace selection:
      # tags = ["app", "production"]
    }
  }

  # Experimental features
  experiments = [
    # module_variable_optional_attrs,  # Example experimental feature
    # config_driven_flow,             # Another example
  ]
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

resource "aws_instance" "secondary_instance" {
  provider = aws.secondary
  ami      = ""
}

resource "null_resource" "example" {
  triggers = {
    instance_count = var.instance_count
    environment    = var.environment
  }
}

# resources.tf - Additional resources with meta arguments

# 1. Count meta-argument with conditional creation
resource "aws_s3_bucket" "primary_buckets" {
  count = var.environment == "prod" ? 3 : 1

  bucket = "${local.bucket_name}-${count.index}"
  tags = merge(local.common_tags, {
    BucketIndex = count.index
    Region      = var.aws_region
  })
}

# 2. For_each meta-argument with map
resource "aws_iam_user" "deployment_users" {
  for_each = {
    ci_cd      = "continuous-integration"
    backup     = "backup-process"
    monitoring = "monitoring-system"
  }

  name = "${local.naming.prefix}-${each.key}-user"
  tags = merge(local.common_tags, {
    Role = each.value
  })
}

# 3. Multiple providers with aliases
resource "aws_s3_bucket" "cross_region_buckets" {
  for_each = {
    primary   = aws
    secondary = aws.secondary
  }

  provider = each.value
  bucket   = "${local.bucket_name}-${each.key}-${random_pet.bucket_suffix.id}"

  tags = merge(local.common_tags, {
    Region = each.key
  })
}

# 4. Depends_on meta-argument
resource "aws_iam_user_policy" "bucket_access_policies" {
  for_each = aws_iam_user.deployment_users

  # Explicit dependency on S3 buckets
  depends_on = [aws_s3_bucket.primary_buckets]

  name = "${each.value.name}-s3-access"
  user = each.value.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:*"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# 5. Lifecycle meta-argument with ignore_changes and prevent_destroy
resource "aws_security_group" "instance_security_group" {
  name        = "${local.instance_name}-sg"
  description = "Security group for EC2 instances"

  # Lifecycle configuration
  lifecycle {
    prevent_destroy = var.environment == "prod" ? true : false
    ignore_changes  = [description]
  }

  tags = local.common_tags
}

# 6. Count with conditional and lifecycle create_before_destroy
resource "aws_cloudwatch_log_group" "app_logs" {
  count = var.instance_count > 0 ? 1 : 0

  name = "/aws/ec2/${local.instance_name}"

  lifecycle {
    create_before_destroy = true
  }

  tags = local.common_tags
}

# 7. Complex for_each with nested structure
resource "aws_ssm_parameter" "application_config" {
  for_each = {
    for idx, config in local.application_configs :
    config.name => config
  }

  name  = each.value.name
  type  = each.value.type
  value = each.value.value

  tags = local.common_tags
}

resource "aws_vpc" "secondary_vpc" {
  provider = aws.secondary

  depends_on = [aws_s3_bucket.cross_region_buckets["secondary"]]

  cidr_block = local.config.networking.cidr_blocks.secondary
  tags = merge(local.common_tags, {
    Name = "${local.naming.prefix}-secondary-vpc"
  })
}

# 9. Multiple resources with count and element() function
resource "aws_subnet" "primary_subnets" {
  count = length(data.aws_availability_zones.available.names)

  vpc_id            = aws_vpc.primary_vpc.id
  cidr_block        = cidrsubnet(local.config.networking.cidr_blocks.primary, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.naming.prefix}-subnet-${count.index}"
    AZ   = data.aws_availability_zones.available.names[count.index]
  })
}

# 10. Null resource with triggers and depends_on
resource "null_resource" "deployment_trigger" {
  depends_on = [
    aws_s3_bucket.primary_buckets
  ]

  triggers = {
    instance_count = var.instance_count
    bucket_count   = length(aws_s3_bucket.primary_buckets)
    timestamp      = timestamp()
  }

  provisioner "local-exec" {
    command = "echo 'Deployment completed with ${var.instance_count} instances and ${length(aws_s3_bucket.primary_buckets)} buckets'"
  }
}

# Additional supporting resources and locals

# Primary VPC resource
resource "aws_vpc" "primary_vpc" {
  cidr_block = local.config.networking.cidr_blocks.primary
  tags = merge(local.common_tags, {
    Name = "${local.naming.prefix}-primary-vpc"
  })
}

# EC2 instances with count
resource "aws_instance" "primary_instances" {
  count = var.instance_count

  ami           = local.config.instances.ami[var.aws_region]
  instance_type = local.config.instances.type

  # Using element() to distribute across AZs
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  vpc_security_group_ids = [aws_security_group.instance_security_group.id]

  tags = merge(local.common_tags, {
    Name = "${local.instance_name}-${count.index}"
    AZ   = element(data.aws_availability_zones.available.names, count.index)
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

# Additional locals for complex configurations
locals {
  application_configs = [
    {
      name  = "/${var.environment}/database/host"
      type  = "String"
      value = "localhost"
    },
    {
      name  = "/${var.environment}/database/port"
      type  = "String"
      value = "5432"
    },
    {
      name  = "/${var.environment}/app/version"
      type  = "String"
      value = "1.0.0"
    }
  ]

  # Dynamic naming based on count
  instance_names = [
    for i in range(var.instance_count) :
    "${local.instance_name}-${i}"
  ]
}

# Additional outputs to showcase the meta-arguments results
output "s3_buckets" {
  description = "Created S3 buckets"
  value       = { for k, v in aws_s3_bucket.primary_buckets : k => v.bucket }
}

output "iam_users" {
  description = "Created IAM users"
  value       = { for k, v in aws_iam_user.deployment_users : k => v.name }
}

output "cross_region_buckets_info" {
  description = "Cross-region buckets information"
  value       = { for k, v in aws_s3_bucket.cross_region_buckets : k => { bucket = v.bucket, region = v.tags_all.Region } }
}

output "subnet_configuration" {
  description = "Subnet configuration details"
  value = [
    for subnet in aws_subnet.primary_subnets : {
      id                = subnet.id
      cidr_block        = subnet.cidr_block
      availability_zone = subnet.availability_zone
    }
  ]
}

output "ssm_parameters" {
  description = "SSM parameter details"
  value       = { for k, v in aws_ssm_parameter.application_config : k => v.name }
}
