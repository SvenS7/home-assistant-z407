"""Tests for entity-level behavior."""

from __future__ import annotations

from custom_components.logitech_z407.button import BUTTONS


def test_factory_reset_disabled_by_default():
    factory_button = next(button for button in BUTTONS if button.key == "factory_reset")
    assert factory_button.enabled_default is False

