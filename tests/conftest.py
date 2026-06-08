"""Test fixtures for Logitech Z407."""

from __future__ import annotations

import pytest

from custom_components.logitech_z407.config_flow import LogitechZ407ConfigFlow


@pytest.fixture(autouse=True)
def reset_discovered_devices():
    """Keep config-flow discovery state isolated between tests."""

    LogitechZ407ConfigFlow.discovered_devices = {}
    yield
    LogitechZ407ConfigFlow.discovered_devices = {}
