#!/usr/bin/env python3
"""
Router Configuration Generator

This script generates Cisco IOS commands for configuring router interfaces and loopback addresses.
It takes router name, interface name, IP address, and subnet mask as input and outputs the
corresponding configuration commands.
"""

import ipaddress
import argparse
import sys


def cidr_to_subnet_mask(cidr):
    """
    Convert CIDR notation to subnet mask.
    
    Args:
        cidr (int): CIDR prefix length (e.g., 24 for /24)
    
    Returns:
        str: Subnet mask in dotted decimal format (e.g., 255.255.255.0)
    """
    try:
        # Convert CIDR to integer
        cidr = int(cidr)
        
        # Validate CIDR range
        if cidr < 0 or cidr > 32:
            return None
        
        # Create a binary string with cidr number of 1's followed by (32-cidr) 0's
        binary = '1' * cidr + '0' * (32 - cidr)
        
        # Split the binary string into 4 octets and convert to decimal
        octets = [binary[i:i+8] for i in range(0, 32, 8)]
        decimal_octets = [str(int(octet, 2)) for octet in octets]
        
        # Join the octets with dots
        return '.'.join(decimal_octets)
    except (ValueError, TypeError):
        return None


def validate_cidr(cidr):
    """
    Validate that the provided string is a valid CIDR prefix length.
    
    Args:
        cidr (str): CIDR prefix length to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        cidr_int = int(cidr)
        return 0 <= cidr_int <= 32
    except (ValueError, TypeError):
        return False


def generate_interface_config(router_name, interface_name, ip_address, subnet_mask):
    """
    Generate configuration commands for a router interface.
    
    Args:
        router_name (str): Name of the router
        interface_name (str): Name of the interface (e.g., 'fastethernet 0/0')
        ip_address (str): IP address for the interface
        subnet_mask (str): Subnet mask for the interface
    
    Returns:
        str: Configuration commands for the interface
    """
    # Determine if this is a loopback interface
    is_loopback = "loopback" in interface_name.lower()
    
    # Generate configuration commands
    config = [
        "enable",
        "conf t",
        f"interface {interface_name}",
        f"ip address {ip_address} {subnet_mask}",
    ]
    
    # Add 'no shutdown' for non-loopback interfaces
    if not is_loopback:
        config.append(f"no shutdown")
        config.append(f"exit")
        config.append(f"do write")
    else:
        config.append(f"exit")
        config.append(f"do write")
    
    return "\n".join(config)


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


def validate_subnet_mask(subnet_mask):
    """
    Validate that the provided string is a valid subnet mask.
    
    Args:
        subnet_mask (str): Subnet mask to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Convert to integer representation
        mask_parts = subnet_mask.split('.')
        if len(mask_parts) != 4:
            return False
        
        # Check each octet is a valid number between 0 and 255
        for part in mask_parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        # Additional check for valid subnet mask pattern (continuous 1s followed by continuous 0s)
        binary = ''.join([bin(int(x))[2:].zfill(8) for x in mask_parts])
        return '01' not in binary
    except (ValueError, AttributeError):
        return False


def interactive_mode():
    """
    Run the script in interactive mode, prompting the user for input.
    """
    print("Router Configuration Generator")
    print("-----------------------------")
    
    router_name = input("Enter router name (e.g., Router3): ")
    
    # Get interface configuration
    print("\nInterface Configuration:")
    interface_name = input("Enter interface name (e.g., fastethernet 0/0): ")
    
    while True:
        ip_address = input("Enter IP address: ")
        if validate_ip_address(ip_address):
            break
        print("Invalid IP address. Please try again.")
    
    # Ask for subnet mask format preference
    mask_format = input("Enter subnet mask as [1] CIDR notation (e.g., 24) or [2] dotted decimal (e.g., 255.255.255.0) [1/2]: ")
    
    if mask_format == "1":
        while True:
            cidr = input("Enter CIDR prefix length (0-32): ")
            if validate_cidr(cidr):
                subnet_mask = cidr_to_subnet_mask(cidr)
                print(f"Using subnet mask: {subnet_mask}")
                break
            print("Invalid CIDR prefix length. Please enter a number between 0 and 32.")
    else:
        while True:
            subnet_mask = input("Enter subnet mask (e.g., 255.255.255.0): ")
            if validate_subnet_mask(subnet_mask):
                break
            print("Invalid subnet mask. Please try again.")
    
    # Generate and display interface configuration
    interface_config = generate_interface_config(router_name, interface_name, ip_address, subnet_mask)
    print("\nInterface Configuration Commands:")
    print("--------------------------------")
    print(interface_config)
    
    # Ask if loopback configuration is needed
    configure_loopback = input("\nDo you want to configure a loopback interface? (y/n): ").lower()
    
    if configure_loopback == 'y':
        loopback_number = input("Enter loopback number (e.g., 0): ")
        
        # Always configure IP for loopback
        while True:
            loopback_ip = input("Enter loopback IP address: ")
            if validate_ip_address(loopback_ip):
                break
            print("Invalid IP address. Please try again.")
        
        # Ask for loopback subnet mask format preference
        mask_format = input("Enter loopback subnet mask as [1] CIDR notation (e.g., 32) or [2] dotted decimal (e.g., 255.255.255.255) [1/2]: ")
        
        if mask_format == "1":
            while True:
                loopback_cidr = input("Enter loopback CIDR prefix length (0-32, default 32): ") or "32"
                if validate_cidr(loopback_cidr):
                    loopback_mask = cidr_to_subnet_mask(loopback_cidr)
                    print(f"Using loopback subnet mask: {loopback_mask}")
                    break
                print("Invalid CIDR prefix length. Please enter a number between 0 and 32.")
        else:
            while True:
                loopback_mask = input("Enter loopback subnet mask (default 255.255.255.255): ") or "255.255.255.255"
                if validate_subnet_mask(loopback_mask):
                    break
                print("Invalid subnet mask. Please try again.")
            
        # Generate and display loopback configuration
        loopback_config = generate_interface_config(router_name, f"loopback {loopback_number}", loopback_ip, loopback_mask)
        print("\nLoopback Configuration Commands:")
        print("--------------------------------")
        print(loopback_config)


