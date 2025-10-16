#!/bin/bash

echo "=== Cisco Router Lab with SSH Setup (Fixed) ==="
echo "Cleaning up any existing containers..."
docker-compose -f docker-compose-ssh-fixed.yml down

echo "Starting routers with SSH access (fixed IP addresses)..."
docker-compose -f docker-compose-ssh-fixed.yml up -d

echo "Waiting for containers to start and SSH to initialize..."
sleep 15

echo "=== Container Status ==="
docker ps

echo ""
echo "=== SSH Connection Information ==="
echo "Router R1:"
echo "  SSH: ssh router@localhost -p 2201"
echo "  Password: cisco123"
echo "  Management IP: 172.20.20.21 (updated)"
echo ""
echo "Router R2:"
echo "  SSH: ssh router@localhost -p 2202" 
echo "  Password: cisco123"
echo "  Management IP: 172.20.20.22 (updated)"
echo ""
echo "=== Test SSH Connection ==="
echo "Testing R2 SSH connection..."
timeout 5 ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no router@localhost -p 2202 "echo 'R2 SSH working!'" 2>/dev/null || echo "R2 SSH not ready yet, try in a few seconds"
echo ""
echo "=== Alternative Login Methods ==="
echo "Docker exec R1: docker exec -it cisco-lab-R1 bash"
echo "Docker exec R2: docker exec -it cisco-lab-R2 bash"
echo ""
echo "=== Network Information ==="
echo "Router Link Network: 192.168.12.0/24"
echo "R1 Router Link IP: 192.168.12.1"
echo "R2 Router Link IP: 192.168.12.2"
echo "R1 Loopback: 10.1.1.1/32"
echo "R2 Loopback: 10.2.2.2/32"
echo ""
echo "=== Quick Commands ==="
echo "Once logged in via SSH, use:"
echo "  router     # Enter FRRouting CLI (vtysh)"
echo "  show \"show version\"  # Quick show commands"
echo "  conf       # Enter configuration mode"