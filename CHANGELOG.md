# Changelog

## v0.5.1

- Release after successful HACS and Hassfest validation for default repository
  submission.
- 在 HACS 与 Hassfest 校验成功后发布，用于申请加入 HACS 默认仓库。

## v0.5.0

- Add polling health, retry state, section freshness, and last-success details to
  redacted diagnostics.
- Add an anonymized UMR-Industrial-EU `1.17.11` compatibility fixture and tests.
- Normalize and validate router origins with IPv4, host name, port, and IPv6
  support.
- Prepare HACS default-listing metadata, ZIP release discovery, compatibility
  documentation, scheduled validation, and the one-click HACS link.
- 诊断信息新增轮询健康状态，并完善固件兼容样本、IPv6 地址及 HACS 收录准备。

## v0.4.2

- Make legacy entity ID migration reliable by reading entities directly from the
  config entry registry.
- 修复真实 Home Assistant 环境中两个旧流量实体 ID 未迁移的问题。

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
