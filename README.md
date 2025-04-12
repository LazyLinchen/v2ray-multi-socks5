# Shadowsocks to V2Ray Converter

A Python utility for converting Shadowsocks configuration files to V2Ray configuration format, with Docker support for easy deployment.

## Project Description

This project provides a tool to convert Shadowsocks server configurations into a V2Ray client configuration. It intelligently selects nodes from different geographic regions to provide a balanced set of proxy options. The tool:

1. Reads a Shadowsocks configuration file containing multiple server nodes
2. Filters out information nodes and organizes servers by geographic region
3. Selects representative nodes from each region (typically the first and last node from each region)
4. Generates a V2Ray configuration file with:
   - SOCKS5 inbound connections on local ports (starting from 10001)
   - Shadowsocks outbound connections to the selected servers
   - Routing rules to direct traffic from each inbound port to its corresponding outbound server

The project also includes Docker support for easy deployment of the V2Ray service using the generated configuration.

## Installation

### Prerequisites

- Python 3.6 or higher
- Docker and Docker Compose (optional, for containerized deployment)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/v2ray.git
   cd v2ray
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Converting Shadowsocks Configuration to V2Ray

```bash
python main.py -i shadow.json -o config.json -p 10001
```

Parameters:
- `-i, --input`: Input Shadowsocks JSON file (required)
- `-o, --output`: Output V2Ray config file (default: config.json)
- `-p, --port`: Starting port number for local SOCKS5 servers (default: 10001)

### Running V2Ray with Docker

After generating the configuration file, you can run V2Ray using Docker:

```bash
docker-compose up -d
```

This will start a V2Ray container using the generated configuration file, exposing the SOCKS5 proxy ports (10001-10099).

## Configuration Format

### Input (Shadowsocks)

The input file should be a JSON array of Shadowsocks server configurations:

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

- Inbound SOCKS5 servers on local ports
- Outbound Shadowsocks connections to the selected servers
- Routing rules to connect each inbound port to its corresponding outbound server

## How It Works

1. The script reads the Shadowsocks configuration file
2. It filters out information nodes (those with remarks containing "最新网址", "剩余流量", "过期时间")
3. It groups nodes by region (Hong Kong, Taiwan, Japan, Singapore, USA, UK, Malaysia, Turkey, Argentina)
4. From each region, it selects representative nodes (typically the first and last node)
5. For each selected node, it creates:
   - A SOCKS5 inbound connection on a local port
   - A Shadowsocks outbound connection to the server
   - A routing rule connecting the inbound and outbound
6. The configuration is saved to the specified output file
7. The V2Ray service can then be run using this configuration

## Docker Deployment

The included `docker-compose.yaml` file configures a V2Ray container that:

- Uses the official V2Ray image
- Maps the local ports 10001-10099 to the container
- Mounts the generated configuration file
- Automatically restarts if it crashes

## License

[MIT License](LICENSE)