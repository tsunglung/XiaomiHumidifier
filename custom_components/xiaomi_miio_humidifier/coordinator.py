"""Shared polling for the Xiaomi Smart Humidifier/Dehumidifier component.

One DataUpdateCoordinator per device: a single status request per interval,
read by all entities. Commands and status requests are serialized with a
lock so they never hit the device at the same time.
"""
import asyncio
import logging
from datetime import timedelta
from functools import partial

from miio import DeviceException

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


def command_ok(result) -> bool:
    """Return True if a miio/MIoT command result reports success."""
    if result == ["ok"]:
        return True
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return all(item.get("code", -1) == 0 for item in result)
    if isinstance(result, dict):
        return result.get("code", -1) == 0
    return False


class XiaomiHumidifierCoordinator(DataUpdateCoordinator):
    """Fetch the device status once per interval for all entities."""

    def __init__(self, hass: HomeAssistant, entry, device, name, model, unique_id, mac):
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {name}",
            update_interval=UPDATE_INTERVAL,
        )
        self.device = device
        self.device_name = name
        self.model = model
        self.unique_id = unique_id
        self.mac = mac
        self.info = None
        self._lock = asyncio.Lock()

    async def async_run(self, func, *args, **kwargs):
        """Run a blocking device call in the executor, one at a time."""
        async with self._lock:
            return await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

    async def async_fetch_info(self) -> None:
        """Read firmware/hardware info once (used for device_info)."""
        try:
            self.info = await self.async_run(self.device.info)
        except DeviceException as ex:
            _LOGGER.debug("Could not read device info: %s", ex)
            self.info = None

    async def _async_update_data(self):
        try:
            return await self.async_run(self.device.status)
        except DeviceException as ex:
            raise UpdateFailed(f"Error communicating with device: {ex}") from ex

    async def async_command(self, func, *args, optimistic=None, **kwargs) -> bool:
        """Send a command; on success apply optimistic values right away.

        optimistic: dict of status keys -> values to show immediately, as the
        device reports a changed property only after a short delay.
        """
        try:
            result = await self.async_run(func, *args, **kwargs)
        except DeviceException as ex:
            _LOGGER.error("Command %s failed: %s", getattr(func, "__name__", func), ex)
            return False

        _LOGGER.debug("Response received from humidifier: %s", result)
        if not command_ok(result):
            _LOGGER.error(
                "Command %s rejected by device: %s",
                getattr(func, "__name__", func), result,
            )
            return False

        if optimistic and self.data is not None:
            self.data.data.update(optimistic)
            self.async_update_listeners()
        return True


class XiaomiHumidifierEntity(CoordinatorEntity):
    """Common base for all entities of one device."""

    def __init__(self, coordinator: XiaomiHumidifierCoordinator) -> None:
        super().__init__(coordinator)
        self._coordinator = coordinator

    @property
    def status(self):
        """Return the latest status object (or None)."""
        return self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        coord = self._coordinator
        info = {
            "identifiers": {(DOMAIN, coord.unique_id)},
            "manufacturer": (coord.model or "Xiaomi").split(".", 1)[0].capitalize(),
            "name": coord.device_name,
            "model": coord.model,
        }
        if coord.info is not None:
            info["sw_version"] = coord.info.firmware_version
            info["hw_version"] = coord.info.hardware_version
        if coord.mac is not None:
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, coord.mac)}
        return info
