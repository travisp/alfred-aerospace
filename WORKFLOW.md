# Alfred Workflow Wiring

This repo ships Python scripts that mirror the Raycast Aerospace extension. Use the steps below to wire them into an Alfred workflow.

## Create the workflow

1) Create a new workflow in Alfred.
2) Set the workflow name to `AeroSpace` (or your preference).

## Script Filters

Add these Script Filters and connect them to the action noted. Recommended settings:

- Language: `/bin/bash`
- With input as: `argv`
- Argument Required: off

1) **Shortcuts list**
- Keyword: `as`
- Script: `python3 "$PWD/scripts/shortcuts.py" "$1"`
- Alfred filters results: on
- Connect to: Run Script **Execute Shortcut**

2) **Config path**
- Keyword: `ascfg`
- Script: `python3 "$PWD/scripts/config.py"`
- Alfred filters results: on
- Connect to: Run Script **Open Target**

3) **Windows (default scope)**
- Keyword: `asw`
- Script: `python3 "$PWD/scripts/windows.py" "$1"`
- Alfred filters results: off
- Connect to: Run Script **Focus Window**

4) **Windows (all)**
- Keyword: `asw-all`
- Script: `python3 "$PWD/scripts/windows.py" "$1" all`
- Alfred filters results: off
- Connect to: Run Script **Focus Window**

5) **Windows (focused)**
- Keyword: `asw-focused`
- Script: `python3 "$PWD/scripts/windows.py" "$1" focused`
- Alfred filters results: off
- Connect to: Run Script **Focus Window**

## Run Script actions

Create these Run Script actions using `/bin/bash`, with input as `argv`:

1) **Execute Shortcut**
- Script: `python3 "$PWD/scripts/execute_shortcut.py" "$1"`

2) **Focus Window**
- Script: `python3 "$PWD/scripts/focus_window.py" "$1"`

3) **Open Target**
- Script: `python3 "$PWD/scripts/open_target.py" "$1"`

## Notes

- The scripts attempt to discover the AeroSpace config path using `aerospace config --config-path`.
- Ensure the `aerospace` CLI is installed and accessible from Alfred. The scripts add common Homebrew paths to `PATH` automatically.

## Troubleshooting

- If a Script Filter shows no results, confirm **Argument Required** is off.
- If a keyword runs but returns nothing, verify the Script Filter uses `argv` and the script is called with `$1` (not `{query}`).
- If your Alfred version doesn't show per-object variables, use the explicit `all`/`focused` argument shown above instead of workflow variables.
- If `asw` returns an error, run `aerospace list-windows --json` in a terminal to verify permissions and AeroSpace availability.
- For shortcut execution, macOS Accessibility permissions are required for Alfred/osascript.
