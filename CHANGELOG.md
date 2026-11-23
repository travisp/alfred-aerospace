# Changelog

## Unreleased

## 1.3.0

- Layout actions now target the window shown in Alfred even if focus has moved.
- Sped up window switching, focused-window details, and workspace results by replacing per-app Spotlight searches with one batched icon lookup (#2).

## 1.2.0

- Added support for inline `# alfred-name: ...` binding comments so `as` can show custom searchable shortcut names instead of raw commands.
- Added support for inline `# alfred-skip` binding comments to hide bindings from Alfred entirely.

## 1.1.0

- Switched `as` shortcut execution to AeroSpace CLI dispatch via `trigger-binding`.
- Added visible error notifications for failed action scripts.
- Added `build-workflow.sh` and made the release workflow reuse the same packaging path.

## 1.0.1

- Added unbound command actions.
- Simplified mode-main shortcut labels.
