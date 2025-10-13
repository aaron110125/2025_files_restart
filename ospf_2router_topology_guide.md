# OSPF Topology with 2 Routers using Containerlab

This guide shows you how to create an OSPF topology with 2 routers using containerlab and FRRouting.

## Topology Overview

```
┌─────────────┐                    ┌─────────────┐
│   Router1   │ eth1 ──────── eth1 │   Router2   │
│ 10.1.1.1/32 │ 192.168.12.1/24    │ 10.2.2.2/32 │
│  (Area 0)   │                    │  (Area 0)   │
└─────────────┘                    └─────────────┘
```

## Step 1: Create the Topology File

Create a new file called `ospf-lab.yml` in your containerlab-labs directory:

```bash
cd ~/containerlab-labs
```

```yaml
name: ospf-lab

topology:
  nodes:
    router1:
      kind: linux
      image: frrouting/frr:latest
      binds:
        - daemons:/etc/frr/daemons
      
    router2:
      kind: linux
      image: frrouting/frr:latest
      binds:
        - daemons:/etc/frr/daemons
      
  links:
    - endpoints: ["router1:eth1", "router2:eth1"]
```

## Step 2: Create the FRR Daemons Configuration

Create a `daemons` file to enable OSPF:

```bash
cat > daemons << 'EOF'
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
EOF
```

## Step 3: Deploy the Lab

```bash
containerlab deploy --topo ospf-lab.yml
```

Expected output:
```
INFO Creating lab directory path=/lab/clab-ospf-lab
INFO Creating container name=router1
INFO Creating container name=router2
╭─────────────────────┬─────────────┬─────────┬─────────────────╮
│        Name         │ Kind/Image  │  State  │  IPv4/6 Address │
├─────────────────────┼─────────────┼─────────┼─────────────────┤
│ clab-ospf-lab-router1 │ linux       │ running │ 172.20.20.2     │
│                     │ frr:latest  │         │ 3fff:172:20:20::2│
├─────────────────────┼─────────────┼─────────┼─────────────────┤
│ clab-ospf-lab-router2 │ linux       │ running │ 172.20.20.3     │
│                     │ frr:latest  │         │ 3fff:172:20:20::3│
╰─────────────────────┴─────────────┴─────────┴─────────────────╯
```

## Step 4: Configure Router1

Connect to router1 and configure interfaces and OSPF:

```bash
docker exec -it clab-ospf-lab-router1 vtysh
```

In the FRR shell, run these commands:

```
configure terminal

! Configure the link interface
interface eth1
  ip address 192.168.12.1/24
  no shutdown
  exit

! Configure loopback interface
interface lo
  ip address 10.1.1.1/32
  exit

! Configure OSPF
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 10.1.1.1/32 area 0
  exit

! Save configuration
write memory
exit
```

## Step 5: Configure Router2

Connect to router2 and configure interfaces and OSPF:

```bash
docker exec -it clab-ospf-lab-router2 vtysh
```

In the FRR shell, run these commands:

```
configure terminal

! Configure the link interface
interface eth1
  ip address 192.168.12.2/24
  no shutdown
  exit

! Configure loopback interface
interface lo
  ip address 10.2.2.2/32
  exit

! Configure OSPF
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit

! Save configuration
write memory
exit
```

## Step 6: Verify OSPF Configuration

### Check OSPF Neighbors

On Router1:
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf neighbor"
```

Expected output:
```
Neighbor ID     Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
2.2.2.2           1 Full/DR           38.997s 192.168.12.2    eth1:192.168.12.1        0     0     0
```

On Router2:
```bash
docker exec -it clab-ospf-lab-router2 vtysh -c "show ip ospf neighbor"
```

### Check OSPF Routes

On Router1:
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip route ospf"
```

Expected output:
```
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, D - SHARP,
       F - PBR, f - OpenFabric,
       > - selected route, * - FIB route, q - queued route, r - rejected route

O   10.2.2.2/32 [110/20] via 192.168.12.2, eth1, weight 1, 00:01:23
```

### Test Connectivity

Test ping from Router1 to Router2's loopback:
```bash
docker exec -it clab-ospf-lab-router1 ping -c 3 10.2.2.2
```

Expected output:
```
PING 10.2.2.2 (10.2.2.2) 56(84) bytes of data.
64 bytes from 10.2.2.2: icmp_seq=1 ttl=64 time=0.123 ms
64 bytes from 10.2.2.2: icmp_seq=2 ttl=64 time=0.089 ms
64 bytes from 10.2.2.2: icmp_seq=3 ttl=64 time=0.095 ms

--- 10.2.2.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss
```

## Step 7: Advanced OSPF Verification Commands

### Check OSPF Database
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf database"
```

### Check OSPF Interface Details
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf interface"
```

### Check Full Routing Table
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip route"
```

### Monitor OSPF in Real-time
```bash
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf neighbor detail"
```

## Step 8: Troubleshooting OSPF

### Common Issues and Solutions

**Issue: No OSPF neighbors**
```bash
# Check if OSPF is running
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf"

# Check interface status
docker exec -it clab-ospf-lab-router1 vtysh -c "show interface brief"

# Check OSPF interface configuration
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf interface"
```

**Issue: Routes not appearing**
```bash
# Check OSPF database
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf database"

# Check if networks are properly advertised
docker exec -it clab-ospf-lab-router1 vtysh -c "show running-config"
```

## Step 9: Adding More Networks

You can add additional networks to advertise via OSPF:

```bash
docker exec -it clab-ospf-lab-router1 vtysh
```

```
configure terminal
router ospf
  network 10.10.10.0/24 area 0
  exit
write memory
exit
```

## Step 10: Clean Up

When you're done testing:

```bash
containerlab destroy --topo ospf-lab.yml
```

## Quick Reference Commands

```bash
# Deploy lab
containerlab deploy --topo ospf-lab.yml

# Connect to router
docker exec -it clab-ospf-lab-router1 vtysh

# Check OSPF neighbors
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip ospf neighbor"

# Check OSPF routes
docker exec -it clab-ospf-lab-router1 vtysh -c "show ip route ospf"

# Test connectivity
docker exec -it clab-ospf-lab-router1 ping 10.2.2.2

# Destroy lab
containerlab destroy --topo ospf-lab.yml
```

## Next Steps

- Try adding a third router to create a more complex topology
- Experiment with different OSPF areas
- Configure OSPF authentication
- Test OSPF convergence by shutting down interfaces
- Add static routes and redistribute them into OSPF

This setup gives you a fully functional OSPF lab environment for learning and testing!