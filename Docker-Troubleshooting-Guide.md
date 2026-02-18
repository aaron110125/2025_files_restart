Y# Docker and Containerlab Troubleshooting Guide

## Issue: Docker daemon not running

**Error**: `docker: Cannot connect to the Docker daemon at unix:///Users/dcoaaron/.docker/run/docker.sock. Is the docker daemon running?`

### Solution:

1. **Start Docker Desktop**:
   - Open Docker Desktop application on your Mac
   - Wait for it to fully start (you'll see the Docker whale icon in the menu bar)
   - The status should show "Docker Desktop is running"

2. **Verify Docker is running**:
   ```bash
   docker --version
   docker ps
   ```

3. **If Docker Desktop is not installed**:
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start the application

## Complete Deployment Steps (Updated)

### Step 1: Start Docker Desktop
- Launch Docker Desktop application
- Wait for it to fully initialize

### Step 2: Verify Docker is running
```bash
docker --version
docker ps
```

### Step 3: Deploy the OSPF Lab
```bash
containerlab deploy --topo cisco-ospf-topology.yml
```

### Step 4: Configure the routers
```bash
# Configure R1
docker exec -i clab-cisco-ospf-lab-R1 vtysh < configs/R1-ospf-config.txt

# Configure R2  
docker exec -i clab-cisco-ospf-lab-R2 vtysh < configs/R2-ospf-config.txt
```

### Step 5: Verify OSPF
```bash
# Check OSPF neighbors
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf neighbor"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf neighbor"

# Test connectivity
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 192.168.12.2
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 2.2.2.2
```

## Alternative: Using Docker Compose (if containerlab issues persist)

If you continue having issues with containerlab, you can use the existing Docker Compose setup:

```bash
# Use the SSH-enabled version
docker-compose -f docker-compose-ssh-fixed.yml up -d

# Then configure OSPF manually via SSH
ssh -p 2201 root@localhost  # R1
ssh -p 2202 root@localhost  # R2
```

Once Docker Desktop is running, try the containerlab deployment again!