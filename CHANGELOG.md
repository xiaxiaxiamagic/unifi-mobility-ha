# Changelog

## v0.4.1

- Completes entity ID migration for legacy data-size IDs with numeric suffixes.

## v0.4.0

- Migrates automatically generated numbered entity IDs to stable readable IDs.
- Creates entities according to capabilities detected from the first firmware poll.
- Adds Home Assistant Repairs for repeated optional RPC failures and SSL errors.
- Limits local API concurrency and adds exponential backoff with polling jitter.
- Expands API, parser, entity, diagnostics, coordinator, and migration tests.
- Adds bilingual release notes and upgrade documentation.

## v0.3.1

- Parses billing-cycle Unix timestamps using the Home Assistant timezone.
- Displays the next billing date and calendar-day countdown correctly.

## v0.3.0

- Added firmware-tolerant parsing, safe diagnostic buttons, data-plan sensors,
  stale-data handling, stable device identity, tests, and automated releases.

## v0.2.0

- First public release.
