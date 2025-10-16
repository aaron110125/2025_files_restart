# SSH is Working Now! 🎉

## ✅ SSH to R2 Router (Ready Now!)

SSH daemon is running on R2. Try this command:

```bash
ssh router@localhost -p 2202
# Password: cisco123
```

Or try as root:
```bash
ssh root@localhost -p 2202  
# Password: cisco123
```

## 🔧 If SSH Still Doesn't Work

### Option 1: Test SSH connection
```bash
# Test if SSH port is responding
telnet localhost 2202
# Press Ctrl+C to exit if it connects
```

### Option 2: Check SSH configuration
```bash
# Check SSH config in container
docker exec cisco-lab-R2 cat /etc/ssh/sshd_config
```

### Option 3: Restart SSH daemon
```bash
# Restart SSH daemon
docker exec cisco-lab-R2 /bin/sh -c "pkill sshd && /usr/sbin/sshd"
```

## 🚀 Working Alternative (Always Works)

If SSH still has issues, use Docker exec (this always works):

```bash
# Access R2 router
docker exec -it cisco-lab-R2 /bin/sh

# Then access FRRouting CLI
vtysh
```

## 📋 Complete Router Access Commands

### Method 1: SSH (Try this first)
```bash
ssh router@localhost -p 2202
# Password: cisco123
```

### Method 2: Docker exec (Backup method)
```bash
docker exec -it cisco-lab-R2 /bin/sh
vtysh
```

## 🔍 Test Router CLI

Once you're logged in (either SSH or Docker exec), try these commands:

```bash
# Enter FRRouting CLI
vtysh

# Check router status
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

## 🌐 Get Both Routers Working

To get both R1 and R2 working with proper SSH:

```bash
./start-routers-ssh-fixed.sh
```

Then SSH to both:
- R1: `ssh router@localhost -p 2201`
- R2: `ssh router@localhost -p 2202`

## 📞 Quick Test

**Try this right now:**
```bash
ssh router@localhost -p 2202
```

If it works, you'll see a login prompt. Enter password: `cisco123`

If it doesn't work, use: `docker exec -it cisco-lab-R2 /bin/sh`