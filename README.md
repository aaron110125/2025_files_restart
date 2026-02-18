# 2025 Files Restart

This repository contains files for my 2025 restart project.

## Overview

This is a new beginning for my project files in 2025.

## MEMORY BANK: ACTIVE

### Complete Journey: From ContainerLab Installation to OSPF Configuration

Here is the comprehensive explanation of everything accomplished, from installation to a working OSPF lab.

### 🚀 Phase 1: ContainerLab Installation

#### Initial Setup on macOS

We started by installing the necessary components:

1. Docker Desktop Installation
- Downloaded and installed Docker Desktop for Mac.
- Configured resource allocation (4GB+ RAM, 2+ CPU cores).
- Enabled file sharing for the working directory.

2. ContainerLab Installation
- Used Homebrew method:

```bash
brew tap srl-labs/containerlab
brew install containerlab
```

- Alternative binary installation method was also documented.
- Verified installation with:

```bash
containerlab version
```

### 🏗️ Phase 2: Initial Topology Attempts

#### ContainerLab Native Approach

We initially tried using ContainerLab's native YAML format:

```yaml
name: cisco-ospf-lab
topology:
  nodes:
    R1:
      kind: linux
      image: frrouting/frr:latest
    R2:
      kind: linux
      image: frrouting/frr:latest
  links:
    - endpoints: ["R1:eth1", "R2:eth1"]
```

Challenge: ContainerLab networking was complex for OSPF configuration and router access.

### 🔄 Phase 3: Docker Compose Transition

#### Why We Switched

ContainerLab was powerful but overly complex for our two-router OSPF lab. We transitioned to Docker Compose for:

- Simpler network configuration.
- Better port mapping for SSH access.
- More predictable IP addressing.
- Easier troubleshooting.

#### Docker Compose Evolution

We went through several iterations:

- Basic Docker Compose (`docker-compose.yml`)
- SSH-enabled version (`docker-compose-ssh.yml`)
- Final working version (`docker-compose-ssh-fixed.yml`)

### 🌐 Phase 4: Network Architecture Design

#### Final Network Topology

```text
Management Network: 172.20.20.0/24
├── R1: 172.20.20.10 (SSH: port 2201)
└── R2: 172.20.20.11 (SSH: port 2202)

Router Link Network: 192.168.12.0/24
├── R1: 192.168.12.10
└── R2: 192.168.12.11

Loopback Networks:
├── R1: 10.1.1.1/32
└── R2: 10.2.2.2/32
```

#### Key Configuration Elements

- FRRouting image: `frrouting/frr:latest`
- Privileged containers: required for network manipulation
- Volume mounts: `./configs/daemons:/etc/frr/daemons:ro`
- SSH setup: custom script for Alpine Linux compatibility

### 🛠️ Phase 5: Router Access Solutions

#### SSH Access Challenges

Initial SSH attempts failed because:

- FRRouting containers use Alpine Linux, not Ubuntu.
- Different package managers (`apk` vs `apt`).
- Different SSH daemon configurations.

#### Working Solutions Developed

1. Direct Docker Exec (primary method):

```bash
docker exec -it cisco-lab-R1 bash
vtysh
```

2. SSH Access (alternative):

```bash
ssh -p 2201 root@localhost
# Password: admin
```

### 📋 Phase 6: OSPF Configuration Implementation

#### FRRouting Daemon Configuration

Created `configs/daemons` file:

```text
zebra=yes
ospfd=yes
# Other daemons disabled
```

#### OSPF Configuration Process

Router R1 configuration:

```bash
vtysh
configure terminal
interface lo
  ip address 1.1.1.1/32
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 1.1.1.1/32 area 0
write memory
```

Router R2 configuration:

```bash
vtysh
configure terminal
interface lo
  ip address 2.2.2.2/32
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 2.2.2.2/32 area 0
write memory
```

### 🔍 Phase 7: Verification and Testing

#### Connectivity Tests

Basic IP connectivity:

```bash
docker exec -it cisco-lab-R1 ping -c 3 192.168.12.11
```

OSPF neighbor verification:

```bash
docker exec cisco-lab-R1 vtysh -c "show ip ospf neighbor"
```

Route learning test:

```bash
docker exec cisco-lab-R1 ping -c 3 10.2.2.2  # R1 to R2 loopback
```

### 📚 Phase 8: Documentation and Automation

#### Comprehensive Documentation Created

- `mac_containerlab_installation_guide.md` - Complete installation guide
- `containerlab_cisco_setup_guide.md` - Topology setup instructions
- `Final-OSPF-Configuration.md` - Ready-to-use OSPF commands
- `working-router-access.md` - Immediate access methods

#### Automation Scripts

- `start-routers-ssh-fixed.sh` - Automated lab startup
- `deploy-ospf-lab.sh` - Complete deployment automation

### 🎯 Final Working Solution

#### Quick Start Commands

```bash
# 1. Start the lab
./start-routers-ssh-fixed.sh

# 2. Access routers
docker exec -it cisco-lab-R1 vtysh
docker exec -it cisco-lab-R2 vtysh

# 3. Verify OSPF
docker exec cisco-lab-R1 vtysh -c "show ip ospf neighbor"
docker exec cisco-lab-R2 vtysh -c "show ip ospf neighbor"

# 4. Test connectivity
docker exec cisco-lab-R1 ping -c 3 10.2.2.2
```

### 🏆 Key Achievements

- Successful installation: ContainerLab and Docker Desktop working on macOS
- Network lab creation: two-router topology with proper IP addressing
- OSPF implementation: full OSPF configuration with neighbor relationships
- Multiple access methods: both Docker exec and SSH access working
- Complete documentation: step-by-step guides for reproduction
- Automation: scripts for quick lab deployment and configuration

### 💡 Lessons Learned

- ContainerLab vs Docker Compose: Docker Compose was simpler for basic labs.
- Alpine Linux considerations: Different from Ubuntu in package management and SSH setup.
- FRRouting power: Excellent free alternative to Cisco IOS for learning OSPF.
- Network troubleshooting: Systematic approach to connectivity issues.
- Documentation importance: Detailed guides enable quick reproduction.

This journey took us from zero to a fully functional OSPF lab environment, with comprehensive documentation and automation scripts that make it easy to deploy and use for network learning and testing.
