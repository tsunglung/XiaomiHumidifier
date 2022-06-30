"""Support for Xiaomi Smart Humidifier/Dehumidifier service."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN
)
from miio import DeviceException

from .humidifier_miot import SystemStatus
from .const import (
    CONF_MODEL,
    DATA_KEY,
    DOMAIN,
    HUMIDIFIER_SENSORS,
    MODELS_MIOT,
    XiaomiHumidifierSensorDescription
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier sensor."""

    host = entry.options[CONF_HOST]
    model = entry.options[CONF_MODEL]
    name = entry.title
    unique_id = entry.unique_id

    humidifier = hass.data[DOMAIN][host]

    try:
        entities = []

        for description in HUMIDIFIER_SENSORS:
            if model in MODELS_MIOT:
                entities.extend(
                    [XiaomiHumidifierSensor(entry.options, description, name, unique_id, humidifier)]
                )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

class XiaomiHumidifierSensor(SensorEntity):
    """Implementation of a Xiaomi Smart Humidifier/Dehumidifier sensor."""
    entity_description: XiaomiHumidifierSensorDescription

    def __init__(self, entry_data, description, name, unique_id, humidifier):
        self.entity_description = description
        self._entry_data = entry_data
        self._name = name
        self._model = entry_data[CONF_MODEL]
        self._unique_id = unique_id
        self._attr = description.key
        self._mac = entry_data[CONF_TOKEN]
        self._host = entry_data[CONF_HOST]
        self._humidifier = humidifier
        self._available = True
        self._skip_update = False
        self._state = None
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(self._name, self.entity_description.name)

    @property
    def unique_id(self):
        """Return the unique of the sensor."""
        return "{}_{}".format(self._name, self.entity_description.key)

    def friendly_name(self):
        """Return the friendly name of the sensor."""
        return "{}".format(self.entity_description.name)

    @property
    def device_info(self):
        """Return the device info."""
        info = self._humidifier.info()
        device_info = {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": (self._model or "Xiaomi").split(".", 1)[0].capitalize(),
            "name": self._name,
            "model": self._model,
            "sw_version": info.firmware_version,
            "hw_version": info.hardware_version
        }

        if self._mac is not None:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        return device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            if getattr(self.hass.data[DATA_KEY][self._host], "status", None):
                state = self.hass.data[DATA_KEY][self._host].status
            else:
                state = await self.hass.async_add_executor_job(self._humidifier.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = getattr(state, self._attr, None)
            if self.entity_description.key == "system_status":
                self._state = SystemStatus(self._state).name

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

