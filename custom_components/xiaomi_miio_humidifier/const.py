"""Constants of the Xiaomi Smart Humidifier/Dehumidifier component."""
from datetime import timedelta
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass
)

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntityDescription,
)

from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    TIME_SECONDS
)

DEFAULT_NAME = "Xiaomi Smart Humidifier/Dehumidifier"
DOMAIN = "xiaomi_miio_humidifier"
DOMAINS = ["humidifier", "sensor", "switch", "button"]
DATA_KEY = "xiaomi_humidifier_data"
DATA_STATE = "state"
DATA_DEVICE = "device"

CONF_MODEL = "model"
CONF_MAC = "mac"

MODEL_DMAKER_DERH_22HT = "dmaker.derh.22ht"
MODEL_DMAKER_DERH_22L = "dmaker.derh.22l"
MODEL_DMAKER_DERH_50L = "dmaker.derh.50l"

OPT_MODEL = {
    MODEL_DMAKER_DERH_22HT: "Mi PowerStrip (Global)",
    MODEL_DMAKER_DERH_22L: "Mi PowerStrip (China)"
}


MODELS_MIOT = [
    MODEL_DMAKER_DERH_22HT,
    MODEL_DMAKER_DERH_22L,
    MODEL_DMAKER_DERH_50L
]

MODELS_ALL_DEVICES = MODELS_MIOT

DEFAULT_SCAN_INTERVAL = 30
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

ATTR_POWER = "power"
ATTR_TEMPERATURE = "temperature"
ATTR_LOAD_POWER = "load_power"
ATTR_MODEL = "model"
ATTR_POWER_MODE = "power_mode"
ATTR_WIFI_LED = "wifi_led"
ATTR_POWER_PRICE = "power_price"
ATTR_PRICE = "price"
ATTR_WORKING_TIME = "working_time"
ATTR_COUNT_DOWN_TIME = "count_down_time"
ATTR_COUNT_DOWN = "count_down"
ATTR_KEEP_RELAY = "keep_relay"

@dataclass
class XiaomiHumidifierSensorDescription(
    SensorEntityDescription
):
    """Class to describe an Xiaomi Smart Humidifier/Dehumidifier sensor."""


HUMIDIFIER_SENSORS: tuple[XiaomiHumidifierSensorDescription, ...] = (
    XiaomiHumidifierSensorDescription(
        key="system_status",
        name="System Status",
        icon="mdi:chip"
    ),
    XiaomiHumidifierSensorDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    XiaomiHumidifierSensorDescription(
        key="relative_humidity",
        name="Relative Humidity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent"
    ),
    XiaomiHumidifierSensorDescription(
        key="dry_left_time",
        name="Dry Left Time",
        native_unit_of_measurement=TIME_SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timelapse"
    ),
    XiaomiHumidifierSensorDescription(
        key="is_warming_up",
        name="Is Warming Up",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-wave"
    )
)

HUMIDIFIER_SWITCHS_V1: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="indicator_light",
        name="Indicator Light",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="physical_controls_locked",
        name="Physical Controls Lock",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="dry_after_off",
        name="Dry After Off",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="alarm",
        name="Indicator Buzzer",
        device_class=SwitchDeviceClass.SWITCH,
    )
)

HUMIDIFIER_BUTTONS_V1: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reset-filter",
        name="Reset Filter",
        device_class=ButtonDeviceClass.RESTART,
    ),
    ButtonEntityDescription(
        key="loop-mode",
        name="Loop Mode",
        device_class=ButtonDeviceClass.RESTART,
    )
)
