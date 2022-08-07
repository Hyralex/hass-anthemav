"""The Anthem A/V Receivers integration."""
from __future__ import annotations

from abc import abstractmethod
import logging

import anthemav
from anthemav.device_error import DeviceError
from anthemav.protocol import AVR

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import ANTHEMAV_UDATE_SIGNAL, DEVICE_TIMEOUT_SECONDS, DOMAIN, MANUFACTURER

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Anthem A/V Receivers from a config entry."""

    @callback
    def async_anthemav_update_callback(message: str) -> None:
        """Receive notification from transport that new data exists."""
        _LOGGER.debug("Received update callback from AVR: %s", message)
        async_dispatcher_send(hass, f"{ANTHEMAV_UDATE_SIGNAL}_{entry.entry_id}")

    try:
        avr = await anthemav.Connection.create(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            update_callback=async_anthemav_update_callback,
        )

        # Wait for the zones to be initialised based on the model
        await avr.protocol.wait_for_device_initialised(DEVICE_TIMEOUT_SECONDS)
    except (OSError, DeviceError) as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = avr

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    @callback
    def close_avr(event: Event) -> None:
        avr.close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_avr)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    avr = hass.data[DOMAIN][entry.entry_id]

    if avr is not None:
        _LOGGER.debug("Close avr connection")
        avr.close()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class AnthemAVEntity(Entity):
    """Base AnthemAV entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, avr: AVR, name: str, mac_address: str, model: str, entry_id: str
    ) -> None:
        """Initialize base AnthemAV entity."""
        self.avr = avr
        self._entry_id = entry_id
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=name,
            manufacturer=MANUFACTURER,
            model=model,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{ANTHEMAV_UDATE_SIGNAL}_{self._entry_id}",
                self.update_states,
            )
        )

    @callback
    def update_states(self) -> None:
        """Update states for the entity."""
        self.set_states()
        self.async_write_ha_state()

    @abstractmethod
    def set_states(self) -> None:
        """Set current state of the entity."""
