#!/bin/sh

# SSH Setup Script for Alpine Linux (FRRouting containers)
echo "Setting up SSH access for Alpine Linux..."

# Install SSH server
apk update
apk add openssh-server sudo

# Create SSH directory
mkdir -p /var/run/sshd

# Create router user with password
adduser -D -s /bin/bash router
echo 'router:cisco123' | chpasswd

# Add router user to wheel group (sudo equivalent in Alpine)
addgroup router wheel

# Configure SSH
cat > /etc/ssh/sshd_config << 'EOF'
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
UsePAM no
X11Forwarding no
PrintMotd no
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

# Set root password
echo 'root:cisco123' | chpasswd

# Generate SSH host keys
ssh-keygen -A

# Start SSH daemon
/usr/sbin/sshd -D &

# Add router user to frr group for vtysh access
addgroup router frr
addgroup router frrvty

# Create bash profile for router user
cat > /home/router/.profile << 'EOF'
# Router environment setup
export PS1='\u@\h:\w$ '
alias router='vtysh'
alias show='vtysh -c'
alias conf='vtysh -c "configure terminal"'

echo "Welcome to FRRouting Router"
echo "Use 'router' or 'vtysh' to access router CLI"
echo "Use 'show \"command\"' for quick show commands"
EOF

chown router:router /home/router/.profile

echo "SSH setup completed for Alpine Linux"