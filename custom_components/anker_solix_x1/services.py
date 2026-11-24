"""Actions for generating a dashboard for an installed X1."""

from __future__ import annotations

import voluptuous as vol
import yaml

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN


def async_setup_services(hass: HomeAssistant) -> None:
    """Register actions for the integration."""

    async def generate_dashboard(call: ServiceCall) -> ServiceResponse:
        # Filter by state instead of async_loaded_entries(), which is not
        # available in every supported Home Assistant version.
        requested_id = call.data.get("config_entry_id")
        entries = [
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
            and (requested_id is None or entry.entry_id == requested_id)
        ]
        if len(entries) != 1:
            raise HomeAssistantError("Wähle genau eine geladene Anker Solix X1-Anlage aus.")

        entry = entries[0]
        prefix = f"{entry.entry_id}_"
        registry = er.async_get(hass)
        entities = {
            entity.unique_id.removeprefix(prefix): entity.entity_id
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
            if entity.domain == "sensor"
            and entity.unique_id.startswith(prefix)
            and not entity.disabled
        }

        def tiles(definitions: list[tuple[str, str, str]]) -> list[dict]:
            return [
                {"type": "tile", "entity": entities[key], "name": label, "icon": icon}
                for key, label, icon in definitions
                if key in entities
            ]

        groups = [
            ("Energie live", "mdi:flash", tiles([
                ("pv_power", "Solarleistung", "mdi:solar-power"),
                ("load_power", "Hausverbrauch", "mdi:home-lightning-bolt"),
                ("grid_power", "Netzleistung", "mdi:transmission-tower"),
                ("battery_power_pcs", "Akkuleistung", "mdi:battery-charging"),
            ])),
            ("Batterie", "mdi:battery", tiles([
                ("akku_soc", "Ladezustand", "mdi:battery"),
                ("akku_soh", "Akkugesundheit", "mdi:battery-heart-variant"),
                ("akku_rated_capacity", "Nennkapazität", "mdi:battery-high"),
                ("inverter_temperature", "Wechselrichter", "mdi:thermometer"),
            ])),
            ("Heute", "mdi:calendar-today", tiles([
                ("daily_pv_generation", "Solarerzeugung", "mdi:white-balance-sunny"),
                ("daily_load_consumption_energy", "Hausverbrauch", "mdi:home-lightning-bolt"),
                ("daily_purchased_energy", "Netzbezug", "mdi:transmission-tower-import"),
                ("daily_feed_in_energy", "Einspeisung", "mdi:transmission-tower-export"),
                ("akku_daily_charge_energy", "Akku geladen", "mdi:battery-arrow-up"),
                ("akku_daily_discharge_energy", "Akku entladen", "mdi:battery-arrow-down"),
            ])),
        ]
        history = [
            {"entity": entities[key], "name": label}
            for key, label in [
                ("pv_power", "Solar"),
                ("load_power", "Haus"),
                ("grid_power", "Netz"),
                ("battery_power_pcs", "Akku"),
            ]
            if key in entities
        ]
        if history:
            groups.append(("Verlauf", "mdi:chart-line", [{
                "type": "history-graph",
                "hours_to_show": 24,
                "entities": history,
                "grid_options": {"columns": "full"},
            }]))

        sections = [
            {"type": "grid", "cards": [
                {"type": "heading", "heading": title, "icon": icon}, *cards
            ]}
            for title, icon, cards in groups if cards
        ]
        if not sections:
            raise HomeAssistantError("Für diese Anlage sind keine Dashboard-Sensoren aktiviert.")

        dashboard = {"views": [{
            "title": entry.title,
            "path": "solix-x1",
            "icon": "mdi:solar-power",
            "type": "sections",
            "max_columns": 2,
            "sections": sections,
        }]}
        return {"yaml": yaml.safe_dump(dashboard, allow_unicode=True, sort_keys=False)}

    hass.services.async_register(
        DOMAIN,
        "generate_dashboard",
        generate_dashboard,
        schema=vol.Schema({vol.Optional("config_entry_id"): cv.string}),
        supports_response=SupportsResponse.ONLY,
    )
