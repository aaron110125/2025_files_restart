# READY TO CONFIGURE OSPF! 

## Network Topology Confirmed ✅
- **R1**: 192.168.12.10/24 on eth0 (router-link)
- **R2**: 192.168.12.11/24 on eth0 (router-link)
- Both connected via 192.168.12.0/24 network

## Step 1: Test Basic Connectivity
```bash
# Test ping from R1 to R2
docker exec -it cisco-lab-R1 ping -c 3 192.168.12.11
```

This should work with 0% packet loss!

## Step 2: Configure OSPF on R1
```bash
# SSH into R1
ssh -p 2201 root@localhost
# Password: admin

# Configure OSPF
vtysh
configure terminal
interface eth0
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

## Step 3: Configure OSPF on R2
```bash
# SSH into R2
ssh -p 2202 root@localhost
# Password: admin

# Configure OSPF
vtysh
configure terminal
interface eth0
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

## Step 4: Verify OSPF Neighbors
```bash
# Check OSPF neighbors on R1
ssh -p 2201 root@localhost "vtysh -c 'show ip ospf neighbor'"

# Check OSPF neighbors on R2
ssh -p 2202 root@localhost "vtysh -c 'show ip ospf neighbor'"
```

Expected output:
```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
2.2.2.2           1 Full/DR           00:01:23        00:00:37  192.168.12.11   eth0:192.168.12.10
```

## Step 5: Test OSPF Routes
```bash
# Check OSPF routes
ssh -p 2201 root@localhost "vtysh -c 'show ip route ospf'"

# Test connectivity to loopbacks
ssh -p 2201 root@localhost "ping -c 3 2.2.2.2"
ssh -p 2202 root@localhost "ping -c 3 1.1.1.1"
```

## Your Network Diagram is Now Reality! 🎉

- **R1**: 192.168.12.10 (eth0 = Fa0/0 equivalent)
- **R2**: 192.168.12.11 (eth0 = Fa0/0 equivalent)
- **OSPF Area**: 0
- **Network**: 192.168.12.0/24

Start with the connectivity test: `docker exec -it cisco-lab-R1 ping -c 3 192.168.12.11`
Command to get into the lab: docker exec -it cisco-lab-R2 vtysh