# UniFi Mobility for Home Assistant

[中文](#中文说明) · [English](#english)

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=xiaxiaxiamagic&repository=unifi-mobility-ha&category=integration)

## 中文说明

这是一个面向 Ubiquiti UniFi 移动路由器的 Home Assistant 本地集成，支持 UMR、UMR-Industrial 及兼容型号。

集成直接连接设备的 **UMR 本地门户 JSON-RPC API**，无需 Mobility Cloud 订阅，路由器状态数据不会离开本地网络。

> 本项目是独立的社区项目，与 Ubiquiti Inc. 无隶属关系，也未获得其官方认可。

### 主要功能

- 本地轮询，并自动续期登录会话
- 本地门户密码变更后支持 Home Assistant 重新认证
- 快速与慢速分组轮询，降低路由器负载
- 提供立即刷新与重新连接本地会话的安全诊断按钮
- 提供剩余流量、流量使用率及距离结算日传感器
- 中文和英文配置界面
- Home Assistant 2026.3+ 本地图标资源
- 诊断信息自动隐藏凭据和设备标识符
- 符合 HACS 自定义仓库结构

### 可用实体

- 连接状态、激活状态、SIM 卡及 PIN 锁定状态
- 运营商、网络来源、LTE 频段和蜂窝网络类型
- RSSI、RSRP、RSRQ、信号质量、RX/TX 信道
- 固件版本、CPU、内存、运行时间
- WAN/LAN IPv4、WAN IPv6、已连接客户端数量
- LTE 调制解调器型号和 PoE 直通状态
- 当前流量、流量限额和计费周期

IMEI 和 ICCID 属于敏感标识符，因此对应实体默认禁用，可在实体设置中手动启用。

### 使用要求

- 推荐 Home Assistant 2026.3 或更高版本
- Home Assistant 能够访问受支持的 UniFi 移动路由器
- 路由器本地门户密码
- 稳定版本的 UMR 固件；已在 UMR-Industrial-EU `1.17.11` 上测试

### 兼容性矩阵

| 型号 | 固件 | 状态 | 验证方式 |
|---|---|---|---|
| UMR-Industrial-EU | `1.17.11` | 已验证 | 真实设备及匿名响应样本 |
| UMR | 待补充 | 预期兼容 | 共用本地门户 API |

不同固件可能缺少部分可选 JSON-RPC 方法。欢迎按贡献指南提交脱敏后的固件响应样本，以便持续扩充自动兼容测试。

### 安装

#### 通过 HACS 安装

1. 打开 HACS。
2. 添加自定义仓库 `https://github.com/xiaxiaxiamagic/unifi-mobility-ha`，类别选择 **Integration（集成）**。
3. 安装 **UniFi Mobility**。
4. 重启 Home Assistant。
5. 前往 **设置 → 设备与服务 → 添加集成**，搜索 **UniFi Mobility**。

#### 手动安装

1. 将 `custom_components/unifi_mobility` 复制到 Home Assistant 的 `/config/custom_components/` 目录。
2. 重启 Home Assistant。
3. 前往 **设置 → 设备与服务 → 添加集成**。
4. 搜索并添加 **UniFi Mobility**。

### 配置示例

| 字段 | 示例 | 说明 |
|---|---|---|
| 主机地址 | `192.168.105.1` | 可不填写协议，默认使用 HTTPS |
| 密码 | 本地门户密码 | 本地用户名固定为 `ui` |
| 验证 SSL | 关闭 | UMR 通常使用自签名证书 |

安装后可在集成的 **配置** 页面修改主机地址、密码、SSL 验证、轮询间隔及客户端列表轮询。默认每 30 秒更新实时信号与状态，每 5 分钟更新静态信息和客户端列表。

### 信号质量标准

| RSRP | 评价 |
|---|---|
| 高于 −80 dBm | 极佳 |
| −80 至 −90 dBm | 良好 |
| −90 至 −100 dBm | 一般 |
| 低于 −100 dBm | 较差 |

### 隐私与安全

- Home Assistant 与路由器之间仅进行本地通信。
- 集成只调用只读状态接口，不修改路由器配置。
- 密码保存在 Home Assistant 的配置条目存储中。
- 诊断信息会隐藏密码、会话令牌、IP/MAC 地址、IMEI、ICCID、SSID 和客户端标识符。
- 不包含分析统计或外部遥测。

### 常见问题

- **无法连接：** 确认 Home Assistant 能访问 UMR 地址，并在浏览器中验证本地门户密码。除非设备安装了可信证书，否则请关闭 SSL 验证。
- **实体不可用：** 不同固件提供的 JSON-RPC 方法略有区别；不支持的可选数据会保持不可用，不影响其他实体。
- **密码已更改：** Home Assistant 会启动重新认证流程，输入新密码即可，无需删除集成。

