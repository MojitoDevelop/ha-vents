"""Vents A21 protocol and integration constants."""

from homeassistant.const import Platform

DOMAIN = "vents_a21"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.FAN,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
CONF_UNIT_ID = "unit_id"
CONF_POLL_INTERVAL = "poll_interval"
CONF_CONNECT_DELAY = "connect_delay"
CONF_OPTIONAL_SENSORS = "optional_sensors"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_TIMEOUT = 5
DEFAULT_POLL_INTERVAL = 10
DEFAULT_CONNECT_DELAY = 2
OPTIONAL_SENSORS = (
    "humidity",
    "co2",
    "pm25",
    "voc",
    "airflow",
    "pressure",
    "rpm",
    "extra_temperature",
)
