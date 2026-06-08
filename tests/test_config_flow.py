"""Tests for the Z407 config flow."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType
from tests.common import MockConfigEntry

from custom_components.logitech_z407.config_flow import LogitechZ407ConfigFlow
from custom_components.logitech_z407.const import DOMAIN


@pytest.mark.asyncio
async def test_bluetooth_discovery_shows_form(hass):
    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_bluetooth(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Z407")
    )
    assert result["type"] == FlowResultType.FORM
    assert CONF_ADDRESS in result["data_schema"].schema


@pytest.mark.asyncio
async def test_bluetooth_discovery_then_complete_flow(hass):
    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_bluetooth(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Z407")
    )
    assert result["type"] == FlowResultType.FORM

    result = await flow.async_step_user(
        {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDRESS] == "AA:BB:CC:DD:EE:FF"


@pytest.mark.asyncio
async def test_bluetooth_discovery_aborts_when_configured(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data={CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
    )
    entry.add_to_hass(hass)

    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_bluetooth(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Z407")
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_user_step_shows_discovered_devices(hass):
    discovery_flow = LogitechZ407ConfigFlow()
    discovery_flow.hass = hass
    await discovery_flow.async_step_bluetooth(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Z407")
    )

    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user()
    assert result["type"] == FlowResultType.FORM


@pytest.mark.asyncio
async def test_user_step_manual_entry_shows_form_when_empty(hass):
    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user()
    assert result["type"] == FlowResultType.FORM
    assert CONF_ADDRESS in result["data_schema"].schema


@pytest.mark.asyncio
async def test_user_step_manual_entry_creates_entry(hass):
    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user(
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDRESS] == "AA:BB:CC:DD:EE:FF"


@pytest.mark.asyncio
async def test_user_step_manual_entry_invalid_address(hass):
    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user(
        {CONF_ADDRESS: "not-a-mac"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_ADDRESS: "invalid_address"}


@pytest.mark.asyncio
async def test_manual_entry_aborts_when_configured(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data={CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
    )
    entry.add_to_hass(hass)

    flow = LogitechZ407ConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user(
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
