"""Switch to control option of Anthem Av receiver."""
from typing import Any

from anthemav.connection import Connection
from anthemav.protocol import AVR

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AnthemAVEntity
from .const import CONF_MODEL, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Anthem Room Correction switch based on a config entry."""

    name = config_entry.data[CONF_NAME]
    mac_address = config_entry.data[CONF_MAC]
    model = config_entry.data[CONF_MODEL]

    avr_connection: Connection = hass.data[DOMAIN][config_entry.entry_id]

    avr: AVR = avr_connection.protocol

    if avr.support_arc:
        async_add_entities(
            [AnthemARCSwitch(avr, name, mac_address, model, config_entry.entry_id)]
        )


class AnthemARCSwitch(AnthemAVEntity, SwitchEntity):
    """Defines Anthem room correction switch."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "ARC"

    def __init__(
        self, avr: AVR, name: str, mac_address: str, model: str, entry_id: str
    ) -> None:
        """Initialize Anthem Room Correction switch."""
        super().__init__(avr, name, mac_address, model, entry_id)
        self.avr = avr
        self._entry_id = entry_id
        self._attr_unique_id = f"{mac_address}_ARC"
        self.set_states()

    def set_states(self) -> None:
        """Update state of the switch."""
        self._attr_is_on = bool(self.avr.arc)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Anthem room correction."""
        self.avr.arc = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Anthem room correction."""
        self.avr.arc = True