## English

A local Home Assistant integration for Ubiquiti UniFi Mobile Router devices, including UMR, UMR-Industrial, and compatible UMR variants.

It communicates directly with the **UMR Local Portal JSON-RPC API**. No Mobility Cloud subscription is required, and router telemetry stays on your local network.

> This is an independent community project and is not affiliated with or endorsed by Ubiquiti Inc.

## Features

- Local polling with automatic session renewal
- Home Assistant reauthentication when the local portal password changes
- Separate fast and slow polling to reduce router load
- Chinese and English user interfaces
- Local brand assets for Home Assistant 2026.3+
- Redacted diagnostics with credentials and device identifiers removed
- Safe diagnostic buttons for immediate refresh and local-session reconnection
- Data remaining, usage percentage, and billing-cycle countdown sensors
- HACS-compatible repository structure

## Available entities

### Connectivity and cellular

- Internet connectivity
- Activation state
- SIM presence and PIN lock state
- Operator, network source, LTE band, and cellular network type
- RSSI, RSRP, RSRQ, and calculated signal quality
- RX and TX channels

### Device and network

- Firmware version
- CPU and memory utilization
- Uptime
- WAN/LAN IPv4 and WAN IPv6
- Connected client count
- LTE modem model
- PoE passthrough state

### Data plan

- Current data usage
- Configured data limit
- Billing-cycle value

IMEI and ICCID entities are disabled by default because they are sensitive identifiers.

## Requirements

- Home Assistant 2026.3 or newer is recommended
- A supported UniFi Mobile Router reachable from Home Assistant
- The password used by the router's local portal
- Stable UMR firmware; tested with UMR-Industrial-EU firmware `1.17.11`

## Installation

### HACS

1. Open HACS.
2. Add this repository as a custom repository with category **Integration**.
3. Install **UniFi Mobility**.
4. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/unifi_mobility` into Home Assistant's `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **UniFi Mobility**.

## Configuration

For a typical UMR installation:

| Field | Example | Notes |
|---|---|---|
| Host | `192.168.105.1` | Scheme is optional; HTTPS is used by default |
| Password | Local portal password | The local username is fixed to `ui` |
| Verify SSL | Off | UMR devices normally use a self-signed certificate |

After setup, open the integration's **Configure** dialog to change:

- Host address and password
- SSL certificate verification
- Fast polling interval (15–300 seconds)
- Slow polling multiplier
- Client-list polling

The default schedule polls live signal and status every 30 seconds, while static information and the client list are refreshed every 5 minutes.

## Signal quality

Signal quality is calculated primarily from RSRP:

| RSRP | Rating |
|---|---|
| Above −80 dBm | Excellent |
| −80 to −90 dBm | Good |
| −90 to −100 dBm | Fair |
| Below −100 dBm | Poor |

## Privacy and security

- Communication is local between Home Assistant and the router.
- The integration performs read-only status calls.
- Passwords are stored in Home Assistant's config-entry storage.
- Diagnostics redact passwords, session tokens, addresses, MAC addresses, IMEI, ICCID, SSIDs, and client identifiers.
- No analytics or external telemetry is included.

## Compatibility matrix

| Model | Firmware | Status | Validation |
|---|---|---|---|
| UMR-Industrial-EU | `1.17.11` | Verified | Real device and anonymized response fixture |
| UMR | To be confirmed | Expected compatible | Shared local portal API |

Firmware variants may omit optional JSON-RPC methods. Anonymized response samples are welcome; see the contribution guide.

## Troubleshooting

### Cannot connect

- Confirm Home Assistant can reach the UMR address.
- Open the local portal in a browser and verify the password.
- Keep SSL verification disabled unless the router has a trusted certificate.

### Entities are unavailable

UMR firmware versions expose slightly different JSON-RPC methods. Unsupported optional sections are kept unavailable without breaking the whole integration.

### Password changed

Home Assistant will create a repair/reauthentication flow. Enter the new local portal password without deleting the integration.

### Upgrading to v0.4.0

The integration migrates only legacy entity IDs that match its old automatic numbered naming pattern. Manually renamed entity IDs are left unchanged. Entity registry entries, history, and automation references are preserved by Home Assistant's registry migration.

## Development

```bash
uvx ruff format custom_components tests
uvx ruff check custom_components tests
python3 -m compileall -q custom_components/unifi_mobility
```

The repository includes GitHub Actions workflows for Ruff, Hassfest, and HACS validation.

## License

MIT. Ubiquiti, UniFi, and related marks are trademarks of Ubiquiti Inc.
