# Changelog

## Unreleased

- Added support for inline `# alfred-name: ...` binding comments so `as` can show custom searchable shortcut names instead of raw commands.
- Added support for inline `# alfred-skip` binding comments to hide bindings from Alfred entirely.

## 1.1.0

- Switched `as` shortcut execution to AeroSpace CLI dispatch via `trigger-binding`.
- Added visible error notifications for failed action scripts.
- Added `build-workflow.sh` and made the release workflow reuse the same packaging path.

## 1.0.1

- Added unbound command actions.
- Simplified mode-main shortcut labels.
