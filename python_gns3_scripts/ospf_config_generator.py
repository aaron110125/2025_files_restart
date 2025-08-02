#!/usr/bin/env python3
"""
OSPF Configuration Generator

This script generates Cisco IOS commands for configuring OSPF routing protocol.
It focuses on basic OSPF configuration with network advertisements.
"""

import argparse
import sys
import ipaddress


def validate_ip_address(ip_address):
    """
    Validate that the provided string is a valid IP address.
    
    Args:
        ip_address (str): IP address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def validate_network_address(network_address):
    """
    Validate that the provided string is a valid network address.
    
    Args:
        network_address (str): Network address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # For simplicity, we just check if it's a valid IP address format
        # In a production environment, you might want to check if it's actually a network address
        ipaddress.ip_address(network_address)
        return True
    except ValueError:
        return False


def validate_cidr(cidr):
    """
    Validate that the provided string is a valid CIDR prefix length.
    
    Args:
        cidr (str): CIDR prefix length to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Remove leading slash if present
        if cidr.startswith('/'):
            cidr = cidr[1:]
        
        cidr_int = int(cidr)
        return 0 <= cidr_int <= 32
    except (ValueError, TypeError):
        return False


def cidr_to_wildcard(cidr):
    """
    Convert CIDR notation to wildcard mask.
    
    Args:
        cidr (str): CIDR prefix length (e.g., "24" or "/24")
    
    Returns:
        str: Wildcard mask in dotted decimal format
    """
    try:
        # Remove leading slash if present
        if cidr.startswith('/'):
            cidr = cidr[1:]
        
        # Convert CIDR to integer
        cidr = int(cidr)
        
        # Validate CIDR range
        if cidr < 0 or cidr > 32:
            return None
        
        # Create a binary string with cidr number of 0's followed by (32-cidr) 1's
        binary = '0' * cidr + '1' * (32 - cidr)
        
        # Split the binary string into 4 octets and convert to decimal
        octets = [binary[i:i+8] for i in range(0, 32, 8)]
        decimal_octets = [str(int(octet, 2)) for octet in octets]
        
        # Join the octets with dots
        return '.'.join(decimal_octets)
    except (ValueError, TypeError):
        return None


def validate_wildcard_mask(wildcard_mask):
    """
    Validate that the provided string is a valid wildcard mask.
    
    Args:
        wildcard_mask (str): Wildcard mask to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check format
        mask_parts = wildcard_mask.split('.')
        if len(mask_parts) != 4:
            return False
        
        # Check each octet is a valid number between 0 and 255
        for part in mask_parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except (ValueError, AttributeError):
        return False


def validate_process_id(process_id):
    """
    Validate that the provided OSPF process ID is valid.
    
    Args:
        process_id (str): OSPF process ID to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        pid = int(process_id)
        return 1 <= pid <= 65535
    except (ValueError, TypeError):
        return False


def validate_area_id(area_id):
    """
    Validate that the provided OSPF area ID is valid.
    Area ID can be in decimal format (0-4294967295) or IP address format.
    
    Args:
        area_id (str): OSPF area ID to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if area_id is in IP address format
    if '.' in area_id:
        return validate_ip_address(area_id)
    
    # Check if area_id is a valid decimal number
    try:
        aid = int(area_id)
        return 0 <= aid <= 4294967295
    except (ValueError, TypeError):
        return False


def generate_ospf_config(process_id, networks):
    """
    Generate OSPF configuration commands.
    
    Args:
        process_id (str): OSPF process ID
        networks (list): List of tuples containing (network, wildcard_mask, area)
    
    Returns:
        list: List of configuration commands
    """
    config = [
        "enable",
        "conf t",
        f"router ospf {process_id}"
    ]
    
    for network, wildcard_mask, area in networks:
        config.append(f"network {network} {wildcard_mask} area {area}")
    
    config.append("do write")
    
    return config


