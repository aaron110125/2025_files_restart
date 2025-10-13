# Comprehensive Guide: Setting Up Containerlab with Cisco Router Images

## Table of Contents
1. [Introduction to Containerlab](#introduction-to-containerlab)
2. [Prerequisites and System Requirements](#prerequisites-and-system-requirements)
3. [Installation Instructions](#installation-instructions)
4. [Preparing Cisco Router Images](#preparing-cisco-router-images)
5. [Basic Topology Configuration](#basic-topology-configuration)
6. [Advanced Topology Configurations](#advanced-topology-configurations)
7. [Deploying and Managing the Lab Environment](#deploying-and-managing-the-lab-environment)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Best Practices](#best-practices)
10. [Additional Resources](#additional-resources)

## Introduction to Containerlab

Containerlab is a modern network emulation tool that allows network engineers to create and manage container-based networking labs. Unlike traditional virtualization solutions, containerlab leverages the efficiency and speed of containers to provide a lightweight and scalable environment for network testing and development.

### Benefits of Containerlab for Network Virtualization

- **Resource Efficiency**: Containers are more lightweight than traditional VMs, allowing you to run more network devices on the same hardware
- **Fast Startup Times**: Containers boot in seconds rather than minutes
- **Integration with DevOps Tools**: Containerlab works seamlessly with modern CI/CD pipelines and container orchestration tools
- **Consistent Environments**: Create reproducible network topologies that can be version-controlled and shared
- **Flexible Networking**: Supports various connection types and network topologies

### Limitations of Traditional Tools

Traditional network virtualization tools like Docker Compose lack the specific features needed for complex network topologies:

- Limited support for connecting containers in custom network arrangements
- No built-in understanding of network operating system requirements
- Missing features for managing network device-specific configurations

Containerlab addresses these limitations by providing a purpose-built solution for networking labs.

## Prerequisites and System Requirements

### Hardware Requirements

To run containerlab with Cisco router images effectively, your system should meet the following minimum requirements:

- **CPU**: 4+ cores (8+ cores recommended for multiple Cisco router instances)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 20GB+ free space for containerlab and images
- **Network**: Internet connection for installation and image downloads

### Software Requirements

#### Operating System

Containerlab is designed to run on Linux systems. The following distributions are officially supported:

- Ubuntu 20.04 LTS or newer
- Debian 10 or newer
- CentOS/RHEL 8 or newer
- Fedora 32 or newer

#### Required Packages

- **Docker**: Version 20.10.0 or newer
- **Git**: For cloning repositories and examples
- **sudo** privileges or root access

#### System Configuration

For optimal performance with Cisco router images, the following system configurations are recommended:

1. **Increase inotify limits**:
   ```bash
   sysctl -w fs.inotify.max_user_instances=64000
   sysctl -w fs.inotify.max_user_watches=64000
   ```

   To make these changes persistent across reboots, add them to `/etc/sysctl.conf`:
   ```bash
   echo -e "fs.inotify.max_user_instances=64000\nfs.inotify.max_user_watches=64000" | sudo tee -a /etc/sysctl.conf
   ```

2. **Docker configuration**:
   - Ensure Docker daemon is running
   - Configure Docker to start on boot: `sudo systemctl enable docker`
   - Add your user to the docker group: `sudo usermod -aG docker $USER`

## Installation Instructions

### Method 1: Package Manager Installation (Recommended)

Containerlab is distributed as a Linux deb/rpm/apk package for amd64 and arm64 architectures and can be installed on any Debian or RHEL-like distribution.

#### For Debian/Ubuntu:

```bash
# Add GPG key
curl -s https://apt.fury.io/netdevops/ | sudo apt-key add -

# Add repository
echo "deb https://apt.fury.io/netdevops/ /" | sudo tee /etc/apt/sources.list.d/netdevops.list

# Update package list
sudo apt update

# Install containerlab
sudo apt install containerlab
```

#### For RHEL/CentOS/Fedora:

```bash
# Add repository
sudo dnf config-manager --add-repo=https://yum.fury.io/netdevops/

# Install containerlab
sudo dnf install containerlab
```

### Method 2: Quick Setup Script

For a faster installation, you can use the containerlab quick setup script:

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

### Method 3: Manual Installation

If you prefer to manually install containerlab:

1. Download the latest release from the [GitHub releases page](https://github.com/srl-labs/containerlab/releases)
2. Extract and install the binary:

```bash
# Download the latest release (replace X.Y.Z with the version number)
curl -L https://github.com/srl-labs/containerlab/releases/download/vX.Y.Z/containerlab_X.Y.Z_Linux_amd64.tar.gz -o containerlab.tar.gz

# Extract the binary
tar -xf containerlab.tar.gz

# Move the binary to a directory in your PATH
sudo mv containerlab /usr/local/bin/

# Make it executable
sudo chmod +x /usr/local/bin/containerlab
```

### Verification

To verify that containerlab is installed correctly:

```bash
containerlab version
```

This should display the installed version of containerlab.

## Preparing Cisco Router Images

This section will be expanded with information about preparing and using Cisco router images with containerlab.

## Basic Topology Configuration

This section will be expanded with examples of basic topology configurations for Cisco routers.

## Advanced Topology Configurations

This section will be expanded with examples of advanced topology configurations for Cisco routers.

## Deploying and Managing the Lab Environment

This section will be expanded with instructions for deploying and managing containerlab environments.

## Troubleshooting Common Issues

This section will be expanded with troubleshooting tips for common issues.

## Best Practices

This section will be expanded with best practices for using containerlab with Cisco router images.

## Additional Resources

This section will be expanded with additional resources for learning more about containerlab and Cisco router virtualization.