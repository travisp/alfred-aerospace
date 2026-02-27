# AeroSpace Alfred Workflow

Alfred workflow for the AeroSpace window manager. It lists shortcuts from your config, executes them via AppleScript, and provides window switching and workspace overview tools.

## Setup

Install [AeroSpace](https://github.com/nikitabobko/AeroSpace) and grant Alfred Accessibility permission to allow shortcut execution.

## Usage

Search and execute AeroSpace shortcuts (keyword is configurable in workflow settings) via the `as` keyword.

The `as` command also includes a small set of built-in AeroSpace actions when they are not bound in your config:

- `balance-sizes`
- `workspace-back-and-forth`
- `flatten-workspace-tree`
- `reload-config`
- `fullscreen --no-outer-gaps`
- `layout tiling floating`

These entries are shown with the subtitle `no bound shortcut`.

For bindings like `['flatten-workspace-tree', 'mode main']`, shortcut titles are simplified to show just the actionable command (`flatten-workspace-tree`).

Commands (keywords are configurable):

- `as` — list shortcuts
- `ascfg` — open the config file
- `asw` — switch windows (default scope)
- `asw-all` — switch windows (all workspaces)
- `asw-focused` — switch windows (focused workspace)
- `asws` — workspace overview
- `asfocused` — focused window details and layout actions

<img src="images/as.png" alt="Shortcuts list" width="400" />

Switch windows in the focused workspace via the `asw-focused` keyword.
<img src="images/asw-focused.png" alt="Focused workspace windows" width="400" />

Switch windows using the default scope via the `asw` keyword.

Switch windows across all workspaces via the `asw-all` keyword.

Browse workspaces and their windows via the `asws` keyword.
<img src="images/asws.png" alt="Workspace overview" width="400" />

Inspect the focused window and change layout via the `asfocused` keyword.
<img src="images/asfocused.png" alt="Focused window details" width="400" />

## Workflow’s Configuration

- Default Workspace: set the default scope for `asw`.
- Notifications: toggle notifications after shortcut execution.
- Keywords: update any keyword in workflow settings.

## Notes

- AeroSpace CLI must be available on PATH.
- Notifications require Alfred’s Notifications permission if enabled.

## Credits

Initially built to match the behavior of the [AeroSpace Raycast extension](https://www.raycast.com/limonkufu/aerospace).
