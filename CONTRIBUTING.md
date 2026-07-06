# Contributing

Contributions and anonymized firmware samples are welcome. Never include passwords,
session tokens, IP or MAC addresses, IMEI, ICCID, SSIDs, or client identifiers.

## Development

```bash
python -m pip install -e ".[test]"
ruff check custom_components tests
pytest
```

Keep router operations read-only unless a change has an explicit safety and rollback
design. Add tests for every new firmware field mapping or API behavior.
