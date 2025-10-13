# Practical Guide: Installing Containerlab and Setting Up a Cisco Router Topology

This guide provides step-by-step instructions for installing containerlab and configuring a basic topology with two Cisco routers. It includes alternative options using freely available router images like FRRouting (FRR).

## Table of Contents
1. [Installing Containerlab](#installing-containerlab)
2. [Creating a Topology with Two Cisco Routers](#creating-a-topology-with-two-cisco-routers)
3. [Deploying the Topology](#deploying-the-topology)
4. [Configuring the Routers](#configuring-the-routers)
5. [Configuring OSPF](#configuring-ospf)
6. [Verifying the Setup](#verifying-the-setup)
7. [Alternative: Using FRRouting (FRR)](#alternative-using-frrouting-frr)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Cleaning Up](#cleaning-up)

## Installing Containerlab

### Prerequisites

#### For Linux Systems:
- Linux operating system (Ubuntu 20.04+ recommended)
- Docker installed and configured
- sudo privileges

#### For macOS Systems:
- macOS 10.15 (Catalina) or newer
- Docker Desktop for Mac installed and running
- Homebrew package manager (recommended)
- Admin privileges

### Installation Methods

#### Method 1: macOS Installation (Recommended for Mac users)

**Step 1: Install Docker Desktop for Mac**
1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Install and start Docker Desktop
3. Verify Docker is running:
   ```bash
   docker --version
   ```

**Step 2: Install Homebrew (if not already installed)**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Step 3: Install containerlab using Homebrew**
```bash
# Add the containerlab tap
brew tap srl-labs/containerlab

# Install containerlab
brew install containerlab
```

**Alternative: Direct binary installation for macOS**
```bash
# Download the latest macOS binary
curl -L https://github.com/srl-labs/containerlab/releases/latest/download/containerlab_darwin_amd64.tar.gz -o containerlab.tar.gz

# For Apple Silicon Macs (M1/M2), use:
# curl -L https://github.com/srl-labs/containerlab/releases/latest/download/containerlab_darwin_arm64.tar.gz -o containerlab.tar.gz

# Extract the binary
tar -xf containerlab.tar.gz

# Move to a directory in your PATH
sudo mv containerlab /usr/local/bin/

# Make it executable
sudo chmod +x /usr/local/bin/containerlab
```

#### Method 2: Linux Package Manager Installation

For Debian/Ubuntu:
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

For RHEL/CentOS/Fedora:
```bash
# Add repository
sudo dnf config-manager --add-repo=https://yum.fury.io/netdevops/

# Install containerlab
sudo dnf install containerlab
```

#### Method 3: Quick Setup Script (Linux/macOS)

For a faster installation on both Linux and macOS:
```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

#### Method 4: Build from Source (Linux/macOS)

If you prefer to build from source:

**For Linux:**
```bash
# Install Go (if not already installed)
sudo apt update
sudo apt install -y golang-go

# Clone the repository
git clone https://github.com/srl-labs/containerlab.git
cd containerlab

# Build and install
make build
sudo make install
```

**For macOS:**
```bash
# Install Go using Homebrew (if not already installed)
brew install go

# Clone the repository
git clone https://github.com/srl-labs/containerlab.git
cd containerlab

# Build and install
make build
sudo make install
```

### Verify Installation

To verify that containerlab is installed correctly:
```bash
containerlab version
```

This should display the installed version of containerlab.

### macOS-Specific Notes

**Important considerations for macOS users:**

1. **Docker Desktop Configuration**: Ensure Docker Desktop has sufficient resources allocated:
   - Go to Docker Desktop → Preferences → Resources
   - Allocate at least 4GB RAM and 2 CPU cores for basic labs
   - For multiple routers, consider 8GB+ RAM

2. **File Sharing**: Docker Desktop needs access to your working directory:
   - Go to Docker Desktop → Preferences → Resources → File Sharing
   - Ensure your working directory is included in the shared paths

3. **Network Limitations**: macOS Docker Desktop runs in a VM, which may have some networking limitations compared to native Linux Docker

4. **Performance**: Container startup times may be slightly slower on macOS compared to native Linux installations

## Creating a Topology with Two Cisco Routers

### Topology Overview

```
+-------+                   +-------+
|       |eth1      eth1     |       |
| r1    +-------------------+ r2    |
|       |192.168.12.1/24    |       |
+-------+             192.168.12.2/24+-------+
```

### Create the Topology File

Create a file named `cisco-lab.yml` with the following content:

```yaml
name: cisco-lab

topology:
  nodes:
    r1:
      kind: cisco_ios
      image: cisco/ios:latest
      mgmt-ipv4: 172.20.20.11
      
    r2:
      kind: cisco_ios
      image: cisco/ios:latest
      mgmt-ipv4: 172.20.20.12
      
  links:
    - endpoints: ["r1:eth1", "r2:eth1"]
```

> **Note**: Replace `cisco/ios:latest` with the actual Cisco router image you have available. The image name and format may vary depending on your environment and the specific Cisco image you're using.

## Deploying the Topology

To deploy the lab:

**On Linux:**
```bash
sudo containerlab deploy -t cisco-lab.yml
```

**On macOS (Docker Desktop):**
```bash
containerlab deploy -t cisco-lab.yml
```

This command will:
1. Pull the necessary container images (if not already present)
2. Create the network topology
3. Start the containers
4. Configure the links between them

> **Note**: On macOS with Docker Desktop, you typically don't need `sudo` to run containerlab commands, as Docker Desktop handles the necessary permissions.

## Configuring the Routers

### Configure the First Router (r1)

```bash
# Connect to the router
docker exec -it clab-cisco-lab-r1 /bin/bash

# Enter configuration mode
enable
configure terminal

# Configure interface
interface GigabitEthernet0/1
  ip address 192.168.12.1 255.255.255.0
  no shutdown
  exit

# Configure loopback for testing
interface Loopback0
  ip address 10.1.1.1 255.255.255.255
  exit

# Save configuration
write memory
exit
```

### Configure the Second Router (r2)

```bash
# Connect to the router
docker exec -it clab-cisco-lab-r2 /bin/bash

# Enter configuration mode
enable
configure terminal

# Configure interface
interface GigabitEthernet0/1
  ip address 192.168.12.2 255.255.255.0
  no shutdown
  exit

# Configure loopback for testing
interface Loopback0
  ip address 10.2.2.2 255.255.255.255
  exit

# Save configuration
write memory
exit
```

## Configuring OSPF

OSPF (Open Shortest Path First) is a widely used interior gateway protocol that helps routers dynamically learn and advertise routes. Let's configure OSPF on our Cisco routers.

### Configure OSPF on the First Router (r1)

```bash
# Connect to the router
docker exec -it clab-cisco-lab-r1 /bin/bash

# Enter configuration mode
enable
configure terminal

# Configure OSPF
router ospf 1
  router-id 1.1.1.1
  network 192.168.12.0 0.0.0.255 area 0
  network 10.1.1.1 0.0.0.0 area 0
  exit

# Save configuration
write memory
exit
```

### Configure OSPF on the Second Router (r2)

```bash
# Connect to the router
docker exec -it clab-cisco-lab-r2 /bin/bash

# Enter configuration mode
enable
configure terminal

# Configure OSPF
router ospf 1
  router-id 2.2.2.2
  network 192.168.12.0 0.0.0.255 area 0
  network 10.2.2.2 0.0.0.0 area 0
  exit

# Save configuration
write memory
exit
```

## Verifying the Setup

### Check Interface Status

On r1:
```bash
docker exec -it clab-cisco-lab-r1 /bin/bash
enable
show ip interface brief
```

On r2:
```bash
docker exec -it clab-cisco-lab-r2 /bin/bash
enable
show ip interface brief
```

### Test Connectivity

From r1 to r2:
```bash
docker exec -it clab-cisco-lab-r1 /bin/bash
enable
ping 192.168.12.2
```

From r2 to r1:
```bash
docker exec -it clab-cisco-lab-r2 /bin/bash
enable
ping 192.168.12.1
```

### Verify OSPF Configuration

On r1:
```bash
docker exec -it clab-cisco-lab-r1 /bin/bash
enable
show ip ospf neighbor
show ip ospf interface brief
show ip route ospf
```

Expected output for `show ip ospf neighbor`:
```
Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           1   FULL/BDR        00:00:33    192.168.12.2    GigabitEthernet0/1
```

On r2:
```bash
docker exec -it clab-cisco-lab-r2 /bin/bash
enable
show ip ospf neighbor
show ip ospf interface brief
show ip route ospf
```

### Test OSPF Connectivity

From r1 to r2's loopback:
```bash
docker exec -it clab-cisco-lab-r1 /bin/bash
enable
ping 10.2.2.2
```

From r2 to r1's loopback:
```bash
docker exec -it clab-cisco-lab-r2 /bin/bash
enable
ping 10.1.1.1
```

## Alternative: Using FRRouting (FRR)

If you don't have access to Cisco router images, you can use FRRouting (FRR) as a free alternative.

### Create a Topology File for FRR

Create a file named `frr-lab.yml` with the following content:

```yaml
name: frr-lab

topology:
  nodes:
    router1:
      kind: linux
      image: frrouting/frr:latest
      mgmt-ipv4: 172.20.20.11
      binds:
        - daemons:/etc/frr/daemons
      
    router2:
      kind: linux
      image: frrouting/frr:latest
      mgmt-ipv4: 172.20.20.12
      binds:
        - daemons:/etc/frr/daemons
      
  links:
    - endpoints: ["router1:eth1", "router2:eth1"]
```

### Create a Daemons File

Create a file named `daemons` to enable the required FRR daemons:

```
zebra=yes
bgpd=no
ospfd=yes
ospf6d=no
ripd=no
ripngd=no
isisd=no
pimd=no
ldpd=no
nhrpd=no
eigrpd=no
babeld=no
sharpd=no
pbrd=no
bfdd=no
fabricd=no
vrrpd=no
pathd=no
```

### Deploy the FRR Lab

**On Linux:**
```bash
sudo containerlab deploy -t frr-lab.yml
```

**On macOS (Docker Desktop):**
```bash
containerlab deploy -t frr-lab.yml
```

### Configure the First FRR Router

```bash
# Connect to the router
docker exec -it clab-frr-lab-router1 vtysh

# Configure interfaces and routing
configure terminal
interface eth1
  ip address 192.168.12.1/24
  no shutdown
  exit

interface lo
  ip address 10.1.1.1/32
  exit

write memory
exit
```

### Configure the Second FRR Router

```bash
# Connect to the router
docker exec -it clab-frr-lab-router2 vtysh

# Configure interfaces and routing
configure terminal
interface eth1
  ip address 192.168.12.2/24
  no shutdown
  exit

interface lo
  ip address 10.2.2.2/32
  exit

write memory
exit
```

### Verify FRR Setup

Check interface status on router1:
```bash
docker exec -it clab-frr-lab-router1 vtysh -c "show interface brief"
```

Test connectivity from router1 to router2:
```bash
docker exec -it clab-frr-lab-router1 ping 192.168.12.2
```

### Configure OSPF on FRR Routers

For router1:
```bash
# Connect to the router
docker exec -it clab-frr-lab-router1 vtysh

# Configure OSPF
configure terminal
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 10.1.1.1/32 area 0
  exit
write memory
exit
```

For router2:
```bash
# Connect to the router
docker exec -it clab-frr-lab-router2 vtysh

# Configure OSPF
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
write memory
exit
```

### Verify OSPF on FRR

Check OSPF neighbors on router1:
```bash
docker exec -it clab-frr-lab-router1 vtysh -c "show ip ospf neighbor"
```

Expected output:
```
Neighbor ID     Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
2.2.2.2           1 Full/DR           38.997s 192.168.12.2    eth1:192.168.12.1        0     0     0
```

Check OSPF routes on router1:
```bash
docker exec -it clab-frr-lab-router1 vtysh -c "show ip route ospf"
```

Test OSPF connectivity from router1 to router2's loopback:
```bash
docker exec -it clab-frr-lab-router1 ping 10.2.2.2
```

## Troubleshooting Common Issues

### Issue: Containers fail to start

**Solution**:
- Check Docker service status: `systemctl status docker`
- Ensure you have enough resources (CPU, RAM)
- Check Docker logs: `docker logs clab-cisco-lab-r1`

### Issue: Unable to connect to routers

**Solution**:
- Verify the containers are running: `docker ps`
- Check if the management IP is accessible: `ping 172.20.20.11`
- Ensure the container has the expected shell or CLI: `docker exec -it clab-cisco-lab-r1 /bin/bash`

### Issue: Unable to ping between routers

**Solution**:
- Check interface status: `show ip interface brief`
- Verify IP addresses are correctly configured
- Check for any ACLs or firewall rules
- Ensure interfaces are in the "up/up" state

### Issue: "Permission denied" errors

**Solution**:
- Run containerlab with sudo
- Check file permissions for topology files
- Ensure Docker socket permissions are correct

## Cleaning Up

To destroy the lab and clean up all resources:

**On Linux:**
```bash
sudo containerlab destroy -t cisco-lab.yml
```

**On macOS (Docker Desktop):**
```bash
containerlab destroy -t cisco-lab.yml
```

Or for the FRR lab:

**On Linux:**
```bash
sudo containerlab destroy -t frr-lab.yml
```

**On macOS (Docker Desktop):**
```bash
containerlab destroy -t frr-lab.yml
```

## Conclusion

This guide has provided you with a complete workflow for:

1. Installing containerlab on your system using multiple methods
2. Creating a topology with two Cisco routers
3. Deploying the topology using containerlab
4. Configuring basic IP addressing on the routers
5. Setting up OSPF routing between the routers
6. Verifying the configuration and connectivity
7. Using FRRouting (FRR) as a free alternative to Cisco router images

By following these steps, you can create a functional network lab environment for testing and learning networking concepts. The containerlab approach offers significant advantages over traditional virtualization, including faster startup times, lower resource usage, and better integration with modern DevOps tools.

For more information and advanced configurations, refer to the [official containerlab documentation](https://containerlab.dev/).