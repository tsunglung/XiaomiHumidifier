"""Support for Xiaomi Smart Humidifier/Dehumidifier sensors."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .humidifier_miot import SystemStatus
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_SENSORS,
    HUMIDIFIER_SENSORS_DELAY,
    MODELS_DELAY,
    MODELS_MIOT,
    XiaomiHumidifierSensorDescription
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier sensors."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_MIOT:
        return

    descriptions = HUMIDIFIER_SENSORS
    if model in MODELS_DELAY:
        descriptions = descriptions + HUMIDIFIER_SENSORS_DELAY

    async_add_entities(
        XiaomiHumidifierSensor(coordinator, description)
        for description in descriptions
    )


class XiaomiHumidifierSensor(XiaomiHumidifierEntity, SensorEntity):
    """A sensor of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: XiaomiHumidifierSensorDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.status is None:
            return None
        value = getattr(self.status, self.entity_description.key, None)
        if self.entity_description.key == "system_status":
            # the status property already maps the fault code to an enum
            return value.name if value is not None else None
        return value