def interactive_mode():
    """
    Run the script in interactive mode, prompting the user for input.
    """
    print("OSPF Configuration Generator")
    print("---------------------------")
    
    # Get OSPF process ID
    while True:
        process_id = input("Enter OSPF process ID (1-65535): ")
        if validate_process_id(process_id):
            break
        print("Invalid process ID. Please enter a number between 1 and 65535.")
    
    # Network advertisements
    networks = []
    while True:
        # Get network address
        while True:
            network = input("\nEnter network address (e.g., 192.168.1.0) or 'done' to finish: ")
            if network.lower() == 'done':
                break
            if validate_network_address(network):
                break
            print("Invalid network address. Please try again.")
        
        if network.lower() == 'done':
            break
        
        # Get wildcard mask or CIDR
        mask_format = input("Enter mask as [1] CIDR notation (e.g., /24) or [2] wildcard format (e.g., 0.0.0.255) [1/2]: ")
        
        if mask_format == "1":
            while True:
                cidr = input("Enter CIDR prefix length (0-32): ")
                if validate_cidr(cidr):
                    wildcard_mask = cidr_to_wildcard(cidr)
                    print(f"Using wildcard mask: {wildcard_mask}")
                    break
                print("Invalid CIDR prefix length. Please enter a number between 0 and 32.")
        else:
            while True:
                wildcard_mask = input("Enter wildcard mask (e.g., 0.0.0.255): ")
                if validate_wildcard_mask(wildcard_mask):
                    break
                print("Invalid wildcard mask. Please try again.")
        
        # Get area ID
        while True:
            area = input("Enter area ID (e.g., 0 or 0.0.0.0): ")
            if validate_area_id(area):
                break
            print("Invalid area ID. Please try again.")
        
        # Add network to the list
        networks.append((network, wildcard_mask, area))
    
    # Generate and display the configuration
    if networks:
        config = generate_ospf_config(process_id, networks)
        print("\nOSPF Configuration Commands:")
        print("---------------------------")
        print("\n".join(config))
    else:
        print("\nNo networks were configured for OSPF.")


def command_line_mode():
    """
    Run the script in command-line mode, parsing arguments.
    """
    parser = argparse.ArgumentParser(description='Generate OSPF configuration commands.')
    parser.add_argument('--process-id', required=True, help='OSPF process ID (1-65535)')
    parser.add_argument('--network', action='append', help='Network address to advertise (can be used multiple times)')
    parser.add_argument('--wildcard', action='append', help='Wildcard mask for the network (can be used multiple times)')
    parser.add_argument('--cidr', action='append', help='CIDR prefix length (alternative to --wildcard, can be used multiple times)')
    parser.add_argument('--area', action='append', help='OSPF area ID for the network (can be used multiple times)')
    
    args = parser.parse_args()
    
    # Validate process ID
    if not validate_process_id(args.process_id):
        print(f"Error: Invalid OSPF process ID: {args.process_id}")
        sys.exit(1)
    
    # Process network advertisements
    networks = []
    if args.network:
        # Check if we have the same number of networks and areas
        if not args.area:
            print("Error: For each network, you must provide an area")
            sys.exit(1)
        
        if len(args.network) != len(args.area):
            print("Error: The number of networks and areas must be the same")
            sys.exit(1)
        
        # Check if we have wildcard masks or CIDR notations
        if args.wildcard and args.cidr:
            print("Error: Cannot use both --wildcard and --cidr options together")
            sys.exit(1)
        
        if args.wildcard and len(args.network) != len(args.wildcard):
            print("Error: The number of networks and wildcard masks must be the same")
            sys.exit(1)
        
        if args.cidr and len(args.network) != len(args.cidr):
            print("Error: The number of networks and CIDR prefixes must be the same")
            sys.exit(1)
        
        if not args.wildcard and not args.cidr:
            print("Error: For each network, you must provide either a wildcard mask or a CIDR prefix")
            sys.exit(1)
        
        # Process each network
        for i in range(len(args.network)):
            network = args.network[i]
            area = args.area[i]
            
            # Validate network
            if not validate_network_address(network):
                print(f"Error: Invalid network address: {network}")
                sys.exit(1)
            
            # Validate area
            if not validate_area_id(area):
                print(f"Error: Invalid area ID: {area}")
                sys.exit(1)
            
            # Process mask (wildcard or CIDR)
            if args.wildcard:
                wildcard = args.wildcard[i]
                if not validate_wildcard_mask(wildcard):
                    print(f"Error: Invalid wildcard mask: {wildcard}")
                    sys.exit(1)
            else:  # CIDR
                cidr = args.cidr[i]
                if not validate_cidr(cidr):
                    print(f"Error: Invalid CIDR prefix length: {cidr}")
                    sys.exit(1)
                wildcard = cidr_to_wildcard(cidr)
            
            # Add network to the list
            networks.append((network, wildcard, area))
    
    # Generate and display the configuration
    if networks:
        config = generate_ospf_config(args.process_id, networks)
        print("\nOSPF Configuration Commands:")
        print("---------------------------")
        print("\n".join(config))
    else:
        print("\nNo networks were configured for OSPF.")


if __name__ == "__main__":
    # If no command-line arguments are provided, run in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        command_line_mode()