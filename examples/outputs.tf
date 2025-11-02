# Debug outputs to show relationships
output "locals_debug" {
  description = "Debug information showing relationships between locals"
  value       = local.debug_info
}

output "naming_conventions" {
  description = "Generated naming conventions across clouds"
  value       = local.naming
}

output "derived_configurations" {
  description = "Configurations derived from input variables"
  value       = local.derived_config
}

output "network_configuration" {
  description = "Computed network configuration"
  value       = local.network_config
}

# Resource outputs showing locals in action
output "aws_instances" {
  description = "AWS instances with computed properties"
  value = {
    for instance in aws_instance.web :
    instance.tags.Name => {
      instance_type = instance.instance_type
      subnet_cidr   = aws_subnet.main[index(aws_instance.web.*.subnet_id, instance.subnet_id)].cidr_block
      uses_spot     = local.derived_config.use_spot_instances
      monitoring    = var.enable_monitoring
    }
  }
}

output "cross_cloud_summary" {
  description = "Summary across all cloud providers"
  value = {
    total_instances   = var.instance_count * 3
    total_subnets     = local.network_config.subnet_count * 3
    high_availability = local.derived_config.high_availability_mode
    environment       = var.environment
    security_rules    = length(local.security_rules.all_rules)
  }
}

output "google_compute_summary" {
  description = "Summary of GCP compute instances"
  value = {
    for instance in google_compute_instance.web :
    instance.name => {
      machine_type = instance.machine_type
      zone         = instance.zone
      tags         = instance.tags
      monitoring   = var.enable_monitoring
    }
  }
}

output "google_compute_network" {
  description = "GCP Network configuration details"
  value = {
    network_name    = google_compute_network.main.name
    subnetwork_name = google_compute_subnetwork.main.name
    subnet_cidrs    = local.network_config.subnet_cidrs
    region          = var.gcp_region
  }
}
