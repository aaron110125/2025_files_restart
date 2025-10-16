# Working Router Access - Immediate Solution

## 🎯 Current Working Method (Use This Now!)

Since R2 is running, you can access it immediately using Docker exec:

```bash
# Access Router R2 (currently running)
docker exec -it cisco-lab-R2 bash

# Once inside the container, access FRRouting CLI
vtysh
```

## 🔧 Complete Example Session

```bash
# Step 1: Access the container
docker exec -it cisco-lab-R2 bash

# Step 2: You're now in the router container
bash-5.1# vtysh

# Step 3: You're now in the FRRouting CLI
R2# show version
R2# show interface brief
R2# configure terminal
R2(config)# router ospf
R2(config-router)# ospf router-id 2.2.2.2
R2(config-router)# network 192.168.12.0/24 area 0
R2(config-router)# network 10.2.2.2/32 area 0
R2(config-router)# exit
R2(config)# exit
R2# write memory
R2# exit
bash-5.1# exit
```

## 🚀 Get Both Routers Working

The SSH setup was failing because the FRRouting container uses Alpine Linux, not Ubuntu. Here's the simple solution:

```bash
# Use the fixed startup script to get both routers running
./start-routers-ssh-fixed.sh
```

Then access both routers using Docker exec:

```bash
# Access Router R1
docker exec -it cisco-lab-R1 bash
vtysh

# Access Router R2  
docker exec -it cisco-lab-R2 bash
vtysh
```

## 📋 Router Configuration Example

### Configure OSPF on R1:
```bash
docker exec -it cisco-lab-R1 vtysh -c "
configure terminal
router ospf
  ospf router-id 1.1.1.1
  network 192.168.12.0/24 area 0
  network 10.1.1.1/32 area 0
  exit
exit
write memory
"
```

### Configure OSPF on R2:
```bash
docker exec -it cisco-lab-R2 vtysh -c "
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
exit
write memory
"
```

## 🔍 Verify OSPF and Connectivity

### Check OSPF neighbors:
```bash
# On R1
docker exec cisco-lab-R1 vtysh -c "show ip ospf neighbor"

# On R2
docker exec cisco-lab-R2 vtysh -c "show ip ospf neighbor"
```

### Test connectivity:
```bash
# From R1 to R2's loopback
docker exec cisco-lab-R1 ping -c 3 10.2.2.2

# From R2 to R1's loopback
docker exec cisco-lab-R2 ping -c 3 10.1.1.1
```

## 🌐 Network Topology

```
R1 (172.20.20.21) ---- 192.168.12.0/24 ---- R2 (172.20.20.22)
   (192.168.12.1)                            (192.168.12.2)
   
Loopbacks:
R1: 10.1.1.1/32
R2: 10.2.2.2/32
```

## ✅ Summary

1. **Current R2 access**: `docker exec -it cisco-lab-R2 bash` then `vtysh`
2. **Get both routers**: `./start-routers-ssh-fixed.sh`
3. **Access both**: Use `docker exec -it cisco-lab-R1 bash` and `docker exec -it cisco-lab-R2 bash`
4. **Configure OSPF**: Use the examples above
5. **Test connectivity**: Use ping commands above

This method works immediately and gives you full access to both routers!