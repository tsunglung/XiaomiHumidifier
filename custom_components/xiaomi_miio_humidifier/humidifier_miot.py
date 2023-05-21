"""
Support for Xiaomi Smart Humidifier/Dehumidifier

"""
import enum
from typing import Any, Dict
import logging
import click

from miio.click_common import command, format_output
from miio.device import DeviceStatus
from miio.miot_device import MiotDevice
from .const import (
    MODEL_DMAKER_DERH_22HT,
    MODEL_DMAKER_DERH_22L
)

_LOGGER = logging.getLogger(__name__)


MIOT_MAPPING = {
    MODEL_DMAKER_DERH_22HT: {
        "status": {"siid": 2, "piid": 1},  # read, notify, write
        "device_fault": {"siid": 2, "piid": 2},  # read, notify
        "mode": {"siid": 2, "piid": 3},  # read, notify, write
        "target_humidity": {"siid": 2, "piid": 5},  # read, notify, write
        "relative_humidity": {"siid": 3, "piid": 1},  # read, notify
        "temperature": {"siid": 3, "piid": 2},  # read, notify
        "alarm": {"siid": 4, "piid": 1},  # read, notify, write
        "indicator_light": {"siid": 5, "piid": 1},  # read, notify, write
        "light_mode": {"siid": 5, "piid": 2},  # read, notify, write
        "physical_controls_locked": {"siid": 6, "piid": 1},  # read, notify, write
        "off_delay_time": {"siid": 7, "piid": 1},  # read, notify, write
        "dry_after_off": {"siid": 7, "piid": 2},  # read, notify, write
        "dry_left_time": {"siid": 7, "piid": 3},  # read, notify
        "is_warming_up": {"siid": 7, "piid": 4},  # read, notify
        "toggle": {"siid": 7, "aiid": 1},
        "loop-mode": {"siid": 7, "aiid": 2},
        "reset-filter": {"siid": 7, "aiid": 3},
    },
    MODEL_DMAKER_DERH_22L: {
        "status": {"siid": 2, "piid": 1},  # read, notify, write
        "device_fault": {"siid": 2, "piid": 2},  # read, notify
        "mode": {"siid": 2, "piid": 3},  # read, notify, write
        "target_humidity": {"siid": 2, "piid": 5},  # read, notify, write
        "relative_humidity": {"siid": 3, "piid": 1},  # read, notify
        "temperature": {"siid": 3, "piid": 2},  # read, notify
        "alarm": {"siid": 4, "piid": 1},  # read, notify, write
        "indicator_light": {"siid": 5, "piid": 1},  # read, notify, write
        "light_mode": {"siid": 5, "piid": 2},  # read, notify, write
        "physical_controls_locked": {"siid": 6, "piid": 1},  # read, notify, write
        "off_delay_time": {"siid": 7, "piid": 1},  # read, notify, write
        "dry_after_off": {"siid": 7, "piid": 2},  # read, notify, write
        "dry_left_time": {"siid": 7, "piid": 3},  # read, notify
        "is_warming_up": {"siid": 7, "piid": 4},  # read, notify
        "toggle": {"siid": 7, "aiid": 1},
        "loop-mode": {"siid": 7, "aiid": 2},
        "reset-filter": {"siid": 7, "aiid": 3},
    }
}


class DeviceException(Exception):
    """Exception wrapping any communication errors with the device."""


class Status(enum.Enum):
    """ Status """
    Unknown = -1
    Off = 0
    On = 1


class SystemStatus(enum.Enum):
    """ System Status """
    Unknown = -1
    No_Fault = 0
    Water_Full = 1
    Sensor_Fault1 = 2
    Sensor_Fault2 = 3
    Communication_Fault1 = 4
    Filter_Clean = 5
    Defrost = 6
    Fan_Motor = 7
    Overload = 8
    Lack_Of_Refrigerant = 9
    Out_Of_Temperature = 10


class PowerMode_V1(enum.Enum):
    """ Power Mode """
    Smart = 0
    Sleep = 1
    Clothes_Drying = 2


