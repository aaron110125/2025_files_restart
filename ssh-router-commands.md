# SSH Router Commands - You're Connected! 🎉

## ✅ Current Status
You're successfully SSH'd into R2! The prompt `R2:~$` shows you're logged in.

## 🔧 Fix vtysh Access

Since you're logged in as the `router` user, you need to run vtysh as root or fix permissions. Try these commands in your SSH session:

### Method 1: Switch to root user
```bash
# In your SSH session (R2:~$), try:
su root
# Password: cisco123

# Then try vtysh:
vtysh
```

### Method 2: Run vtysh directly as root
```bash
# In your SSH session (R2:~$), try:
su -c "vtysh" root
# Password: cisco123
```

### Method 3: Use full path to vtysh
```bash
# In your SSH session (R2:~$), try:
/usr/bin/vtysh
```

## 📋 Router Commands to Try

Once you get vtysh working, try these commands:

```bash
# Basic router information
show version
show interface brief
show ip route

# Configure OSPF
configure terminal
router ospf
  ospf router-id 2.2.2.2
  network 192.168.12.0/24 area 0
  network 10.2.2.2/32 area 0
  exit
exit
write memory
```

## 🔍 Test Network Connectivity

```bash
# Test ping to R1 (if both routers are running)
ping 192.168.12.1
ping 10.1.1.1

# Check interfaces
show ip interface brief
```

## 🚀 Alternative: SSH as Root

You can also SSH directly as root:
```bash
# From your local terminal (new session):
ssh root@localhost -p 2202
# Password: cisco123
```

Then `vtysh` should work immediately.

## 📞 Quick Commands for Your Current SSH Session

**Try these in order in your R2:~$ prompt:**

1. `su root` (password: cisco123)
2. `vtysh`
3. `show version`
4. `show interface brief`

## 🌐 Network Information

- **R2 Management IP**: 172.20.20.12
- **R2 Router Link IP**: 192.168.12.2  
- **R2 Loopback**: 10.2.2.2/32
- **SSH Port**: 2202

Your SSH connection is working perfectly! Just need to get the right permissions for vtysh.