def command_line_mode():
    """
    Run the script in command-line mode, parsing arguments.
    """
    parser = argparse.ArgumentParser(description='Generate router configuration commands.')
    parser.add_argument('--router', required=True, help='Router name (e.g., Router3)')
    parser.add_argument('--interface', required=True, help='Interface name (e.g., "fastethernet 0/0")')
    parser.add_argument('--ip', required=True, help='IP address for the interface')
    parser.add_argument('--mask', help='Subnet mask for the interface (dotted decimal format)')
    parser.add_argument('--cidr', help='CIDR prefix length (alternative to --mask)')
    parser.add_argument('--loopback', action='store_true', help='Configure loopback interface')
    parser.add_argument('--loopback-number', default='0', help='Loopback interface number (default: 0)')
    parser.add_argument('--loopback-ip', help='IP address for the loopback interface (optional)')
    parser.add_argument('--loopback-mask', help='Subnet mask for the loopback interface (dotted decimal format)')
    parser.add_argument('--loopback-cidr', help='CIDR prefix length for loopback interface (alternative to --loopback-mask)')
    
    args = parser.parse_args()
    
    # Validate IP address
    if not validate_ip_address(args.ip):
        print(f"Error: Invalid IP address: {args.ip}")
        sys.exit(1)
    
    # Handle subnet mask or CIDR notation
    if args.cidr:
        if not validate_cidr(args.cidr):
            print(f"Error: Invalid CIDR prefix length: {args.cidr}")
            sys.exit(1)
        subnet_mask = cidr_to_subnet_mask(args.cidr)
    elif args.mask:
        # Check if mask is in CIDR format (just a number)
        if args.mask.isdigit() and validate_cidr(args.mask):
            subnet_mask = cidr_to_subnet_mask(args.mask)
        else:
            if not validate_subnet_mask(args.mask):
                print(f"Error: Invalid subnet mask: {args.mask}")
                sys.exit(1)
            subnet_mask = args.mask
    else:
        print("Error: Either --mask or --cidr must be provided")
        sys.exit(1)
    
    # Generate and display interface configuration
    interface_config = generate_interface_config(args.router, args.interface, args.ip, subnet_mask)
    print("\nInterface Configuration Commands:")
    print("--------------------------------")
    print(interface_config)
    
    # Generate loopback configuration if requested
    if args.loopback:
        if args.loopback_ip:
            # Validate loopback IP and mask if provided
            if not validate_ip_address(args.loopback_ip):
                print(f"Error: Invalid loopback IP address: {args.loopback_ip}")
                sys.exit(1)
            
            # Handle loopback subnet mask or CIDR notation
            loopback_mask = "255.255.255.255"  # Default
            
            if args.loopback_cidr:
                if not validate_cidr(args.loopback_cidr):
                    print(f"Error: Invalid loopback CIDR prefix length: {args.loopback_cidr}")
                    sys.exit(1)
                loopback_mask = cidr_to_subnet_mask(args.loopback_cidr)
            elif args.loopback_mask:
                # Check if mask is in CIDR format (just a number)
                if args.loopback_mask.isdigit() and validate_cidr(args.loopback_mask):
                    loopback_mask = cidr_to_subnet_mask(args.loopback_mask)
                else:
                    if not validate_subnet_mask(args.loopback_mask):
                        print(f"Error: Invalid loopback subnet mask: {args.loopback_mask}")
                        sys.exit(1)
                    loopback_mask = args.loopback_mask
            
            loopback_config = generate_interface_config(args.router, f"loopback {args.loopback_number}",
                                                      args.loopback_ip, loopback_mask)
            print("\nLoopback Configuration Commands:")
            print("--------------------------------")
            print(loopback_config)
        else:
            # Just configure the loopback interface without an IP
            config = [
                "enable",
                "conf t",
                f"interface loopback {args.loopback_number}",
                "exit"
            ]
            print("\nLoopback Configuration Commands (without IP):")
            print("--------------------------------------------")
            print("\n".join(config))


if __name__ == "__main__":
    # If no command-line arguments are provided, run in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        command_line_mode()