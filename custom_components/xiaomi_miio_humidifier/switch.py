"""Support for Xiaomi Smart Humidifier/Dehumidifier switches."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_SWITCHS_V1,
    HUMIDIFIER_SWITCHS_DELAY,
    MODELS_DELAY,
    MODELS_MIOT
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier switches."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_MIOT:
        return

    descriptions = HUMIDIFIER_SWITCHS_V1
    if model in MODELS_DELAY:
        descriptions = descriptions + HUMIDIFIER_SWITCHS_DELAY

    async_add_entities(
        XiaomiHumidifierSwitch(coordinator, description)
        for description in descriptions
    )


class XiaomiHumidifierSwitch(XiaomiHumidifierEntity, SwitchEntity):
    """A switch of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: SwitchEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._key = description.key
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def is_on(self):
        """Return the state of the switch."""
        if self.status is None:
            return None
        value = getattr(self.status, self._key, None)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._coordinator.async_command(
            self._coordinator.device.set_switch_on, self._key,
            optimistic={self._key: True},
        )

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._coordinator.async_command(
            self._coordinator.device.set_switch_off, self._key,
            optimistic={self._key: False},
        )
