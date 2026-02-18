# OSPF Lab Deployment Guide - R1 and R2 Connected via Fa0/0

This guide will help you deploy the exact OSPF topology shown in your image:
- R1 and R2 routers in OSPF Area 0
- Connected via Fa0/0 interfaces (eth1 in containerlab)
- Using 192.168.12.0/24 network
- R1: 192.168.12.1, R2: 192.168.12.2

## Step 1: Deploy the Containerlab Topology

```bash
containerlab deploy --topo cisco-ospf-topology.yml
```

Expected output should show R1 and R2 containers running.

## Step 2: Configure R1 Router

Connect to R1 and apply the OSPF configuration:

```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh
```

Then run these commands in the FRR shell:

```
configure terminal

! Configure the link interface (simulating Fa0/0)
interface eth1
  ip address 192.168.12.1/24
  no shutdown
  exit

! Configure loopback interface
interface lo
  ip address 1.1.1.1/32
  exit

! Configure OSPF
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 1.1.1.1/32 area 0
  exit

! Save configuration
write memory
exit
```

## Step 3: Configure R2 Router

Connect to R2 and apply the OSPF configuration:

```bash
docker exec -it clab-cisco-ospf-lab-R2 vtysh
```

Then run these commands in the FRR shell:

```
configure terminal

! Configure the link interface (simulating Fa0/0)
interface eth1
  ip address 192.168.12.2/24
  no shutdown
  exit

! Configure loopback interface
interface lo
  ip address 2.2.2.2/32
  exit

! Configure OSPF
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 2.2.2.2/32 area 0
  exit

! Save configuration
write memory
exit
```

## Step 4: Verify OSPF Configuration

### Check OSPF Neighbors

On R1:
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf neighbor"
```

Expected output:
```
Neighbor ID     Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
2.2.2.2           1 Full/DR           38.997s 192.168.12.2    eth1:192.168.12.1        0     0     0
```

On R2:
```bash
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf neighbor"
```

Expected output:
```
Neighbor ID     Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
1.1.1.1           1 Full/BDR         38.997s 192.168.12.1    eth1:192.168.12.2        0     0     0
```

### Check OSPF Routes

On R1:
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip route ospf"
```

Expected to see route to R2's loopback (2.2.2.2/32).

On R2:
```bash
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip route ospf"
```

Expected to see route to R1's loopback (1.1.1.1/32).

### Test Connectivity

Test ping between routers:
```bash
# From R1 to R2's interface
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 192.168.12.2

# From R1 to R2's loopback
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 2.2.2.2

# From R2 to R1's interface
docker exec -it clab-cisco-ospf-lab-R2 ping -c 3 192.168.12.1

# From R2 to R1's loopback
docker exec -it clab-cisco-ospf-lab-R2 ping -c 3 1.1.1.1
```

## Step 5: Additional Verification Commands

### Check OSPF Database
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf database"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf database"
```

### Check Interface Status
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show interface brief"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show interface brief"
```

### Check OSPF Interface Details
```bash
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf interface"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf interface"
```

## Troubleshooting

If OSPF neighbors don't appear:
1. Check if interfaces are up: `show interface brief`
2. Verify IP addresses: `show ip interface brief`
3. Check OSPF configuration: `show running-config`
4. Verify OSPF is running: `show ip ospf`

## Clean Up

When finished testing:
```bash
containerlab destroy --topo cisco-ospf-topology.yml
```

## Quick Reference

- **R1 Access**: `docker exec -it clab-cisco-ospf-lab-R1 vtysh`
- **R2 Access**: `docker exec -it clab-cisco-ospf-lab-R2 vtysh`
- **R1 IP**: 192.168.12.1 (Fa0/0 equivalent: eth1)
- **R2 IP**: 192.168.12.2 (Fa0/0 equivalent: eth1)
- **OSPF Area**: 0
- **Network**: 192.168.12.0/24

This setup matches exactly what's shown in your network diagram!