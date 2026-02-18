# Commands to See All Interfaces

## In FRRouting (vtysh) CLI:

### Show all interfaces (brief summary)
```bash
show interface brief
```

### Show all interfaces (detailed information)
```bash
show interface
```

### Show specific interface details
```bash
show interface eth1
show interface lo
```

### Show IP addresses on interfaces
```bash
show ip interface brief
```

### Show interface status and configuration
```bash
show running-config interface
```

## From Linux shell (inside container):

### Show all network interfaces
```bash
ip addr show
# or
ip a
```

### Show interface statistics
```bash
ip -s link show
```

### Show routing table
```bash
ip route show
```

## Complete Example Commands:

### Access R1 and check interfaces
```bash
# Access R1
docker exec -it clab-cisco-ospf-lab-R1 vtysh

# Inside vtysh CLI:
show interface brief
show ip interface brief
show interface eth1
show interface lo
```

### Check from Linux level
```bash
# Check interfaces from Linux shell
docker exec -it clab-cisco-ospf-lab-R1 ip addr show
docker exec -it clab-cisco-ospf-lab-R1 ip route show
```

## Expected Output Examples:

**`show interface brief`:**
```
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         172.20.20.11/24
eth1            up      default         192.168.12.1/24
lo              up      default         1.1.1.1/32
```

**`show ip interface brief`:**
```
Interface         IP-Address      Status                Protocol
eth0              172.20.20.11    up                    up
eth1              192.168.12.1    up                    up
lo                1.1.1.1         up                    up
```

**`ip addr show`:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN
    inet 1.1.1.1/32 scope global lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    inet 172.20.20.11/24 scope global eth0
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    inet 192.168.12.1/24 scope global eth1
```

The most commonly used command is `show interface brief` in the vtysh CLI.