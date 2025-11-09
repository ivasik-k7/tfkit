# Random suffix for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

# AWS Resources using locals
resource "aws_vpc" "main" {
  cidr_block = local.network_config.base_cidr
  tags       = local.computed_tags
}

resource "aws_subnet" "main" {
  count = local.network_config.subnet_count

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.network_config.subnet_cidrs[count.index]
  availability_zone = "${var.aws_region}${count.index == 0 ? "a" : count.index == 1 ? "b" : "c"}"

  tags = merge(local.computed_tags, {
    Name = "${local.project_prefix}-subnet-${count.index}"
    Type = "private"
  })
}

resource "aws_security_group" "web" {
  name        = local.naming.aws.sg_name
  description = "Security group for web instances"
  vpc_id      = aws_vpc.main.id

  dynamic "ingress" {
    for_each = local.security_rules.all_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.computed_tags
}

resource "aws_instance" "web" {
  count = var.instance_count

  ami           = data.aws_ami.ubuntu.id
  instance_type = local.instance_sizes.aws[var.machine_size]
  subnet_id     = aws_subnet.main[count.index % local.network_config.subnet_count].id
  monitoring    = var.enable_monitoring

  # Use spot instances in dev
  instance_market_options {
    market_type = local.derived_config.use_spot_instances ? "spot" : null

    dynamic "spot_options" {
      for_each = local.derived_config.use_spot_instances ? [1] : []
      content {
        max_price = "0.05" # Maximum spot price
      }
    }
  }

  root_block_device {
    volume_size = local.storage_config.disk_sizes[var.machine_size]
    volume_type = local.storage_config.aws_storage_class
  }

  vpc_security_group_ids = [aws_security_group.web.id]

  tags = merge(local.computed_tags, {
    Name = "${local.naming.aws.instance_name}-${count.index + 1}"
    Role = "web-server"
  })
}

# GCP Resources using locals
resource "google_compute_network" "vpc" {
  name                    = local.naming.gcp.network_name
  auto_create_subnetworks = false
}

resource "google_compute_network" "vpc_g2" {
  provider                = google.g2
  name                    = local.naming.gcp.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  count = local.network_config.subnet_count

  name          = "${local.project_prefix}-subnet-${count.index}"
  ip_cidr_range = local.network_config.subnet_cidrs[count.index]
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

resource "google_compute_instance" "web" {
  count = var.instance_count

  name         = "${local.naming.gcp.instance_name}-${count.index + 1}"
  machine_type = local.instance_sizes.gcp[var.machine_size]
  zone         = var.gcp_zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
      size  = local.storage_config.disk_sizes[var.machine_size]
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet[count.index % local.network_config.subnet_count].id

    access_config {
      # Ephemeral public IP
    }
  }

  scheduling {
    preemptible       = local.derived_config.use_preemptible_vms
    automatic_restart = !local.derived_config.use_preemptible_vms
  }

  labels = local.computed_tags
}

# Azure Resources using locals
resource "azurerm_resource_group" "main" {
  name     = local.naming.azure.resource_group
  location = var.azure_region

  tags = local.computed_tags
}

resource "azurerm_virtual_network" "main" {
  name                = local.naming.azure.vnet_name
  address_space       = [local.network_config.base_cidr]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = local.computed_tags
}

resource "azurerm_subnet" "internal" {
  count = local.network_config.subnet_count

  name                 = "${local.project_prefix}-subnet-${count.index}"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [local.network_config.subnet_cidrs[count.index]]
}

resource "azurerm_network_interface" "main" {
  count = var.instance_count

  name                = "${local.naming.azure.vm_name}-nic-${count.index + 1}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.internal[count.index % local.network_config.subnet_count].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = local.computed_tags
}

resource "azurerm_linux_virtual_machine" "main" {
  count = var.instance_count

  name                = "${local.naming.azure.vm_name}-${count.index + 1}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = local.instance_sizes.azure[var.machine_size]
  admin_username      = "adminuser"

  network_interface_ids = [
    azurerm_network_interface.main[count.index].id,
  ]

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = local.storage_config.disk_sizes[var.machine_size]
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  tags = merge(local.computed_tags, {
    Name = "${local.naming.azure.vm_name}-${count.index + 1}"
    Role = "web-server"
  })
}
