# Shadowsocks to V2Ray Converter

A Python utility for converting Shadowsocks subscription files to V2Ray multi-inbound/multi-outbound configuration format, with Docker support for easy deployment. This tool allows you to run multiple proxy nodes simultaneously through different ports.

## Project Description

This project provides a tool to convert Shadowsocks subscription files into a V2Ray client configuration with multiple inbound and outbound connections. It intelligently selects nodes from different geographic regions to provide a balanced set of proxy options, allowing you to run multiple proxy nodes simultaneously. The tool:

1. Reads a Shadowsocks subscription file containing multiple server nodes
2. Filters out information nodes and organizes servers by geographic region
3. Selects representative nodes from each region (typically the first and last node from each region)
4. Generates a V2Ray configuration file with:
   - Multiple SOCKS5 inbound connections on different local ports (starting from 10001)
   - Multiple Shadowsocks outbound connections to the selected servers
   - Routing rules to direct traffic from each inbound port to its corresponding outbound server
5. Enables you to use multiple proxy nodes simultaneously through different local ports

The project also includes Docker support for easy deployment of the V2Ray service using the generated configuration.

## Installation

### Prerequisites

- Python 3.6 or higher
- PyYAML package (for Docker Compose file handling)
- Docker and Docker Compose (optional, for containerized deployment)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/v2ray-multi-socks5
   cd v2ray-multi-socks5
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Converting Shadowsocks Subscription to V2Ray

```bash
python main.py -i shadowsocks.json -o config.json -p 10001
```

Parameters:
- `-i, --input`: Input Shadowsocks JSON file (default: shadowsocks.json)
- `-o, --output`: Output V2Ray config file (default: config.json)
- `-p, --port`: Starting port number for local SOCKS5 servers (default: 10001)
- `-a, --append`: Append to existing config file instead of creating a new one (optional)
- `-d, --docker`: Docker Compose file to update with port mappings (default: docker-compose.yaml)

### Example Usage Scenarios

#### Basic Conversion

```bash
python main.py -i my_subscription.json -o v2ray_config.json
```

#### Append New Nodes to Existing Configuration

```bash
python main.py -i new_subscription.json -o existing_config.json -a
```

#### Custom Starting Port

```bash
python main.py -i shadowsocks.json -o config.json -p 20001
```

#### Update Docker Compose File

```bash
python main.py -i shadowsocks.json -o config.json -d my-docker-compose.yaml
```

### Running V2Ray with Docker

After generating the configuration file, you can run V2Ray using Docker:

```bash
docker-compose up -d
```

This will start a V2Ray container using the generated configuration file, exposing the SOCKS5 proxy ports.

## Configuration Format

### Input (Shadowsocks)

The input file should be a Shadowsocks subscription file, which is typically a JSON array of server configurations:

```json
[
    {
        "remarks": "Hong Kong-01",
        "server": "example-server.com",
        "server_port": 56001,
        "method": "chacha20-ietf-poly1305",
        "password": "your-password"
    },
    ...
]
```

### Output (V2Ray)

The generated V2Ray configuration includes:

- Multiple inbound SOCKS5 servers on different local ports
- Multiple outbound Shadowsocks connections to the selected servers
- Routing rules to connect each inbound port to its corresponding outbound server

This multi-inbound/multi-outbound configuration allows you to use different proxy servers simultaneously through different local ports. For example, you can configure different applications to use different proxy ports.

## How It Works

1. The script reads the Shadowsocks subscription file
2. It filters out information nodes (those with remarks containing "最新网址", "剩余流量", "过期时间")
3. It dynamically extracts and groups nodes by region, analyzing patterns in node names without relying on hardcoded region lists
4. From each region, it selects representative nodes:
   - Nodes are sorted to prioritize those with names starting with the region name
   - Typically selects the first and last node from each region
   - If a region has only one node, that node is still included
5. For each selected node, it creates:
   - A SOCKS5 inbound connection on a local port
   - A Shadowsocks outbound connection to the server
   - A routing rule connecting the inbound and outbound
6. The configuration is saved to the specified output file
7. If append mode is used, the tool adds new nodes to an existing configuration file
8. If a Docker Compose file is specified, the port mappings are automatically updated
9. The V2Ray service can then be run using this configuration

## Docker Deployment

The included `docker-compose.yaml` file configures a V2Ray container that:

- Uses the official V2Ray image (v2fly/v2fly-core)
- Maps the local ports to the container (automatically updated based on the generated configuration)
- Mounts the generated configuration file to the container
- Automatically restarts if it crashes

When you use the `-d` option, the script will automatically update the port mappings in the Docker Compose file to match the ports used in the generated configuration.

## Advanced Usage

### Using Different Proxy Servers for Different Applications

Since the tool creates multiple SOCKS5 proxies on different ports, you can configure different applications to use different proxy servers:

1. Web browser: Configure to use 127.0.0.1:10001 (Hong Kong server)
2. Download manager: Configure to use 127.0.0.1:10002 (Japan server)
3. Other applications: Configure to use other ports as needed

This allows you to optimize your connection based on the specific needs of each application.

### Customizing Node Selection

By default, the tool selects the first and last nodes from each region. If you want to modify this behavior, you can edit the `select_nodes_from_regions` function in the script.

## Troubleshooting

### Common Issues

1. **Port conflicts**: If you see errors about ports already being in use, use the `-p` option to specify a different starting port.

2. **Docker issues**: Make sure Docker and Docker Compose are properly installed and that you have permission to run Docker commands.

3. **JSON parsing errors**: Ensure your Shadowsocks subscription file is valid JSON. You can use online JSON validators to check.

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

[MIT License](LICENSE)