# Shadowsocks 转 V2Ray 配置转换器

一个用于将 Shadowsocks 订阅文件转换为 V2Ray 多入站/多出站配置格式的 Python 工具，支持 Docker 部署，便于快速使用。该工具允许您通过不同端口同时运行多个代理节点。

## 项目描述

本项目提供了一个工具，可以将 Shadowsocks 订阅文件转换为具有多个入站和出站连接的 V2Ray 客户端配置。它智能地从不同地理区域选择节点，提供平衡的代理选项，允许您同时使用多个代理节点。该工具：

1. 读取包含多个服务器节点的 Shadowsocks 订阅文件
2. 过滤掉信息节点并按地理区域组织服务器
3. 从每个区域选择代表性节点（通常是每个区域的第一个和最后一个节点）
4. 生成一个 V2Ray 配置文件，包含：
   - 不同本地端口上的多个 SOCKS5 入站连接（从 10001 开始）
   - 到所选服务器的多个 Shadowsocks 出站连接
   - 将每个入站端口的流量定向到其对应出站服务器的路由规则
5. 使您能够通过不同的本地端口同时使用多个代理节点

该项目还包括 Docker 支持，便于使用生成的配置部署 V2Ray 服务。

## 安装

### 前提条件

- Python 3.6 或更高版本
- PyYAML 包（用于处理 Docker Compose 文件）
- Docker 和 Docker Compose（可选，用于容器化部署）

### 设置

1. 克隆此仓库：
   ```bash
   git clone https://github.com/yourusername/v2ray-multi-socks5
   cd v2ray-multi-socks5
   ```

2. 安装所需的 Python 包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 将 Shadowsocks 订阅转换为 V2Ray

```bash
python main.py -i shadowsocks.json -o config.json -p 10001
```

参数：
- `-i, --input`：输入的 Shadowsocks JSON 文件（默认：shadowsocks.json）
- `-o, --output`：输出的 V2Ray 配置文件（默认：config.json）
- `-p, --port`：本地 SOCKS5 服务器的起始端口号（默认：10001）
- `-a, --append`：追加到现有配置文件而不是创建新文件（可选）
- `-d, --docker`：要更新端口映射的 Docker Compose 文件（默认：docker-compose.yaml）

### 使用示例

#### 基本转换

```bash
python main.py -i my_subscription.json -o v2ray_config.json
```

#### 追加新节点到现有配置

```bash
python main.py -i new_subscription.json -o existing_config.json -a
```

#### 自定义起始端口

```bash
python main.py -i shadowsocks.json -o config.json -p 20001
```

#### 更新 Docker Compose 文件

```bash
python main.py -i shadowsocks.json -o config.json -d my-docker-compose.yaml
```

### 使用 Docker 运行 V2Ray

生成配置文件后，您可以使用 Docker 运行 V2Ray：

```bash
docker-compose up -d
```

这将使用生成的配置文件启动一个 V2Ray 容器，暴露 SOCKS5 代理端口。

## 配置格式

### 输入（Shadowsocks）

输入文件应该是一个 Shadowsocks 订阅文件，通常是服务器配置的 JSON 数组：

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

### 输出（V2Ray）

生成的 V2Ray 配置包括：

- 不同本地端口上的多个入站 SOCKS5 服务器
- 到所选服务器的多个出站 Shadowsocks 连接
- 将每个入站端口连接到其对应出站服务器的路由规则

这种多入站/多出站配置允许您通过不同的本地端口同时使用不同的代理服务器。例如，您可以配置不同的应用程序使用不同的代理端口。

## 工作原理

1. 脚本读取 Shadowsocks 订阅文件
2. 它过滤掉信息节点（那些备注中包含"最新网址"、"剩余流量"、"过期时间"的节点）
3. 它动态地提取并按区域分组节点，分析节点名称中的模式，而不依赖于硬编码的区域列表
4. 从每个区域，它选择代表性节点：
   - 节点按名称是否以区域名称开头进行排序，优先选择以区域名称开头的节点
   - 通常选择每个区域的第一个和最后一个节点
   - 如果一个区域只有一个节点，该节点仍然会被包含
5. 对于每个选定的节点，它创建：
   - 本地端口上的 SOCKS5 入站连接
   - 到服务器的 Shadowsocks 出站连接
   - 连接入站和出站的路由规则
6. 配置保存到指定的输出文件
7. 如果使用追加模式，工具会将新节点添加到现有配置文件中
8. 如果指定了 Docker Compose 文件，端口映射会自动更新
9. 然后可以使用此配置运行 V2Ray 服务

## Docker 部署

包含的 `docker-compose.yaml` 文件配置了一个 V2Ray 容器，该容器：

- 使用官方 V2Ray 镜像（v2fly/v2fly-core）
- 将本地端口映射到容器（根据生成的配置自动更新）
- 挂载生成的配置文件到容器中
- 如果崩溃，自动重启

当您使用 `-d` 选项时，脚本将自动更新 Docker Compose 文件中的端口映射，以匹配生成配置中使用的端口。

## 高级用法

### 为不同应用程序使用不同代理服务器

由于该工具在不同端口上创建多个 SOCKS5 代理，您可以为不同的应用程序配置不同的代理服务器：

1. 网页浏览器：配置使用 socks5://127.0.0.1:10001（香港服务器）
2. 下载管理器：配置使用 socks5://127.0.0.1:10002（日本服务器）
3. 其他应用程序：根据需要配置使用其他端口

这允许您根据每个应用程序的特定需求优化连接。

### 自定义节点选择

默认情况下，该工具会选择每个区域的第一个和最后一个节点。如果您想修改此行为，可以编辑脚本中的 `select_nodes_from_regions` 函数。

## 故障排除

### 常见问题

1. **端口冲突**：如果您看到关于端口已被使用的错误，请使用 `-p` 选项指定不同的起始端口。

2. **Docker 问题**：确保 Docker 和 Docker Compose 已正确安装，并且您有权限运行 Docker 命令。

3. **JSON 解析错误**：确保您的 Shadowsocks 订阅文件是有效的 JSON。您可以使用在线 JSON 验证器进行检查。

## 贡献

欢迎贡献！以下是您可以贡献的方式：

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature-name`
3. 提交您的更改：`git commit -am 'Add some feature'`
4. 推送到分支：`git push origin feature-name`
5. 提交拉取请求

## 许可证

[MIT 许可证](LICENSE)
