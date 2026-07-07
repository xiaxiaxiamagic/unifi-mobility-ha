"""Focused tests for the UMR JSON-RPC client."""

import ssl
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectorCertificateError, ClientResponseError

from custom_components.unifi_mobility.api import (
    UnifiMobilityApi,
    UnifiMobilityAuthError,
    UnifiMobilitySslError,
    normalize_host,
)


class FakeResponse:
    def __init__(self, body=None, error=None) -> None:
        self.body = body
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def raise_for_status(self) -> None:
        if self.error:
            raise self.error

    async def json(self, content_type=None):
        return self.body


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


@pytest.mark.asyncio
async def test_request_adds_jsonrpc_id() -> None:
    session = MagicMock()
    session.post.return_value = FakeResponse({"result": {"ok": True}})
    api = UnifiMobilityApi(session, "192.0.2.1", "secret")
    assert await api._request("/rpc", "Status", {}, authenticated=False) == {"ok": True}
    payload = session.post.call_args.kwargs["json"]
    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == 1


@pytest.mark.asyncio
async def test_http_401_is_auth_error() -> None:
    session = MagicMock()
    error = ClientResponseError(MagicMock(real_url="https://router"), (), status=401)
    session.post.return_value = FakeResponse(error=error)
    api = UnifiMobilityApi(session, "192.0.2.1", "secret")
    with pytest.raises(UnifiMobilityAuthError):
        await api._request("/rpc", "Status", {})


@pytest.mark.asyncio
async def test_certificate_error_is_classified() -> None:
    session = MagicMock()
    error = ClientConnectorCertificateError(
        MagicMock(host="router", port=443, ssl=True),
        ssl.SSLCertVerificationError("untrusted"),
    )
    session.post.return_value = FakeResponse(error=error)
    api = UnifiMobilityApi(session, "192.0.2.1", "secret", verify_ssl=True)
    with pytest.raises(UnifiMobilitySslError):
        await api._request("/rpc", "Status", {})


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("192.168.105.1", "https://192.168.105.1"),
        ("http://router.local:8080/path", "http://router.local:8080"),
        ("fd00::105", "https://[fd00::105]"),
        ("https://[fd00::105]:8443/", "https://[fd00::105]:8443"),
    ],
)
def test_normalize_host(raw: str, expected: str) -> None:
    assert normalize_host(raw) == expected


@pytest.mark.parametrize("raw", ["", "ftp://router.local", "https://user@router"])
def test_normalize_host_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_host(raw)
