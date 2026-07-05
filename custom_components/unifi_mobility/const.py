"""Constants for the UniFi Mobility integration."""

DOMAIN = "unifi_mobility"
PLATFORMS = ["binary_sensor", "sensor"]

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
