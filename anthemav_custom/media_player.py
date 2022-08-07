"""Support for Anthem Network Receivers and Processors."""
from __future__ import annotations

import logging

from anthemav.connection import Connection
from anthemav.protocol import AVR
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.components.repairs import IssueSeverity, async_create_issue
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import AnthemAVEntity
from .const import CONF_MODEL, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

VOLUME_STEP = 0.01

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up our socket to the AVR."""
    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        breaks_in_ha_version="2022.10.0",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )
    _LOGGER.warning(
        "Configuration of the Anthem A/V Receivers integration in YAML is "
        "deprecated and will be removed in Home Assistant 2022.10; Your "
        "existing configuration has been imported into the UI automatically "
        "and can be safely removed from your configuration.yaml file"
    )
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=config,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    name = config_entry.data[CONF_NAME]
    mac_address = config_entry.data[CONF_MAC]
    model = config_entry.data[CONF_MODEL]

    avr: Connection = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for zone_number in avr.protocol.zones:
        _LOGGER.debug("Initializing Zone %s", zone_number)
        entity = AnthemAVR(
            avr.protocol, name, mac_address, model, zone_number, config_entry.entry_id
        )
        entities.append(entity)

    _LOGGER.debug("Connection data dump: %s", avr.dump_conndata)

    async_add_entities(entities)


class AnthemAVR(AnthemAVEntity, MediaPlayerEntity):
    """Entity reading values from Anthem AVR protocol."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_icon = "mdi:audio-video"
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self,
        avr: AVR,
        name: str,
        mac_address: str,
        model: str,
        zone_number: int,
        entry_id: str,
    ) -> None:
        """Initialize entity with transport."""
        super().__init__(avr, name, mac_address, model, entry_id)
        self.avr = avr
        self._entry_id = entry_id
        self._zone_number = zone_number
        self._zone = avr.zones[zone_number]
        if zone_number > 1:
            self._attr_name = f"zone {zone_number}"
            self._attr_unique_id = f"{mac_address}_{zone_number}"
        else:
            self._attr_unique_id = mac_address

        self._support_sound_mode = zone_number == 1 and avr.support_audio_listening_mode

        if self._support_sound_mode:
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE

        self.set_states()

    def set_states(self) -> None:
        """Set all the states from the device to the entity."""
        self._attr_state = STATE_ON if self._zone.power is True else STATE_OFF
        self._attr_is_volume_muted = self._zone.mute
        self._attr_volume_level = self._zone.volume_as_percentage
        self._attr_media_title = self._zone.input_name
        self._attr_app_name = self._zone.input_format
        self._attr_source = self._zone.input_name
        self._attr_source_list = self.avr.input_list
        if self._support_sound_mode:
            if self.state is STATE_OFF:
                self._attr_sound_mode_list = None
            else:
                self._attr_sound_mode_list = self.avr.audio_listening_mode_list
                self._attr_sound_mode = self.avr.audio_listening_mode_text

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Switch the sound mode of the entity."""
        self.avr.audio_listening_mode_text = sound_mode

    async def async_select_source(self, source: str) -> None:
        """Change AVR to the designated source (by name)."""
        self._zone.input_name = source

    async def async_turn_off(self) -> None:
        """Turn AVR power off."""
        self._zone.power = False

    async def async_turn_on(self) -> None:
        """Turn AVR power on."""
        self._zone.power = True

    async def async_set_volume_level(self, volume: float) -> None:
        """Set AVR volume (0 to 1)."""
        self._zone.volume_as_percentage = volume

    async def async_volume_up(self) -> None:
        """Turn volume up for media player."""
        volume = self.volume_level
        if volume and volume < 1:
            await self.async_set_volume_level(min(1, volume + VOLUME_STEP))

    async def async_volume_down(self) -> None:
        """Turn volume down for media player."""
        volume = self.volume_level
        if volume and volume > 0:
            await self.async_set_volume_level(max(0, volume - VOLUME_STEP))

    async def async_mute_volume(self, mute: bool) -> None:
        """Engage AVR mute."""
        self._zone.mute = mute
