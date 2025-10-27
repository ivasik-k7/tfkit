# Local values - Used
locals {
  # Common tags used across resources
  common_tags = {
    Environment = var.environment
    Project     = "Web Application"
    ManagedBy   = "Terraform"
    Version     = "1.0.0"
  }

  # Instance naming convention
  instance_names = [for i in range(var.instance_count) : "web-server-${i + 1}"]

  # Resource naming prefix
  name_prefix = "${var.environment}-${local.project_suffix}"

  # Calculated values based on variables
  total_instances = var.instance_count + 1 # Including unused server

  # Security group common rules
  sg_common_ports = [80, 443, 22]

  # Availability zones for multi-AZ deployment
  available_zones = slice(data.aws_availability_zones.available.names, 0, min(3, length(data.aws_availability_zones.available.names)))

  # Instance configuration map
  instance_config = {
    web = {
      instance_type = "t3.micro"
      sg_ids        = [aws_security_group.web_sg.id]
    }
    unused = {
      instance_type = "t3.small"
      sg_ids        = []
    }
  }

  # Bucket naming patterns
  bucket_suffix = data.aws_caller_identity.current.account_id
  log_buckets   = ["web-logs", "application-logs", "backup-logs"]
}

# Unused local values
locals {
  # These locals are defined but not referenced anywhere
  unused_calculation = var.instance_count * 100
  unused_timestamp   = formatdate("YYYY-MM-DD", timestamp())
  dummy_list         = ["item1", "item2", "item3"]
  unused_map = {
    key1 = "value1"
    key2 = "value2"
    key3 = "value3"
  }

  # Complex unused calculations
  fibonacci_sequence = [for i in range(10) : i <= 1 ? i : local.fibonacci_sequence[i-1] + local.fibonacci_sequence[i-2]]

  # Unused formatted strings
  greeting_message = "Hello, ${var.environment} environment!"
  deployment_info  = "Deploying ${var.instance_count} instances in ${var.aws_region}"

  # Unused conditional values
  is_production = var.environment == "prod"
  should_scale  = var.instance_count > 2

  # Unused transformed lists
  uppercase_names = [for name in local.instance_names : upper(name)]
  numbered_items  = [for i, name in local.instance_names : "${i + 1}. ${name}"]

  # Dummy mathematical operations
  circle_area        = 3.14159 * pow(5, 2)
  random_calculation = (var.instance_count * 100) / 7 + 42

  # Unused merged maps
  extended_tags = merge(local.common_tags, {
    CostCenter = "IT-001"
    Department = "Engineering"
  })

  # Unused filtered data
  even_numbers    = [for i in range(20) : i if i % 2 == 0]
  large_instances = [for size in ["t3.micro", "t3.small", "t3.medium", "t3.large"] : size if contains(["t3.medium", "t3.large"], size)]
}

# Conditional locals - Some used, some unused
locals {
  # Used conditional
  project_suffix = var.environment == "prod" ? "production" : "development"

  # Unused conditionals
  instance_size    = var.instance_count > 5 ? "large" : "small"
  budget_alert     = var.environment == "prod" ? "high" : "low"
  backup_frequency = var.environment == "prod" ? "daily" : "weekly"

  # Complex unused conditionals
  deployment_strategy = var.instance_count > 10 ? "blue-green" : var.instance_count > 5 ? "canary" : "standard"
  monitoring_level    = var.environment == "prod" ? "detailed" : var.environment == "staging" ? "basic" : "minimal"
}
