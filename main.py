import json
import argparse
import os
import yaml
from collections import defaultdict

def convert_shadowsocks_to_v2ray(input_file, output_file, start_port=10001, append_mode=False, docker_compose_file=None):
    # 读取原始Shadowsocks配置
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            ss_configs = json.load(f)
        print(f"Successfully loaded {len(ss_configs)} nodes from {input_file}")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        return 0, 0
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_file}' is not valid JSON")
        return 0, 0
    except Exception as e:
        print(f"Error loading input file: {str(e)}")
        return 0, 0

    # 过滤掉信息节点（通常不包含地区名称）
    info_keywords = ["最新网址", "剩余流量", "过期时间"]
    valid_nodes = []
    for cfg in ss_configs:
        if "remarks" in cfg and not any(keyword in cfg["remarks"] for keyword in info_keywords):
            valid_nodes.append(cfg)

    print(f"Found {len(valid_nodes)} valid nodes after filtering info nodes")

    # 按地区分组节点
    region_keywords = ["Hong Kong", "Taiwan", "Japan", "Singapore", "USA", "UK", "Malaysia", "Turkey", "Argentina"]
    regions = defaultdict(list)
    for node in valid_nodes:
        if "remarks" not in node:
            continue

        remarks = node["remarks"]
        # 提取地区名称
        assigned = False
        for region in region_keywords:
            if region in remarks:
                # 检查节点名称是否以地域开头
                starts_with_region = remarks.startswith(region)
                # 将节点添加到对应地域，并标记是否以地域开头
                regions[region].append((node, starts_with_region))
                assigned = True
                break

        if not assigned:
            print(f"Warning: Node with remarks '{remarks}' could not be assigned to any region")

    print(f"Grouped nodes into {len(regions)} regions")
    for region, nodes in regions.items():
        print(f"  - {region}: {len(nodes)} nodes")

    # 从每个地区选择两个节点
    valid_configs = []
    for region, nodes in regions.items():
        if len(nodes) == 0:
            continue

        # 先按照是否以地域名称开头排序，优先选择以地域名称开头的节点
        sorted_nodes = sorted(nodes, key=lambda x: (not x[1], x[0]["remarks"]))

        if len(sorted_nodes) == 1:
            # 如果地区只有一个节点，仍然添加它
            valid_configs.append(sorted_nodes[0][0])
            print(f"  - Selected 1 node from {region}: {sorted_nodes[0][0]['remarks']}")
        else:
            # 选择该地区的前两个节点
            selected_nodes = sorted_nodes[:1]
            selected_nodes.append(sorted_nodes[len(sorted_nodes)-1])
            for node, starts_with_region in selected_nodes:
                valid_configs.append(node)
                print(f"  - Selected node from {region}: {node['remarks']}")
            print(f"  - Total: Selected {len(selected_nodes)} nodes from {region}")

    # 基础配置模板或读取现有配置
    if append_mode and os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                v2ray_config = json.load(f)
            print(f"Loaded existing configuration from {output_file} for appending")
            # 获取已使用的端口，以避免端口冲突
            used_ports = set(inbound['port'] for inbound in v2ray_config['inbounds'])
            if used_ports and start_port <= max(used_ports):
                start_port = max(used_ports) + 1
                print(f"Adjusted start port to {start_port} to avoid conflicts")
        except Exception as e:
            print(f"Error loading existing config file for appending: {str(e)}")
            print("Creating new configuration instead")
            v2ray_config = {
                "inbounds": [],
                "outbounds": [],
                "routing": {
                    "rules": [],
                    "domainStrategy": "IPIfNonMatch"
                }
            }
    else:
        v2ray_config = {
            "inbounds": [],
            "outbounds": [],
            "routing": {
                "rules": [],
                "domainStrategy": "IPIfNonMatch"
            }
        }

    current_port = start_port

    for idx, ss_cfg in enumerate(valid_configs, 1):
        # 生成入站配置 (SOCKS5)
        inbound_tag = f"in-{current_port}-{ss_cfg["remarks"]}"
        v2ray_config["inbounds"].append({
            "port": current_port,
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
        })

        # 生成出站配置 (Shadowsocks)
        outbound_tag = f"out-{current_port}-{ss_cfg["remarks"]}"
        v2ray_config["outbounds"].append({
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
        })

        # 添加路由规则
        v2ray_config["routing"]["rules"].append({
            "type": "field",
            "inboundTag": [inbound_tag],
            "outboundTag": outbound_tag
        })

        current_port += 1

    # 添加默认直连规则
    v2ray_config["outbounds"].append({
        "protocol": "freedom",
        "tag": "direct"
    })

    # 写入配置文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(v2ray_config, f, indent=2, ensure_ascii=False)
        print(f"Successfully wrote configuration to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
        return 0, 0

    # 更新 docker-compose.yaml 文件
    if docker_compose_file and os.path.exists(docker_compose_file):
        try:
            # 获取所有使用的端口
            all_ports = [inbound['port'] for inbound in v2ray_config['inbounds']]
            min_port = min(all_ports) if all_ports else start_port
            max_port = max(all_ports) if all_ports else start_port

            # 读取现有的 docker-compose 文件
            with open(docker_compose_file, 'r', encoding='utf-8') as f:
                docker_compose = yaml.safe_load(f)

            # 更新端口映射
            if 'services' in docker_compose and 'v2ray' in docker_compose['services']:
                # 替换端口映射
                port_mapping = f"{min_port}-{max_port}:{min_port}-{max_port}"
                docker_compose['services']['v2ray']['ports'] = [port_mapping]

                # 写回 docker-compose 文件
                with open(docker_compose_file, 'w', encoding='utf-8') as f:
                    yaml.dump(docker_compose, f, default_flow_style=False, sort_keys=False)
                print(f"Updated Docker Compose port mappings to {port_mapping}")
        except Exception as e:
            print(f"Error updating Docker Compose file: {str(e)}")

    return len(valid_configs), len(regions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Input Shadowsocks JSON file")
    parser.add_argument("-o", "--output", default="config.json", help="Output V2Ray config file")
    parser.add_argument("-p", "--port", type=int, default=10001, help="Starting port number")
    parser.add_argument("-a", "--append", action="store_true", help="Append to existing config file instead of creating a new one")
    parser.add_argument("-d", "--docker", default="docker-compose.yaml", help="Docker Compose file to update with port mappings")
    args = parser.parse_args()

    # 检查 Docker Compose 文件是否存在
    docker_file = args.docker if os.path.exists(args.docker) else None
    if args.docker and not docker_file:
        print(f"Warning: Docker Compose file '{args.docker}' not found, port mappings will not be updated")

    node_count, region_count = convert_shadowsocks_to_v2ray(
        args.input,
        args.output,
        args.port,
        args.append,
        docker_file
    )

    mode_str = "appended to" if args.append else "generated"
    print(f"Config {mode_str}: {args.output} with {node_count} nodes from {region_count} regions")