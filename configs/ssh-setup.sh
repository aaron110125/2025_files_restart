#!/bin/bash

# SSH Setup Script for FRRouting Containers
echo "Setting up SSH access..."

# Install SSH server if not present
if ! command -v sshd &> /dev/null; then
    apt-get update -qq
    apt-get install -y openssh-server sudo
fi

# Create SSH directory
mkdir -p /var/run/sshd

# Create router user with password
useradd -m -s /bin/bash router
echo 'router:cisco123' | chpasswd

# Add router user to sudo group
usermod -aG sudo router

# Configure SSH
cat > /etc/ssh/sshd_config << 'EOF'
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

# Set root password
echo 'root:cisco123' | chpasswd

# Create SSH host keys if they don't exist
ssh-keygen -A

# Start SSH daemon
/usr/sbin/sshd -D &

# Add router user to frr group for vtysh access
usermod -aG frr router
usermod -aG frrvty router

# Create vtysh config for easier access
cat > /home/router/.bashrc << 'EOF'
# Router environment setup
export PS1='\u@\h:\w$ '
alias router='vtysh'
alias show='vtysh -c'
alias conf='vtysh -c "configure terminal"'

echo "Welcome to FRRouting Router"
echo "Use 'router' or 'vtysh' to access router CLI"
echo "Use 'show \"command\"' for quick show commands"
EOF

chown router:router /home/router/.bashrc

echo "SSH setup completed"