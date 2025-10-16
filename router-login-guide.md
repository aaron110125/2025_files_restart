# Router Login and Configuration Guide

## Current Status
✅ **R2 (cisco-lab-R2)** - Running successfully  
⚠️ **R1 (cisco-lab-R1)** - IP conflict issue (can be resolved)

## Quick Start Commands

### 1. Check Container Status
```bash
docker ps
```

### 2. Login to Router R2 (Currently Running)
```bash
# Method 1: Login to container shell first
docker exec -it cisco-lab-R2 bash

# Then inside the container, access FRRouting CLI
vtysh

# Method 2: Direct access to FRRouting CLI
docker exec -it cisco-lab-R2 vtysh
```

### 3. Restart Both Routers (Recommended)
```bash
# Use the provided script
./start-routers.sh

# Or manually
docker-compose down
docker-compose up -d
```

## Router Network Configuration

### Network Topology
```
R1 (172.20.20.11) ---- 192.168.12.0/24 ---- R2 (172.20.20.12)
   (192.168.12.1)                            (192.168.12.2)
   
Loopbacks:
R1: 10.1.1.1/32
R2: 10.2.2.2/32
```

## Basic FRRouting Commands

### Once logged into vtysh:

#### Check System Status
```bash
show version
show interface brief
show ip route
```

#### Configure OSPF (Example for R1)
```bash
configure terminal
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 10.1.1.1/32 area 0
  exit
exit
write memory
```

#### Configure OSPF (Example for R2)
```bash
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
exit
write memory
```

#### Verify OSPF
```bash
show ip ospf neighbor
show ip ospf interface
show ip route ospf
```

#### Test Connectivity
```bash
# From R1 to R2's loopback
ping 10.2.2.2

# From R2 to R1's loopback  
ping 10.1.1.1
```

## Troubleshooting

### If R1 won't start:
1. Clean up and restart:
   ```bash
   docker-compose down
   docker system prune -f
   docker-compose up -d
   ```

2. Check for IP conflicts:
   ```bash
   docker network ls
   docker network inspect 2025_files_restart_mgmt
   ```

3. Manual container start:
   ```bash
   docker run -d --name cisco-lab-R1-manual \
     --privileged \
     --network 2025_files_restart_mgmt \
     --ip 172.20.20.13 \
     frrouting/frr:latest
   ```

## Files Created
- `cisco-ospf-topology.yml` - Containerlab topology file
- `docker-compose.yml` - Docker Compose configuration
- `configs/daemons` - FRRouting daemon configuration
- `start-routers.sh` - Automated startup script
- `router-login-guide.md` - This guide

## Next Steps
1. Login to R2 using the commands above
2. Fix R1 startup issue
3. Configure OSPF on both routers
4. Test connectivity between routers