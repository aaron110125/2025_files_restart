#!/bin/bash

echo "=== Cisco Router Lab Setup ==="
echo "Cleaning up any existing containers..."
docker-compose down

echo "Starting routers with fresh deployment..."
docker-compose up -d

echo "Waiting for containers to start..."
sleep 5

echo "=== Container Status ==="
docker ps

echo ""
echo "=== Login Commands ==="
echo "To login to R1: docker exec -it cisco-lab-R1 bash"
echo "To login to R2: docker exec -it cisco-lab-R2 bash"
echo ""
echo "Once inside container, use: vtysh"
echo ""
echo "=== Network Information ==="
echo "R1 Management IP: 172.20.20.11"
echo "R2 Management IP: 172.20.20.12"
echo "Router Link: 192.168.12.0/24"
echo "R1 Router Link IP: 192.168.12.1"
echo "R2 Router Link IP: 192.168.12.2"