class HumidifierStatusMiot(DeviceStatus):
    """Container for status reports for Xiaomi Smart Humidifier/Dehumidifie."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        {
            'id': 1,
            'result': [
                {'did': 'status', 'siid': 2, 'piid': 1, 'code': 0, 'value': 0},
                {'did': 'mode', 'siid': 2, 'piid': 2, 'code': 0, 'value': 0},
                {'did': 'temperature', 'siid': 3, 'piid': 2, 'code': 0, 'value': 0}
            ],
            'exe_time': 280
        }
        """
        self.data = data

    @property
    def is_on(self) -> bool:
        """True if device is currently on."""
        return self.data["status"]

    @property
    def mode(self) -> str:
        """Mode."""
        return PowerMode_V1(self.data.get("mode")).name

    @property
    def status(self) -> int:
        """Operation status."""
        try:
            return Status(self.data["status"])
        except ValueError:
            _LOGGER.error("Unknown Status (%s)", self.data["status"])
            return Status.Unknown

    @property
    def temperature(self) -> int:
        """Temperature"""
        return self.data["temperature"]

    @property
    def relative_humidity(self) -> int:
        """Relative Humidity"""
        return self.data["relative_humidity"]

    @property
    def target_humidity(self) -> int:
        """Target Humidity"""
        return self.data["target_humidity"]

    @property
    def indicator_light(self) -> int:
        """LED"""
        return self.data["indicator_light"]

    @property
    def alarm(self) -> int:
        """Buzzer"""
        return self.data["alarm"]

    @property
    def dry_after_off(self) -> int:
        """Dry after off"""
        return self.data["dry_after_off"]

    @property
    def light_mode(self) -> int:
        """LED"""
        return self.data["light_mode"]

    @property
    def physical_controls_locked(self) -> int:
        """Children lock"""
        return self.data["physical_controls_locked"]

    @property
    def system_status(self) -> int:
        """System status."""
        try:
            return SystemStatus(self.data["device_fault"])
        except ValueError:
            _LOGGER.error("Unknown System Status (%s)", self.data["device_fault"])
            return SystemStatus.Unknown

    @property
    def dry_left_time(self) -> int:
        """Dry Left Time"""
        return self.data["dry_left_time"]

    @property
    def is_warming_up(self) -> bool:
        """Is Warming Up"""
        return self.data["is_warming_up"]


class HumidifierMiot(MiotDevice):
    """Interface for Smart Humidifier/Dehumidifie Miot"""
    mapping = MIOT_MAPPING[MODEL_DMAKER_DERH_22HT]

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_DMAKER_DERH_22HT,
    ) -> None:
        if model not in MIOT_MAPPING:
            raise DeviceException("Invalid HumidifierMiot model: %s" % model)

        super().__init__(ip, token, start_id, debug, lazy_discover)
        self._model = model

    @command(
        default_output=format_output(
            "",
            "Status: {result.status.name}\n"
        )
    )
    def status(self) -> HumidifierStatusMiot:
        """Retrieve properties."""
        return HumidifierStatusMiot(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    @command(
        click.argument("mode", type=int),
        default_output=format_output("Setting mode {mode}"),
    )
    def set_power_mode(self, mode: int):
        """Set mode."""
        return self.set_property("mode", mode)

    @command(
        click.argument("humidity", type=int),
        default_output=format_output("Setting Humidity {humidity}"),
    )
    def set_humidity(self, humidity: int):
        """Set Humidity."""
        return self.set_property("target_humidity", humidity)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting Wifi LED {mode}"),
    )
    def set_wifi_led(self, mode: bool):
        """Set Wifi LED."""

        return self.set_property("indicator_light", mode)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting Buzzer {mode}"),
    )
    def set_buzzer(self, mode: bool):
        """Set Buzzer."""

        return self.set_property("alarm", mode)

    @command(
        click.argument("switch", type=str),
        default_output=format_output("Setting Switch {switch}"),
    )
    def set_switch_on(self, switch: str):
        """Set Switch."""

        return self.set_property(switch, True)

    @command(
        click.argument("switch", type=str),
        default_output=format_output("Setting Switch {switch}"),
    )
    def set_switch_off(self, switch: str):
        """Set Switch."""

        return self.set_property(switch, False)

    def on(self):
        """ Turn on """
        return self.set_property("status", True)

    def off(self):
        """ Turn off """
        return self.set_property("status", False)
