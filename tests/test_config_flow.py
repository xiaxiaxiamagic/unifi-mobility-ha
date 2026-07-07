"""Tests for config-flow connection lifecycle helpers."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.unifi_mobility.api import UnifiMobilityConnectionError
from custom_components.unifi_mobility.config_flow import _async_test_api


@pytest.mark.asyncio
async def test_probe_always_logs_out() -> None:
    api = MagicMock()
    api.async_login = AsyncMock()
    api.async_call = AsyncMock(side_effect=[{"fw": "1.0"}, {"model_name": "UMR"}])
    api.async_logout = AsyncMock()

    assert await _async_test_api(api, probe=True) == (
        {"fw": "1.0"},
        {"model_name": "UMR"},
    )
    api.async_logout.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_connection_still_logs_out() -> None:
    api = MagicMock()
    api.async_login = AsyncMock(side_effect=UnifiMobilityConnectionError("offline"))
    api.async_logout = AsyncMock()

    with pytest.raises(UnifiMobilityConnectionError):
        await _async_test_api(api, probe=False)
    api.async_logout.assert_awaited_once()
