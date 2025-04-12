import argparse
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

import yaml

def load_shadowsocks_config(input_file: str) -> Tuple[List[Dict[str, Any]], bool]:
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            ss_configs = json.load(f)
        print(f"Successfully loaded {len(ss_configs)} nodes from {input_file}")
        return ss_configs, True
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        return [], False
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_file}' is not valid JSON")
        return [], False
    except Exception as e:
        print(f"Error loading input file: {str(e)}")
        return [], False


def filter_info_nodes(ss_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out information nodes that don't represent actual servers.
    Args:
        ss_configs: List of Shadowsocks configurations
    Returns:
        Filtered list of valid server nodes
    """
    info_keywords = ["最新网址", "剩余流量", "过期时间"]
    valid_nodes = []

    for cfg in ss_configs:
        if "remarks" in cfg and not any(keyword in cfg["remarks"] for keyword in info_keywords):
            valid_nodes.append(cfg)

    print(f"Found {len(valid_nodes)} valid nodes after filtering info nodes")
    return valid_nodes


def extract_regions(nodes: List[Dict[str, Any]]) -> Set[str]:
    """Extract possible region names from node remarks.
    Args:
        nodes: List of node configurations
    Returns:
        Set of possible region names
    """
    possible_regions = set()

    for node in nodes:
        if "remarks" not in node:
            continue

        remarks = node["remarks"]

        # Method 1: Assume region name is at the beginning until first hyphen or digit
        region_match = re.match(r'^([A-Za-z\s]+)[\-\d]', remarks)
        if region_match:
            region = region_match.group(1).strip()
            if region and len(region) > 1:  # Ensure region name is not a single letter
                possible_regions.add(region)
                continue

        # Method 2: Try to match common region formats like "XXX-01"
        region_match = re.search(r'([A-Za-z\s]+)[-\s]\d+', remarks)
        if region_match:
            region = region_match.group(1).strip()
            if region and len(region) > 1:
                possible_regions.add(region)

    print(f"Detected {len(possible_regions)} possible regions from node names")
    if possible_regions:
        print(f"  - Detected regions: {', '.join(sorted(possible_regions))}")

    return possible_regions


def group_nodes_by_region(nodes: List[Dict[str, Any]], possible_regions: Set[str]) -> Dict[str, List[Tuple[Dict[str, Any], bool]]]:
    """Group nodes by their region based on extracted region names.
    Args:
        nodes: List of node configurations
        possible_regions: Set of possible region names
    Returns:
        Dictionary mapping region names to lists of (node, starts_with_region) tuples
    """
    regions = defaultdict(list)

    for node in nodes:
        if "remarks" not in node:
            continue

        remarks = node["remarks"]
        assigned = False

        # Try to match with extracted region names
        for region in possible_regions:
            if region in remarks:
                # Check if node name starts with the region
                starts_with_region = remarks.startswith(region)
                # Add node to corresponding region with flag indicating if it starts with region name
                regions[region].append((node, starts_with_region))
                assigned = True
                break

        # If not assigned, try to extract region name again
        if not assigned:
            region_match = re.match(r'^([A-Za-z\s]+)[\-\d]', remarks)
            if region_match:
                region = region_match.group(1).strip()
                if region and len(region) > 1:
                    regions[region].append((node, True))
                    assigned = True

            # If still not assigned, categorize as "Other"
            if not assigned:
                regions["Other"].append((node, False))
                print(f"Info: Node with remarks '{remarks}' assigned to 'Other' region")

    print(f"Grouped nodes into {len(regions)} regions")
    for region, nodes in regions.items():
        print(f"  - {region}: {len(nodes)} nodes")

    return regions


def select_nodes_from_regions(regions: Dict[str, List[Tuple[Dict[str, Any], bool]]]) -> List[Dict[str, Any]]:
    """Select representative nodes from each region.
    For each region, selects up to two nodes - typically the first and last after sorting.
    If a region has only one node, that node is selected.
    Args:
        regions: Dictionary mapping region names to lists of (node, starts_with_region) tuples
    Returns:
        List of selected node configurations
    """
    valid_configs = []

    for region, nodes in regions.items():
        if not nodes:
            continue

        # Sort nodes by whether they start with region name, then by remarks
        sorted_nodes = sorted(nodes, key=lambda x: (not x[1], x[0]["remarks"]))

        if len(sorted_nodes) == 1:
            # If region has only one node, add it
            valid_configs.append(sorted_nodes[0][0])
            print(f"  - Selected 1 node from {region}: {sorted_nodes[0][0]['remarks']}")
        else:
            # Select first and last nodes from the region
            selected_nodes = [sorted_nodes[0], sorted_nodes[-1]]
            for node, starts_with_region in selected_nodes:
                valid_configs.append(node)
                print(f"  - Selected node from {region}: {node['remarks']}")
            print(f"  - Total: Selected {len(selected_nodes)} nodes from {region}")

    return valid_configs


def load_or_create_v2ray_config(output_file: str, append_mode: bool, start_port: int) -> Tuple[Dict[str, Any], int]:
    """Load existing V2Ray configuration or create a new one.
    Args:
        output_file: Path to the V2Ray configuration file
        append_mode: Whether to append to existing configuration
        start_port: Starting port number for inbound connections
    Returns:
        Tuple containing the V2Ray configuration and the adjusted start port
    """
    # Default configuration template
    default_config = {
        "inbounds": [],
        "outbounds": [],
        "routing": {
            "rules": [],
            "domainStrategy": "IPIfNonMatch"
        }
    }

    if append_mode and os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                v2ray_config = json.load(f)
            print(f"Loaded existing configuration from {output_file} for appending")

            # Get used ports to avoid port conflicts
            used_ports = set(inbound['port'] for inbound in v2ray_config['inbounds'])
            if used_ports and start_port <= max(used_ports):
                start_port = max(used_ports) + 1
                print(f"Adjusted start port to {start_port} to avoid conflicts")

            return v2ray_config, start_port
        except Exception as e:
            print(f"Error loading existing config file for appending: {str(e)}")
            print("Creating new configuration instead")
            return default_config, start_port
    else:
        return default_config, start_port


def create_v2ray_node_config(ss_cfg: Dict[str, Any], port: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Create V2Ray inbound, outbound, and routing rule configurations for a Shadowsocks node.
    Args:
        ss_cfg: Shadowsocks node configuration
        port: Port number for the inbound connection
    Returns:
        Tuple containing inbound, outbound, and routing rule configurations
    """
    # Create tag names based on port and node remarks
    inbound_tag = f"in-{port}-{ss_cfg['remarks']}"
    outbound_tag = f"out-{port}-{ss_cfg['remarks']}"

    # Create inbound configuration (SOCKS5)
    inbound_config = {
        "port": port,
        "protocol": "socks",
        "settings": {
            "auth": "noauth",
            "udp": True,
            "userLevel": 1
        },
        "tag": inbound_tag,
        "sniffing": {
            "enabled": True,
            "destOverride": ["http", "tls"]
        }
    }

    # Create outbound configuration (Shadowsocks)
    outbound_config = {
        "protocol": "shadowsocks",
        "settings": {
            "servers": [{
                "address": ss_cfg["server"],
                "port": ss_cfg["server_port"],
                "method": ss_cfg["method"],
                "password": ss_cfg["password"],
                "level": 1
            }]
        },
        "tag": outbound_tag
    }

    # Create routing rule
    routing_rule = {
        "type": "field",
        "inboundTag": [inbound_tag],
        "outboundTag": outbound_tag
    }

    return inbound_config, outbound_config, routing_rule


def write_v2ray_config(config: Dict[str, Any], output_file: str) -> bool:
    """Write V2Ray configuration to file.
    Args:
        config: V2Ray configuration dictionary
        output_file: Path to save the configuration
    Returns:
        Boolean indicating success
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Successfully wrote configuration to {output_file}")
        return True
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
        return False


def update_docker_compose(docker_compose_file: str, v2ray_config: Dict[str, Any], start_port: int) -> None:
    """Update Docker Compose file with port mappings.
    Args:
        docker_compose_file: Path to Docker Compose file
        v2ray_config: V2Ray configuration dictionary
        start_port: Starting port number
    """
    if not os.path.exists(docker_compose_file):
        print(f"Warning: Docker Compose file '{docker_compose_file}' not found, port mappings will not be updated")
        return

    try:
        # Get all used ports
        all_ports = [inbound['port'] for inbound in v2ray_config['inbounds']]
        min_port = min(all_ports) if all_ports else start_port
        max_port = max(all_ports) if all_ports else start_port

        # Read existing Docker Compose file
        with open(docker_compose_file, 'r', encoding='utf-8') as f:
            docker_compose = yaml.safe_load(f)

        # Update port mappings
        if 'services' in docker_compose and 'v2ray' in docker_compose['services']:
            # Replace port mapping
            port_mapping = f"{min_port}-{max_port}:{min_port}-{max_port}"
            with open(docker_compose_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace(docker_compose['services']['v2ray']['ports'][0], port_mapping)

            # Write back Docker Compose file
            with open(docker_compose_file, "w", encoding='utf-8') as f:
                f.write(content)

            print(f"Updated Docker Compose port mappings to {port_mapping}")
    except Exception as e:
        print(f"Error updating Docker Compose file: {str(e)}")


def convert_shadowsocks_to_v2ray(input_file: str, output_file: str, start_port: int = 10001,
                                append_mode: bool = False, docker_compose_file: Optional[str] = None) -> Tuple[int, int]:
    """Convert Shadowsocks configuration to V2Ray configuration.
    This function performs the following steps:
    1. Loads Shadowsocks configuration from the input file
    2. Filters out information nodes that don't represent actual servers
    3. Extracts region information from node names
    4. Groups nodes by region
    5. Selects representative nodes from each region (typically 2 per region)
    6. Creates V2Ray configuration for each selected node
    7. Writes the configuration to the output file
    8. Updates Docker Compose file with port mappings if specified
    Args:
        input_file: Path to the Shadowsocks JSON configuration file
        output_file: Path to save the V2Ray configuration
        start_port: Starting port number for inbound connections
        append_mode: Whether to append to existing configuration
        docker_compose_file: Path to Docker Compose file to update

    Returns:
        Tuple containing the count of nodes and regions
    """
    # Load Shadowsocks configuration
    ss_configs, success = load_shadowsocks_config(input_file)
    if not success:
        return 0, 0

    # Filter out information nodes
    valid_nodes = filter_info_nodes(ss_configs)

    # Extract regions and group nodes
    possible_regions = extract_regions(valid_nodes)
    regions = group_nodes_by_region(valid_nodes, possible_regions)

    # Select nodes from each region
    valid_configs = select_nodes_from_regions(regions)

    # Load or create V2Ray configuration
    v2ray_config, start_port = load_or_create_v2ray_config(output_file, append_mode, start_port)

    # Generate V2Ray configuration for each selected node
    current_port = start_port

    for ss_cfg in valid_configs:
        # Create inbound, outbound, and routing configurations
        inbound_config, outbound_config, routing_rule = create_v2ray_node_config(ss_cfg, current_port)

        # Add configurations to V2Ray config
        v2ray_config["inbounds"].append(inbound_config)
        v2ray_config["outbounds"].append(outbound_config)
        v2ray_config["routing"]["rules"].append(routing_rule)

        current_port += 1

    # Add default direct connection rule
    v2ray_config["outbounds"].append({
        "protocol": "freedom",
        "tag": "direct"
    })

    # Write configuration to file
    success = write_v2ray_config(v2ray_config, output_file)
    if not success:
        return 0, 0

    # Update Docker Compose file if specified
    if docker_compose_file:
        update_docker_compose(docker_compose_file, v2ray_config, start_port)

    return len(valid_configs), len(regions)

if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description="Convert Shadowsocks configuration to V2Ray configuration")
    parser.add_argument("-i", "--input", default="shadowsocks.json", help="Input Shadowsocks JSON file")
    parser.add_argument("-o", "--output", default="config.json", help="Output V2Ray config file")
    parser.add_argument("-p", "--port", type=int, default=10001, help="Starting port number")
    parser.add_argument("-a", "--append", action="store_true", help="Append to existing config file instead of creating a new one")
    parser.add_argument("-d", "--docker", default="docker-compose.yaml", help="Docker Compose file to update with port mappings")
    args = parser.parse_args()

    # Convert Shadowsocks configuration to V2Ray configuration
    node_count, region_count = convert_shadowsocks_to_v2ray(
        args.input,
        args.output,
        args.port,
        args.append,
        args.docker
    )

    # Print summary
    mode_str = "appended to" if args.append else "generated"
    print(f"Config {mode_str}: {args.output} with {node_count} nodes from {region_count} regions")