#!/bin/bash

echo "=== Deploying OSPF Containerlab Topology ==="
echo "This script will deploy R1 and R2 routers with OSPF Area 0 configuration"
echo "Network: 192.168.12.0/24 (R1: 192.168.12.1, R2: 192.168.12.2)"
echo ""

# Deploy the containerlab topology
echo "1. Deploying containerlab topology..."
containerlab deploy --topo cisco-ospf-topology.yml

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy containerlab topology"
    exit 1
fi

echo ""
echo "2. Waiting for containers to fully start..."
sleep 10

# Configure R1
echo "3. Configuring R1 with OSPF..."
docker exec -i clab-cisco-ospf-lab-R1 vtysh < configs/R1-ospf-config.txt

if [ $? -ne 0 ]; then
    echo "WARNING: R1 configuration may have failed"
fi

# Configure R2
echo "4. Configuring R2 with OSPF..."
docker exec -i clab-cisco-ospf-lab-R2 vtysh < configs/R2-ospf-config.txt

if [ $? -ne 0 ]; then
    echo "WARNING: R2 configuration may have failed"
fi

echo ""
echo "5. Waiting for OSPF convergence..."
sleep 15

echo ""
echo "=== Verification ==="
echo "6. Checking OSPF neighbors on R1:"
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip ospf neighbor"

echo ""
echo "7. Checking OSPF neighbors on R2:"
docker exec -it clab-cisco-ospf-lab-R2 vtysh -c "show ip ospf neighbor"

echo ""
echo "8. Checking OSPF routes on R1:"
docker exec -it clab-cisco-ospf-lab-R1 vtysh -c "show ip route ospf"

echo ""
echo "9. Testing connectivity - Ping from R1 to R2:"
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 192.168.12.2

echo ""
echo "10. Testing connectivity - Ping from R1 to R2's loopback:"
docker exec -it clab-cisco-ospf-lab-R1 ping -c 3 2.2.2.2

echo ""
echo "=== Deployment Complete ==="
echo "Your OSPF topology is now running!"
echo ""
echo "To access routers:"
echo "  R1: docker exec -it clab-cisco-ospf-lab-R1 vtysh"
echo "  R2: docker exec -it clab-cisco-ospf-lab-R2 vtysh"
echo ""
echo "To destroy the lab:"
echo "  containerlab destroy --topo cisco-ospf-topology.yml"