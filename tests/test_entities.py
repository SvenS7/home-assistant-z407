"""Tests for entity-level behavior."""

from __future__ import annotations

from custom_components.logitech_z407.button import BUTTONS


def test_factory_reset_disabled_by_default():
    factory_button = next(button for button in BUTTONS if button.key == "factory_reset")
    assert factory_button.enabled_default is False


def test_all_buttons_have_display_name():
    for button in BUTTONS:
        assert button.name, f"Button {button.key} is missing a display name"


def test_all_buttons_have_valid_command():
    from custom_components.logitech_z407.const import BUTTON_COMMANDS

    for button in BUTTONS:
        assert button.key in BUTTON_COMMANDS, (
            f"Button {button.key} has no matching command in BUTTON_COMMANDS"
        )

