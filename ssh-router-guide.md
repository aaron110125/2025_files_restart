# SSH Access to Cisco Routers Guide

## Quick Start - SSH Access

### 1. Start Routers with SSH
```bash
./start-routers-ssh.sh
```

### 2. SSH to Routers
```bash
# Connect to Router R1
ssh router@localhost -p 2201
# Password: cisco123

# Connect to Router R2  
ssh router@localhost -p 2202
# Password: cisco123
```

## SSH Connection Details

| Router | SSH Command | Password | Management IP | Router Link IP |
|--------|-------------|----------|---------------|----------------|
| R1 | `ssh router@localhost -p 2201` | cisco123 | 172.20.20.11 | 192.168.12.1 |
| R2 | `ssh router@localhost -p 2202` | cisco123 | 172.20.20.12 | 192.168.12.2 |

## Network Topology
```
    SSH Port 2201          SSH Port 2202
         ↓                       ↓
R1 (172.20.20.11) ---- 192.168.12.0/24 ---- R2 (172.20.20.12)
   (192.168.12.1)                            (192.168.12.2)
   
Loopbacks:
R1: 10.1.1.1/32
R2: 10.2.2.2/32
```

## Router CLI Access

### Once SSH connected, use these aliases:
```bash
router          # Enter FRRouting CLI (same as vtysh)
show "command"  # Quick show commands
conf            # Enter configuration mode
```

### Example SSH Session:
```bash
# SSH to router
ssh router@localhost -p 2201

# Once logged in
router@R1:~$ router
R1# show version
R1# show interface brief
R1# configure terminal
R1(config)# router ospf
R1(config-router)# ospf router-id 1.1.1.1
R1(config-router)# network 192.168.12.0/24 area 0
R1(config-router)# exit
R1(config)# exit
R1# write memory
```

## OSPF Configuration Example

### Router R1 Configuration:
```bash
ssh router@localhost -p 2201
# Password: cisco123

router
configure terminal
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 10.1.1.1/32 area 0
  exit
exit
write memory
```

### Router R2 Configuration:
```bash
ssh router@localhost -p 2202
# Password: cisco123

router
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
exit
write memory
```

## Verification Commands

### Check OSPF Status:
```bash
show ip ospf neighbor
show ip ospf interface
show ip route ospf
show ip ospf database
```

### Test Connectivity:
```bash
# From R1 to R2
ping 10.2.2.2
ping 192.168.12.2

# From R2 to R1  
ping 10.1.1.1
ping 192.168.12.1
```

## Alternative Access Methods

### Docker Exec (if SSH doesn't work):
```bash
# Access R1
docker exec -it cisco-lab-R1 bash
vtysh

# Access R2
docker exec -it cisco-lab-R2 bash
vtysh
```

### Direct Container SSH (from inside container network):
```bash
# SSH directly to container IP (from another container)
ssh router@172.20.20.11  # R1
ssh router@172.20.20.12  # R2
```

## Troubleshooting SSH

### If SSH connection fails:
1. **Check containers are running:**
   ```bash
   docker ps
   ```

2. **Check SSH ports are mapped:**
   ```bash
   docker port cisco-lab-R1
   docker port cisco-lab-R2
   ```

3. **Check SSH service in container:**
   ```bash
   docker exec cisco-lab-R1 ps aux | grep ssh
   ```

4. **Restart with SSH setup:**
   ```bash
   ./start-routers-ssh.sh
   ```

### If password doesn't work:
- Default password is: `cisco123`
- Root password is also: `cisco123`
- Try: `ssh root@localhost -p 2201`

## Files Created for SSH Access
- [`docker-compose-ssh.yml`](docker-compose-ssh.yml:1) - Docker Compose with SSH ports
- [`configs/ssh-setup.sh`](configs/ssh-setup.sh:1) - SSH configuration script
- [`start-routers-ssh.sh`](start-routers-ssh.sh:1) - SSH-enabled startup script
- [`ssh-router-guide.md`](ssh-router-guide.md:1) - This guide

## Security Notes
- This is for lab use only
- Default passwords should be changed in production
- SSH keys can be added for key-based authentication
- Containers run in privileged mode for networking features