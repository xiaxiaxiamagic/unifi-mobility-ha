"""Focused tests for the UMR JSON-RPC client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.unifi_mobility.api import (
    UnifiMobilityApi,
    UnifiMobilityAuthError,
)


@pytest.mark.asyncio
async def test_parallel_calls_share_login() -> None:
    api = UnifiMobilityApi(MagicMock(), "192.0.2.1", "secret")
    api._async_login_unlocked = AsyncMock(
        side_effect=lambda: setattr(api, "_token", "x")
    )
    api._request = AsyncMock(return_value={"ok": True})
    assert await api.async_call("InfoLowDump") == {"ok": True}
    api._async_login_unlocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_auth_error_is_exposed() -> None:
    api = UnifiMobilityApi(MagicMock(), "192.0.2.1", "bad")
    api._request = AsyncMock(side_effect=UnifiMobilityAuthError("denied"))
    with pytest.raises(UnifiMobilityAuthError):
        await api.async_login()


@pytest.mark.asyncio
async def test_auth_failure_refreshes_session_once() -> None:
    api = UnifiMobilityApi(MagicMock(), "192.0.2.1", "secret")
    api._token = "old"
    api._async_login_unlocked = AsyncMock(
        side_effect=lambda: setattr(api, "_token", "new")
    )
    api._request = AsyncMock(
        side_effect=[UnifiMobilityAuthError("expired"), {"ok": True}]
    )
    assert await api.async_call("InfoLowDump") == {"ok": True}
    api._async_login_unlocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_clears_token_on_failure() -> None:
    api = UnifiMobilityApi(MagicMock(), "192.0.2.1", "secret")
    api._token = "token"
    api._request = AsyncMock(side_effect=UnifiMobilityAuthError("expired"))
    await api.async_logout()
    assert api._token is None
