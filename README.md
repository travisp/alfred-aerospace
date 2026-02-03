# AeroSpace Alfred Workflow

Alfred workflow that mirrors the AeroSpace Raycast extension. It lists shortcuts from your AeroSpace config, executes them via AppleScript, and provides a fast window switcher.

## Features

- List AeroSpace shortcuts from your config and execute them.
- Show and open the active AeroSpace config file.
- Switch windows in the focused workspace or across all workspaces.
- Window list shows workspace/monitor context and app icons.
- Workspace overview and focused window details with layout actions.

## Requirements

- Alfred 5 with Powerpack.
- AeroSpace installed and available on PATH.
- Python 3.11+ (uses `tomllib`).
- macOS Accessibility permission for Alfred (required for shortcut execution).
- Notifications permission for Alfred if you enable notifications.

## Install

1) Download the latest `AeroSpace.alfredworkflow` from Releases.
2) Double-click to import into Alfred.

## Configuration

- **Default Workspace**: choose focused or all workspaces for `asw` in the workflow settings.
- **Notifications**: toggle notifications after shortcut execution (System Settings > Notifications > Alfred).

## Usage

- `as` — list AeroSpace shortcuts.
- `ascfg` — open the AeroSpace config (Shift for preview).
- `asw` — windows in focused workspace.
- `asw-all` — windows in all workspaces.
- `asw-focused` — windows in focused workspace.
- `asws` — workspace overview (grouped windows).
- `asfocused` — focused window details + layout actions.

## Troubleshooting

- **No shortcuts or config errors**: confirm `aerospace config --config-path` works in Terminal.
- **Shortcuts don’t execute**: grant Alfred Accessibility permissions.
- **Icons missing**: Spotlight indexing must be enabled (icons use `mdfind`).
- **Python errors**: ensure `python3` is available on PATH and is 3.11+.

## Credits

Initially built to match the behavior of the [AeroSpace Raycast extension](https://www.raycast.com/limonkufu/aerospace).
