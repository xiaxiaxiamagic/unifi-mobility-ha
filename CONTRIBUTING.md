# Contributing

Contributions and anonymized firmware samples are welcome. Never include passwords,
session tokens, IP or MAC addresses, IMEI, ICCID, SSIDs, or client identifiers.

## Development

```bash
python -m pip install -e ".[test]"
ruff check custom_components tests
pytest
```

Keep polling operations read-only. Writable controls require explicit user intent,
firmware capability checks, serialized calls, refreshed state, and focused tests.
Never add factory reset, credential, SIM PIN, or firmware-write controls without a
separate safety and rollback design. Add tests for every new field or API behavior.

## Firmware compatibility samples

Place anonymized samples in `tests/fixtures/` and add a focused test in
`tests/test_firmware_fixtures.py`. Keep the response structure intact, but replace
all passwords, session tokens, IP and MAC addresses, IMEI, ICCID, SSIDs, carrier
account details, and client identifiers with `REDACTED`. Include the router model
and firmware version as fixture metadata.
