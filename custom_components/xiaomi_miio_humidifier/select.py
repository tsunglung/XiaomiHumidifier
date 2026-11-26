"""Support for Xiaomi Smart Humidifier/Dehumidifier select entities."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .humidifier_miot import LightMode
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_SELECTS,
    MODELS_MIOT,
)

_LOGGER = logging.getLogger(__name__)

# select key -> (status property, MIoT mapping key, enum)
SELECT_TARGETS = {
    "display_brightness": ("display_brightness", "light_mode", LightMode),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier select entities."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_MIOT:
        return

    async_add_entities(
        XiaomiHumidifierSelect(coordinator, description)
        for description in HUMIDIFIER_SELECTS
        if SELECT_TARGETS[description.key][1] in coordinator.device.mapping
    )


class XiaomiHumidifierSelect(XiaomiHumidifierEntity, SelectEntity):
    """A select entity of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: SelectEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._status_key, self._miot_key, self._enum = SELECT_TARGETS[description.key]
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def current_option(self):
        """Return the selected option."""
        if self.status is None:
            return None
        return getattr(self.status, self._status_key, None)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = self._enum[option].value
        await self._coordinator.async_command(
            self._coordinator.device.set_value, self._miot_key, value,
            optimistic={self._miot_key: value},
        )
