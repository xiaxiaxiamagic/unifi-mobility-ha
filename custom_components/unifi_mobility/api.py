"""Local JSON-RPC client for UniFi Mobile Router devices."""

from __future__ import annotations

import asyncio
from ipaddress import ip_address
from itertools import count
from typing import Any

from aiohttp import (
    ClientConnectorCertificateError,
    ClientError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
)
from yarl import URL


class UnifiMobilityError(Exception):
    """Base API error."""


class UnifiMobilityAuthError(UnifiMobilityError):
    """Authentication failed."""


class UnifiMobilityConnectionError(UnifiMobilityError):
    """The device could not be reached."""


class UnifiMobilitySslError(UnifiMobilityConnectionError):
    """The device certificate could not be verified."""


class UnifiMobilityRpcError(UnifiMobilityError):
    """The device returned a JSON-RPC error."""

    def __init__(self, code: int | None, message: str) -> None:
        super().__init__(message)
        self.code = code


def normalize_host(host: str) -> str:
    """Return a validated HTTP(S) origin, including bracketed IPv6 hosts."""
    raw = host.strip().rstrip("/")
    if not raw:
        raise ValueError("Host cannot be empty")
    if "://" not in raw:
        try:
            address = ip_address(raw)
        except ValueError:
            pass
        else:
            if address.version == 6:
                raw = f"[{raw}]"
        raw = f"https://{raw}"
    try:
        url = URL(raw)
        if url.scheme not in {"http", "https"} or url.host is None:
            raise ValueError
        if url.user is not None or url.password is not None:
            raise ValueError
        return str(url.origin())
    except (TypeError, ValueError) as err:
        raise ValueError("Host must be a valid HTTP(S) address") from err


class UnifiMobilityApi:
    """Communicate with the UMR Local Portal API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        password: str,
        verify_ssl: bool = False,
    ) -> None:
        self._session = session
        self._host = normalize_host(host)
        self._password = password
        self._verify_ssl = verify_ssl
        self._token: str | None = None
        self._login_lock = asyncio.Lock()
        self._timeout = ClientTimeout(total=12)
        self._request_ids = count(1)
        self._request_semaphore = asyncio.Semaphore(3)

    @property
    def host(self) -> str:
        """Return the normalized device origin."""
        return self._host

    async def async_login(self) -> None:
        """Create a local portal session."""
        async with self._login_lock:
            await self._async_login_unlocked()

    async def _async_login_unlocked(self) -> None:
        """Create a session while the login lock is held."""
        result = await self._request(
            "/ubus/call/session",
            "login",
            {
                "username": "ui",
                "password": self._password,
                "timeout": 2129920,
            },
            authenticated=False,
        )
        token = result.get("ubus_rpc_session") if isinstance(result, dict) else None
        if not token:
            raise UnifiMobilityAuthError("The device did not return a session token")
        self._token = token

    async def async_call(
        self, method: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Call a read-only uimqtt method, renewing the session once if needed."""
        if self._token is None:
            async with self._login_lock:
                if self._token is None:
                    await self._async_login_unlocked()
        token = self._token
        try:
            return await self._request("/ubus/call/uimqtt", method, params or {})
        except UnifiMobilityAuthError:
            async with self._login_lock:
                # Other parallel calls may already have refreshed this session.
                if self._token == token:
                    self._token = None
                    await self._async_login_unlocked()
            return await self._request("/ubus/call/uimqtt", method, params or {})

    async def async_logout(self) -> None:
        """Destroy the current local session when possible."""
        if self._token is None:
            return
        try:
            await self._request("/ubus/call/session", "destroy", {})
        except UnifiMobilityError:
            pass
        finally:
            self._token = None

    async def _request(
        self,
        path: str,
        method: str,
        params: dict[str, Any],
        authenticated: bool = True,
    ) -> Any:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if authenticated and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._request_ids),
            "method": method,
            "params": params,
        }

        try:
            async with self._request_semaphore:
                async with self._session.post(
                    f"{self._host}{path}",
                    json=payload,
                    headers=headers,
                    ssl=self._verify_ssl,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()
                    body = await response.json(content_type=None)
        except ClientConnectorCertificateError as err:
            raise UnifiMobilitySslError(str(err)) from err
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise UnifiMobilityAuthError(str(err)) from err
            raise UnifiMobilityConnectionError(str(err)) from err
        except (TimeoutError, ClientError, ValueError) as err:
            raise UnifiMobilityConnectionError(str(err)) from err

        error = body.get("error") if isinstance(body, dict) else None
        if error:
            code = error.get("code")
            message = str(error.get("message", "Unknown JSON-RPC error"))
            if code in (-32002, 6) or "access denied" in message.lower():
                raise UnifiMobilityAuthError(message)
            raise UnifiMobilityRpcError(code, message)
        if not isinstance(body, dict) or "result" not in body:
            raise UnifiMobilityRpcError(None, "Empty JSON-RPC result")
        return body["result"]
