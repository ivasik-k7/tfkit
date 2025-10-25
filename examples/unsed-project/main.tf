# main.tf - Terraform configuration with unused resources

# Provider configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
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

provider "aws" {
  region = var.aws_region
}

provider "random" {}

provider "null" {}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

variable "unused_variable" {
  description = "This variable is not used anywhere"
  type        = string
  default     = "unused_value"
}

# Data sources
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Unused data source
data "aws_region" "current" {
  # This data source is not referenced anywhere
}

# Security Group - Used
resource "aws_security_group" "web_sg" {
  name        = "${var.environment}-web-sg"
  description = "Security group for web servers"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-web-sg"
  }
}

# Security Group - Unused
resource "aws_security_group" "unused_sg" {
  name        = "${var.environment}-unused-sg"
  description = "This security group is not used by any resource"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["192.168.1.0/24"]
  }

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-unused-sg"
  }
}

# EC2 Instances - Used
resource "aws_instance" "web_server" {
  count = var.instance_count

  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name        = "${var.environment}-web-server-${count.index + 1}"
    Environment = var.environment
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
  EOF
}

# Unused EC2 Instance
resource "aws_instance" "unused_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small"

  # This instance doesn't have security groups attached
  # and is not referenced anywhere

  tags = {
    Name        = "${var.environment}-unused-server"
    Environment = var.environment
  }
}

# S3 Bucket - Used
resource "aws_s3_bucket" "logs_bucket" {
  bucket = "${var.environment}-web-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Purpose     = "web-logs"
  }
}

# Unused S3 Bucket
resource "aws_s3_bucket" "unused_bucket" {
  bucket = "${var.environment}-unused-backup-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Purpose     = "backup"
  }
}

# S3 Bucket Policy - Used
resource "aws_s3_bucket_policy" "logs_policy" {
  bucket = aws_s3_bucket.logs_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.logs_bucket.arn}/*"
      }
    ]
  })
}

# Unused IAM Role
resource "aws_iam_role" "unused_role" {
  name = "${var.environment}-unused-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role Policy Attachment - Unused
resource "aws_iam_role_policy_attachment" "unused_policy_attach" {
  role       = aws_iam_role.unused_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# Random resources
resource "random_pet" "bucket_suffix" {
  length = 2
}

# Unused random resource
resource "random_integer" "unused_number" {
  min = 1
  max = 100
}

# Null resource - Used
resource "null_resource" "provisioner" {
  triggers = {
    instance_ids = join(",", aws_instance.web_server[*].id)
  }

  provisioner "local-exec" {
    command = "echo 'Web servers deployed: ${join(",", aws_instance.web_server[*].id)}'"
  }
}

# Unused null resource
resource "null_resource" "unused_provisioner" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "echo 'This provisioner is not needed'"
  }
}

# Outputs - Used
output "web_server_ips" {
  description = "Public IP addresses of web servers"
  value       = aws_instance.web_server[*].public_ip
}

output "s3_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs_bucket.bucket
}

output "security_group_id" {
  description = "ID of the web security group"
  value       = aws_security_group.web_sg.id
}

# Unused outputs
output "unused_instance_id" {
  description = "ID of the unused instance"
  value       = aws_instance.unused_server.id
}

output "unused_random_number" {
  description = "Random number that is not used"
  value       = random_integer.unused_number.result
}

# Local values - Used
locals {
  common_tags = {
    Environment = var.environment
    Project     = "Web Application"
    ManagedBy   = "Terraform"
  }

  instance_names = [for i in range(var.instance_count) : "web-server-${i + 1}"]
}

# Unused local values
locals {
  unused_calculation = var.instance_count * 100
  unused_timestamp   = formatdate("YYYY-MM-DD", timestamp())
}

# Module call - Used
module "web_alarm" {
  source = "./modules/cloudwatch-alarm"

  alarm_name          = "high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    InstanceId = aws_instance.web_server[0].id
  }
}

# Unused module call
module "unused_alarm" {
  source = "./modules/cloudwatch-alarm"

  alarm_name          = "unused-alarm-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NetworkIn"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 1000000

  dimensions = {
    InstanceId = aws_instance.unused_server.id
  }
}
