from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from uvicorn import Config

from backend.core import event_loop


def test_windows_uses_selector_loop(monkeypatch):
    expected_loop = Mock()
    selector_factory = Mock(return_value=expected_loop)
    default_factory = Mock()

    monkeypatch.setattr(
        event_loop,
        "sys",
        SimpleNamespace(platform="win32"),
    )
    monkeypatch.setattr(
        event_loop.asyncio,
        "SelectorEventLoop",
        selector_factory,
    )
    monkeypatch.setattr(
        event_loop.asyncio,
        "new_event_loop",
        default_factory,
    )

    assert event_loop.new_event_loop() is expected_loop
    selector_factory.assert_called_once_with()
    default_factory.assert_not_called()


def test_other_platforms_use_default_loop(monkeypatch):
    expected_loop = Mock()
    default_factory = Mock(return_value=expected_loop)

    monkeypatch.setattr(
        event_loop,
        "sys",
        SimpleNamespace(platform="darwin"),
    )
    monkeypatch.setattr(
        event_loop.asyncio,
        "new_event_loop",
        default_factory,
    )

    assert event_loop.new_event_loop() is expected_loop
    default_factory.assert_called_once_with()


@pytest.mark.parametrize("reload", [False, True])
def test_uvicorn_uses_explicit_loop_factory(reload):
    config = Config(
        "backend.app.main:app",
        loop="backend.core.event_loop:new_event_loop",
        reload=reload,
    )

    assert config.get_loop_factory() is event_loop.new_event_loop
