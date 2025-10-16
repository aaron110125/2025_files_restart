# SSH Router Commands - vtysh is Working! 🎉

## ✅ Good News!
vtysh is now working for your `router` user in the SSH session!

## 🔧 Commands for Your SSH Session

In your current SSH session (`R2:~$`), try these commands:

### Step 1: Test vtysh
```bash
vtysh
```

You should now see the FRRouting CLI prompt: `R2#`

### Step 2: Basic Router Commands
```bash
# Once in vtysh (R2# prompt):
show version
show interface brief
show ip route
```

### Step 3: Configure OSPF
```bash
# In vtysh (R2# prompt):
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
exit
write memory
```

### Step 4: Exit vtysh
```bash
# To exit back to shell:
exit
```

## 📋 Complete Example Session

```bash
R2:~$ vtysh
% Can't open configuration file /etc/frr/vtysh.conf due to 'No such file or directory'.

Hello, this is FRRouting (version 8.4_git).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

R2# show version
FRRouting 8.4_git (R2) on Linux(6.10.14-linuxkit).

R2# show interface brief
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         172.20.20.12/24
eth1            up      default         192.168.12.2/24
lo              up      default         10.2.2.2/32

R2# configure terminal
R2(config)# router ospf
R2(config-router)# ospf router-id 2.2.2.2
R2(config-router)# network 192.168.12.0/24 area 0
R2(config-router)# network 10.2.2.2/32 area 0
R2(config-router)# exit
R2(config)# exit
R2# write memory
Building Configuration...
Configuration saved to /etc/frr/frr.conf
R2# exit
R2:~$
```

## 🌐 Network Information

- **Your Router**: R2
- **Management IP**: 172.20.20.12
- **Router Link IP**: 192.168.12.2
- **Loopback IP**: 10.2.2.2/32

## 🚀 Next Steps

1. **Try vtysh now**: In your SSH session, type `vtysh`
2. **Configure OSPF**: Use the commands above
3. **Get R1 running**: Run `./start-routers-ssh-fixed.sh` to get both routers
4. **Test connectivity**: Ping between routers

## 📞 Quick Test

**In your SSH session right now, try:**
```bash
vtysh
show version
show interface brief
```

The warning about the config file is normal and can be ignored!