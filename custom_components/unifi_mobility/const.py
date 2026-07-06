"""Constants for the UniFi Mobility integration."""

DOMAIN = "unifi_mobility"
PLATFORMS = ["binary_sensor", "button", "sensor"]

ENTITY_KEYS = {
    "binary_sensor": (
        "connectivity",
        "sim_present",
        "pin_locked",
        "activated",
        "poe_passthrough",
    ),
    "button": ("refresh", "reconnect"),
    "sensor": (
        "firmware",
        "operator",
        "network_source",
        "lte_band",
        "rssi",
        "rsrp",
        "rsrq",
        "cpu",
        "memory",
        "data_usage",
        "uptime",
        "wan_ip",
        "lan_ip",
        "client_count",
        "signal_quality",
        "network_type",
        "iccid",
        "imei",
        "lte_model",
        "rx_channel",
        "tx_channel",
        "data_limit",
        "billing_cycle_day",
        "wan_ipv6",
        "data_remaining",
        "data_usage_percent",
        "days_until_billing",
    ),
}

CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SLOW_POLL_MULTIPLIER = "slow_poll_multiplier"
CONF_POLL_CLIENTS = "poll_clients"
DEFAULT_NAME = "UniFi Mobile Router"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SLOW_POLL_MULTIPLIER = 10
DEFAULT_POLL_CLIENTS = True

RPC_INFO_LOW = "InfoLowDump"
RPC_INFO_MEDIUM = "InfoMediumDump"
RPC_INFO_HIGH = "InfoHighDump"
RPC_INFO_CLIENT = "InfoClientDump"
RPC_DEVICE_INFO = "GetDeviceInfo"
RPC_DEVICE_STATUS = "GetDeviceStatus"
RPC_SHADOW = "ShadowReadLocal"

SHADOW_NETWORKS = "networks"
SHADOW_POWERS = "powers"
