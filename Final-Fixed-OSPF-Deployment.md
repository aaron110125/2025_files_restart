# Final OSPF Lab Deployment - Fixed eth1 Interface Issue

## Problem Fixed
The topology file was trying to configure eth1 before containerlab created the link. I've fixed this by letting containerlab create the eth1 interfaces first.

## Deployment Steps

### Step 1: Clean up and redeploy with fixed topology
```bash
# Clean up current deployment
containerlab destroy --topo cisco-ospf-topology.yml

# Deploy with corrected topology
containerlab deploy --topo cisco-ospf-topology.yml
```

### Step 2: Verify eth1 interfaces are created
```bash
# Check R1 interfaces (should now show eth1)
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show interface brief"

# Check R2 interfaces (should now show eth1)
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show interface brief"
```

You should now see `eth1` in both interface lists.

### Step 3: Configure IP addresses on eth1 interfaces
```bash
# Configure R1 eth1 interface
docker exec -it clab-cisco-ospf-lab-R1 ip addr add 192.168.12.1/24 dev eth1
docker exec -it clab-cisco-ospf-lab-R1 ip link set eth1 up

# Configure R2 eth1 interface
docker exec -it clab-cisco-ospf-lab-R2 ip addr add 192.168.12.2/24 dev eth1
docker exec -it clab-cisco-ospf-lab-R2 ip link set eth1 up
```

### Step 4: Test basic connectivity
```bash
# Test ping between routers
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 192.168.12.2
```

This should now work!

### Step 5: Enable OSPF daemon on both routers
```bash
# Enable OSPF on R1
docker exec -it clab-cisco-ospf-lab-R1 sh -c "echo 'ospfd=yes' >> /etc/frr/daemons && /usr/lib/frr/frrinit.sh restart"

# Enable OSPF on R2
docker exec -it clab-cisco-ospf-lab-R2 sh -c "echo 'ospfd=yes' >> /etc/frr/daemons && /usr/lib/frr/frrinit.sh restart"
```

### Step 6: Configure OSPF on R1
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh
```

In R1 vtysh:
```
configure terminal
interface eth1
  ip address 192.168.12.1/24
  no shutdown
  exit
interface lo
  ip address 1.1.1.1/32
  exit
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 1.1.1.1/32 area 0
  exit
write memory
exit
```

### Step 7: Configure OSPF on R2
```bash
docker exec -it clab-cisco-ospf-lab-R2 vtysh
```

In R2 vtysh:
```
configure terminal
interface eth1
  ip address 192.168.12.2/24
  no shutdown
  exit
interface lo
  ip address 2.2.2.2/32
  exit
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 2.2.2.2/32 area 0
  exit
write memory
exit
```

### Step 8: Verify OSPF neighbors
```bash
# Wait for OSPF convergence
sleep 30

# Check OSPF neighbors on both routers
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf neighbor"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf neighbor"
```

You should now see OSPF neighbors with "Full" state!

### Step 9: Test OSPF routes
```bash
# Check OSPF routes
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip route ospf"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip route ospf"

# Test connectivity to loopbacks
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 2.2.2.2
docker exec -it clab-cisco-ospf-lab-R2 ping -c 3 1.1.1.1
```

## What Was Fixed
- Removed premature eth1 configuration from the exec section
- Let containerlab create the eth1 interfaces through the links section
- Configure IP addresses after the interfaces are created

## Expected Results
- **Interface List**: Both routers should show eth1 interface
- **Connectivity**: Ping between 192.168.12.1 and 192.168.12.2 should work
- **OSPF Neighbors**: Should show "Full" state
- **OSPF Routes**: Should see each other's loopback addresses

This should now work perfectly and match your network diagram!