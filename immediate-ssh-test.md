# Immediate SSH Test - R2 is Running!

## Current Status
✅ **R2 (cisco-lab-R2)** - Running successfully with SSH on port 2202  
❌ **R1 (cisco-lab-R1)** - Failed due to IP address conflict

## Test SSH to R2 Right Now

Since R2 is already running, you can test SSH access immediately:

```bash
# SSH to Router R2 (currently running)
ssh router@localhost -p 2202
# Password: cisco123
```

## If SSH doesn't work immediately:

### Option 1: Wait for SSH to initialize
The SSH service might still be starting up. Wait 30-60 seconds and try again.

### Option 2: Check if SSH is ready
```bash
# Check if SSH port is listening
docker exec cisco-lab-R2 netstat -tlnp | grep :22

# Check SSH process
docker exec cisco-lab-R2 ps aux | grep ssh
```

### Option 3: Use Docker exec as backup
```bash
# Login via Docker exec
docker exec -it cisco-lab-R2 bash

# Then inside the container
vtysh
```

## Fix Both Routers

To get both R1 and R2 working with SSH:

```bash
# Use the fixed version with different IP addresses
./start-routers-ssh-fixed.sh
```

This will:
- Clean up existing containers
- Start both routers with fixed IP addresses (172.20.20.21 and 172.20.20.22)
- Wait for SSH to initialize
- Test SSH connectivity

## SSH Connection Details (Fixed Version)

| Router | SSH Command | Password | Management IP | Status |
|--------|-------------|----------|---------------|---------|
| R1 | `ssh router@localhost -p 2201` | cisco123 | 172.20.20.21 | Will work with fixed version |
| R2 | `ssh router@localhost -p 2202` | cisco123 | 172.20.20.22 | Will work with fixed version |

## Current R2 Test (Right Now)

Try this command right now:
```bash
ssh router@localhost -p 2202
```

If it asks for password, enter: `cisco123`

Once logged in, try:
```bash
router@R2:~$ router
R2# show version
R2# show interface brief
```

## Next Steps

1. **Test current R2**: `ssh router@localhost -p 2202`
2. **Fix both routers**: `./start-routers-ssh-fixed.sh`  
3. **SSH to both**: Use ports 2201 (R1) and 2202 (R2)
4. **Configure OSPF** and test connectivity