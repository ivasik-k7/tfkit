locals {
  # Base naming convention
  project_prefix = "mc-${var.environment}" # mc = multi-cloud

  # Cloud-specific naming with relationships
  naming = {
    aws = {
      instance_name = "${local.project_prefix}-aws-vm"
      sg_name       = "${local.project_prefix}-aws-sg"
      bucket_name   = "${local.project_prefix}-aws-bucket-${random_id.suffix.hex}"
    }
    gcp = {
      instance_name = "${local.project_prefix}-gcp-vm"
      bucket_name   = "${local.project_prefix}-gcp-bucket-${random_id.suffix.hex}"
      network_name  = "${local.project_prefix}-gcp-network"
    }
    azure = {
      vm_name         = "${local.project_prefix}-azure-vm"
      vnet_name       = "${local.project_prefix}-azure-vnet"
      resource_group  = "${local.project_prefix}-azure-rg"
      storage_account = "${lower(local.project_prefix)}azurest${random_id.suffix.hex}"
    }
  }

  # Dynamic instance sizing based on environment and machine_size variable
  instance_sizes = {
    aws = {
      small  = "t3.micro"
      medium = "t3.small"
      large  = "t3.medium"
    }
    gcp = {
      small  = "e2-small"
      medium = "e2-medium"
      large  = "e2-large"
    }
    azure = {
      small  = "Standard_B1s"
      medium = "Standard_B2s"
      large  = "Standard_B4ms"
    }
  }

  # Derived configurations based on relationships between variables
  derived_config = {
    is_production    = var.environment == "prod"
    is_development   = var.environment == "dev"
    monitoring_email = var.enable_monitoring ? "alerts@company.com" : null


    # Performance tuning based on instance count
    high_availability_mode = var.instance_count > 1
    load_balancing_enabled = var.instance_count > 1
  }

  # Network CIDR calculations based on environment
  network_config = {
    # Calculate subnets based on instance count
    subnet_count = min(var.instance_count, 3) # Max 3 subnets

    # Generate subnet CIDRs dynamically
    subnet_cidrs = [for i in range(local.network_config.subnet_count) :
      cidrsubnet(local.network_config.base_cidr, 8, i)
    ]
  }

  # Storage configurations with relationships
  storage_config = {
    # Size based on machine_size variable
    disk_sizes = {
      small  = 20
      medium = 50
      large  = 100
    }
  }

  # Tags with inherited and computed relationships
  computed_tags = merge(var.tags, {
    # Inherited from variables
    Environment = var.environment
    ManagedBy   = "Terraform"

    # Computed values
    HighAvailability = local.derived_config.high_availability_mode
    Monitoring       = var.enable_monitoring
    CostOptimized    = local.derived_config.is_development
    InstanceCount    = var.instance_count
    MachineSize      = var.machine_size

    # Timestamps
    DeployedAt  = timestamp()
    TFWorkspace = terraform.workspace
  })

  # Security groups/rules based on environment and monitoring
  security_rules = {
    base_rules = [
      {
        protocol    = "tcp"
        port        = 22
        cidr_blocks = ["0.0.0.0/0"]
        description = "SSH access"
      },
      {
        protocol    = "tcp"
        port        = 80
        cidr_blocks = ["0.0.0.0/0"]
        description = "HTTP access"
      },
      {
        protocol    = "tcp"
        port        = 443
        cidr_blocks = ["0.0.0.0/0"]
        description = "HTTPS access"
      }
    ]

    # Additional rules for monitoring
    monitoring_rules = var.enable_monitoring ? [
      {
        protocol    = "tcp"
        port        = 9100
        cidr_blocks = ["10.0.0.0/8"]
        description = "Node exporter"
      }
    ] : []

    # Combine all rules
    all_rules = concat(local.security_rules.base_rules, local.security_rules.monitoring_rules)
  }

  # Output relationships for debugging
  debug_info = {
    variables_used = {
      environment       = var.environment
      machine_size      = var.machine_size
      instance_count    = var.instance_count
      enable_monitoring = var.enable_monitoring
    }

    computed_values = {
      project_prefix     = local.project_prefix
      is_production      = local.derived_config.is_production
      high_availability  = local.derived_config.high_availability_mode
      subnet_count       = local.network_config.subnet_count
      subnet_cidrs       = local.network_config.subnet_cidrs
      all_security_rules = length(local.security_rules.all_rules)
    }

    cloud_specific = {
      aws_instance_type     = local.instance_sizes.aws[var.machine_size]
      gcp_machine_type      = local.instance_sizes.gcp[var.machine_size]
      azure_vm_size         = local.instance_sizes.azure[var.machine_size]
      aws_bucket_name       = local.naming.aws.bucket_name
      gcp_bucket_name       = local.naming.gcp.bucket_name
      azure_storage_account = local.naming.azure.storage_account
    }
  }

  #   variable "unsused_variable" {
  #   description = "This variable is intentionally left unused to test graph behavior"
  #   type        = string
  #   default     = "unused"
  # }

  unused_calculation = var.unused_variable != "" ? "This is unused" : "Also unused"

  unused_circular_reference = local.unused_calculation == "This is unused" ? local.unused_calculation : "Still unused"
}


