# AeroSpace Alfred Workflow

Alfred workflow for the AeroSpace window manager. It lists shortcuts from your config, executes them via AppleScript, and provides window switching and workspace overview tools.

## Setup

Install [AeroSpace](https://github.com/nikitabobko/AeroSpace) and grant Alfred Accessibility permission to allow shortcut execution.

## Usage

Search and execute AeroSpace shortcuts (keyword is configurable in workflow settings) via the `as` keyword.
![Shortcuts list](images/as.png)

Alternatively, switch windows in the focused workspace via the `asw-focused` keyword.
![Focused workspace windows](images/asw-focused.png)

Alternatively, browse workspaces and their windows via the `asws` keyword.
![Workspace overview](images/asws.png)

Alternatively, inspect the focused window and change layout via the `asfocused` keyword.
![Focused window details](images/asfocused.png)

## Workflow’s Configuration

- Default Workspace: choose focused or all workspaces for `asw`.
- Notifications: toggle notifications after shortcut execution.
- Keywords: all keywords are configurable in workflow settings.

## Notes

- AeroSpace CLI must be available on PATH.
- Notifications require Alfred’s Notifications permission if enabled.

## Credits

Initially built to match the behavior of the [AeroSpace Raycast extension](https://www.raycast.com/limonkufu/aerospace).
