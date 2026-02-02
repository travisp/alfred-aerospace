# Aerospace Raycast Extension Analysis

This document summarizes the Aerospace Raycast extension functionality and how each feature is implemented. It is meant to help build a parallel Alfred extension.

## Overview

The extension is a Raycast front-end for the macOS AeroSpace tiling window manager. It relies on the `aerospace` CLI and the user's existing AeroSpace config. The extension provides four user-facing commands plus a menubar view, and exposes a deep-link launch context to allow external automation to invoke the app switcher with pre-filled search.

Key external dependencies:
- `aerospace` CLI (used to locate config, list windows, and focus windows).
- AeroSpace config file (parsed from TOML).
- macOS `System Events` AppleScript (used to simulate key presses for shortcuts).
- macOS `mdfind` (used to resolve an app bundle id to an app path for icons).

## Alfred Workflow Structure (Simple Parity, Same Behavior)

Goal: mirror Raycast behavior (AppleScript keystrokes for shortcuts, CLI for listing/focusing windows), but in Alfred.

Suggested workflow objects:

1) **Keyword: `as` (Aerospace Shortcuts)**
- **Type:** Script Filter
- **Input:** optional user search text
- **Script (shell/Node/Python):**
  - Run `aerospace config --config-path` and expand `~`.
  - Read TOML, extract `mode.*.binding`.
  - Normalize description (JSON stringify, strip quotes, replace word-boundary dashes).
  - Output Alfred items:
    - `title`: description
    - `subtitle`: shortcut string + mode (e.g., `alt-j - mode: main`)
    - `arg`: shortcut string
    - `mods` or `variables` (optional): include mode, binding value
- **Action:** Run Script (AppleScript or shell) to simulate the keystroke.

2) **Keyword: `ascfg` (Show Config)**
- **Type:** Script Filter or Run Script
- **Script:**
  - Resolve config path and return it as an item.
- **Action:** Open File action or `open "<path>"`.
- Optional: Quick Look a rendered TOML file if you want an in-Alfred view.

3) **Keyword: `asw` (Switch Windows)**
- **Type:** Script Filter
- **Input:** user search text
- **Script:**
  - Decide scope: `focused` or `all` (from workflow variable or argument).
  - Run `aerospace list-windows --json --format ...` with `--workspace focused` or `--all`.
  - Parse JSON, resolve app icon paths with `mdfind` for each bundle id.
  - Output items:
    - `title`: app name
    - `subtitle`: window title (and workspace/monitor)
    - `icon`: file path to app
    - `arg`: window id
- **Action:** Run Script to execute `aerospace focus --window-id <id>`.

4) **Keyword: `asw-all` / `asw-focused` (Scope Helpers)**
- **Type:** Keyword or Script Filter with preset variable
- **Behavior:** sets a workflow variable `scope=all|focused` before `asw` runs.

5) **Optional: `asmenubar`**
- Alfred does not have a menubar list; use a keyword or hotkey to show shortcuts instead.

Implementation defaults to match Raycast:
- Use AppleScript keystrokes for shortcut activation.
- Use the `aerospace` CLI for window listing and focusing.
- Use `shell-env` equivalent for PATH if Alfred's environment cannot find `aerospace` (set `PATH` explicitly in scripts).

## Capability Comparison (Raycast vs Alfred Parity)

| Feature | Raycast Extension | Alfred Workflow (parity plan) |
| --- | --- | --- |
| List shortcuts from config | `showShortcuts` command, List UI | Script Filter lists shortcuts from TOML |
| Execute shortcut | AppleScript keystrokes | AppleScript keystrokes |
| Menubar shortcuts | `MenuBarExtra` list | Not available; use keyword/hotkey |
| Show config | Detail view with TOML + open | Script Filter or Run Script + open file |
| Window list (focused/all) | `switchApps` with workspace arg/preference | Script Filter with scope variable/keyword |
| Focus window | `aerospace focus --window-id` | Same CLI call |
| Icons | App path via `mdfind` | Same `mdfind` lookup |
| Search behavior | Prefix match on app name | Match startsWith (or Alfred default) |
| External automation | Raycast deeplink + launchContext | Alfred workflow variables + args |
| Cached window list | `useCachedState` | Optional in script (cache file) |

## Command Inventory (from package.json)

1) **Show Aerospace Shortcuts** (`showShortcuts`, view)
- Presents all key bindings parsed from the AeroSpace config.
- Each item executes the binding by synthesizing a keyboard shortcut via AppleScript.

2) **Show Aerospace Config** (`showConfig`, view)
- Displays the full parsed config as TOML in a detail view.
- Includes an action to open the config file path in the default editor.

3) **Enable Aerospace Menubar Shortcuts** (`shortcutsMenubar`, menu-bar)
- Menubar listing of shortcuts grouped by AeroSpace mode.
- Selecting an item triggers the same AppleScript shortcut execution.

4) **Switch Apps in Workspace** (`switchApps`, view)
- Lists windows from the focused workspace or all workspaces.
- Lets the user focus a chosen window via the `aerospace` CLI.
- Supports preferences and argument for workspace selection.

## Configuration Handling (src/utils/config.tsx)

How config discovery works:
- The extension runs `aerospace config --config-path` to get the active config location.
- If the path starts with `~`, it is expanded to the user home directory.

How config loading works:
- Reads the file synchronously using `fs.readFileSync`.
- Parses content with `@iarna/toml` into a JS object.
- Only the `mode` section is used for shortcuts; the rest is ignored.

Error handling:
- If the file does not exist or TOML parsing fails, a Raycast toast is shown.
- The toast includes a primary action that opens the AeroSpace installation guide.
 - The missing-file error string is exactly: `Config file does not exist. Please check the path in preferences.`
 - The install link opened by the toast is `https://nikitabobko.github.io/AeroSpace/guide#installation`.

Implications for Alfred:
- You will need to shell out to `aerospace config --config-path` or mimic this lookup.
- You should parse TOML and handle errors in a user-friendly way.

## Shortcut Extraction (src/utils/shortcuts.tsx)

How shortcuts are extracted:
- The config is expected to have a `mode` object, each with a `binding` map.
- For each binding key (for example `alt-j`) in each mode, a Shortcut is created:
  - `mode`: the mode name (`main`, `service`, etc.).
  - `shortcut`: the binding key string itself.
  - `description`: derived from the binding value:
    - `JSON.stringify` is applied to the binding value.
    - Quotes are removed.
    - Dashes between word characters are replaced with spaces.
      Example: `move-workspace-to-monitor` becomes `move workspace to monitor`.
- Shortcuts are stored in a record keyed by `mode + key` (not unique to command).

Grouping:
- `groupShortcutsByMode` returns a map of mode -> array of shortcuts.

Implications for Alfred:
- Your display text can be built from the command's TOML binding value with similar normalization.
- Shortcut uniqueness is not enforced beyond `(mode + key)` in the Raycast version.

## Shortcut Execution (src/utils/shortcuts.tsx)

A shortcut is executed by sending keystrokes to macOS:
- The key string (e.g., `alt-j`) is split by `-`.
- Modifiers are mapped:
  - cmd -> "command down"
  - ctrl -> "control down"
  - alt -> "option down"
  - shift -> "shift down"
- The final part is treated as the key.
- If the key is in a keycode map, the script uses `key code N`.
- Otherwise, it uses `keystroke "<key>"`.
- The AppleScript runs via `@raycast/utils` `runAppleScript`.
- The script returns a string; the UI shows a HUD notification.

Note: This does not call the `aerospace` CLI to execute commands; it simulates the keybinding.

Exact AppleScript template used:

```applescript
tell application "System Events"
    key code <keyCode or keystroke> using {<modifier list>}
    return "Executed: <shortcut>(<modifiers> - <key>)"
end
```

Implications for Alfred:
- The Alfred extension can either use AppleScript (same approach) or run `aerospace` commands directly if you map commands to CLI actions.
- If you mimic the Raycast behavior, you need:
  - a keycode map,
  - a modifier map,
  - and an AppleScript runner.

## Key Normalization (src/utils/keys.tsx)

There are two distinct mappings:

1) `normalizeKey` (for Raycast UI shortcuts)
- Converts special keys and names into Raycast-compatible values.
- Examples:
  - `alt` -> `opt`
  - `esc` -> `escape`
  - `left` -> `arrowLeft`
  - `space` -> `space`
  - many keypad and punctuation mappings
- Used in the UI for key equivalents in Raycast list and menubar items.

2) `mapKeyToKeyCode` (for AppleScript)
- Maps key names to macOS key codes.
- Provides common letters, numbers, punctuation, function keys, arrows, and keypad keys.
- Keys are lowercased before lookup.
- Returns `null` if not found (falls back to `keystroke`).

Exact `normalizeKey` map:

```ts
{
  minus: "-",
  equal: "=",
  period: ".",
  comma: ",",
  slash: "/",
  backslash: "\\",
  quote: "'",
  semicolon: ";",
  backtick: "`",
  leftSquareBracket: "[",
  rightSquareBracket: "]",
  space: "space",
  enter: "enter",
  esc: "escape",
  backspace: "backspace",
  tab: "tab",
  keypad0: "0",
  keypad1: "1",
  keypad2: "2",
  keypad3: "3",
  keypad4: "4",
  keypad5: "5",
  keypad6: "6",
  keypad7: "7",
  keypad8: "8",
  keypad9: "9",
  keypadClear: "clear",
  keypadDecimalMark: "decimal",
  keypadDivide: "divide",
  keypadEnter: "enter",
  keypadEqual: "=",
  keypadMinus: "-",
  keypadMultiply: "*",
  keypadPlus: "+",
  left: "arrowLeft",
  down: "arrowDown",
  up: "arrowUp",
  right: "arrowRight",
  alt: "opt"
}
```

Exact `mapKeyToKeyCode` map:

```ts
{
  a: 0,
  s: 1,
  d: 2,
  f: 3,
  h: 4,
  g: 5,
  z: 6,
  x: 7,
  c: 8,
  v: 9,
  iso_section: 10,
  b: 11,
  q: 12,
  w: 13,
  e: 14,
  r: 15,
  y: 16,
  t: 17,
  "1": 18,
  "2": 19,
  "3": 20,
  "4": 21,
  "6": 22,
  "5": 23,
  equal: 24,
  "9": 25,
  "7": 26,
  minus: 27,
  "8": 28,
  "0": 29,
  right_bracket: 30,
  o: 31,
  u: 32,
  left_bracket: 33,
  i: 34,
  p: 35,
  return: 36,
  l: 37,
  j: 38,
  quote: 39,
  k: 40,
  semicolon: 41,
  backslash: 42,
  comma: 43,
  slash: 44,
  n: 45,
  m: 46,
  period: 47,
  tab: 48,
  space: 49,
  grave: 50,
  delete: 51,
  escape: 53,
  command: 55,
  shift: 56,
  caps_lock: 57,
  option: 58,
  control: 59,
  right_shift: 60,
  right_option: 61,
  right_control: 62,
  function: 63,
  f17: 64,
  keypad_decimal: 65,
  keypad_multiply: 67,
  keypad_plus: 69,
  keypad_clear: 71,
  volume_up: 72,
  volume_down: 73,
  mute: 74,
  keypad_divide: 75,
  keypad_enter: 76,
  keypad_minus: 78,
  f18: 79,
  f19: 80,
  keypad_equals: 81,
  keypad_0: 82,
  keypad_1: 83,
  keypad_2: 84,
  keypad_3: 85,
  keypad_4: 86,
  keypad_5: 87,
  keypad_6: 88,
  keypad_7: 89,
  f20: 90,
  keypad_8: 91,
  keypad_9: 92,
  f5: 96,
  f6: 97,
  f7: 98,
  f3: 99,
  f8: 100,
  f9: 101,
  f11: 103,
  f13: 105,
  f16: 106,
  f14: 107,
  f10: 109,
  f12: 111,
  f15: 113,
  help: 114,
  home: 115,
  page_up: 116,
  forward_delete: 117,
  f4: 118,
  end: 119,
  f2: 120,
  page_down: 121,
  f1: 122,
  left_arrow: 123,
  right_arrow: 124,
  down_arrow: 125,
  up_arrow: 126
}
```

Implications for Alfred:
- If you show shortcuts in Alfred results, you may want a similar normalization for display.
- If you simulate keystrokes, you need a keycode map for accurate AppleScript input.

## Show Shortcuts Command (src/showShortcuts.tsx)

User experience:
- Displays a list of shortcuts parsed from config.
- Each item shows:
  - Title: the normalized description from the binding value.
  - Subtitle: the shortcut string (e.g., `alt-j`).
  - Accessory text: the mode name.
- Selecting an item runs the shortcut via AppleScript.

Implementation details:
- Calls `getConfig()` and `extractKeyboardShortcuts()`.
- Uses `normalizeKey` to map modifiers and key equivalents for Raycast shortcuts.
- If the key is `escape`, it substitutes `home` because Raycast reserves `escape`.

Implications for Alfred:
- Similar list structure can be presented in Alfred Script Filter.
- Executing an item should dispatch the keystroke or mapped command.

## Menubar Shortcuts (src/shortcutsMenubar.tsx)

User experience:
- Adds a menubar icon.
- Displays sections per mode with a list of shortcuts.
- Each item includes a native macOS shortcut display.
- Selecting an item executes the shortcut via AppleScript.

Implementation details:
- Same extraction and normalization as `showShortcuts`.
- Uses `MenuBarExtra.Section` per mode.

Implications for Alfred:
- Alfred does not have a menubar list, but you can provide a workflow keyword to show shortcuts.

## Show Config Command (src/showConfig.tsx)

User experience:
- Shows the full config in a detail view as TOML.
- Provides an action to open the config path in the system editor.

Implementation details:
- Uses `getConfig()` + `getConfigPath()`.
- If parsing fails, it shows an error message.
- Otherwise, it uses `TOML.stringify` to render the config.

Implications for Alfred:
- You can provide a workflow action to open the config or show it in a quick view.

## Switch Apps in Workspace (src/switchApps.tsx, src/utils/appSwitcher.tsx)

User experience:
- Lists app windows and allows focusing a window.
- Grouped by workspace (section header includes workspace and monitor name).
- Search filters by app name prefix.
- Supports two scopes: focused workspace or all workspaces.

Implementation details:
- Preferences:
  - `defaultWorkspace` dropdown (focused/all).
- Arguments:
  - `workspace` dropdown (focused/all).
- Workspace selection:
  - Uses argument if provided, otherwise preference.
- Window retrieval:
  - Runs `aerospace list-windows --json --format ...`.
  - Uses `--workspace focused` or `--all` based on selection.
  - The format includes app name, window title, window id, app pid, workspace, app bundle id, and monitor name.
- Icon lookup:
  - For each window, `mdfind` locates the app path for the bundle id.
  - `app-path` is used as a file icon in Raycast.
- Focus action:
  - `aerospace focus --window-id <id>`.
  - Then closes Raycast window (`popToRoot`, `closeMainWindow`).
- Environment:
  - Uses `shell-env` to load a shell PATH so `aerospace` is found.
  - Cached environment is reused across calls.
- UI:
  - Uses `useCachedState` to cache windows between invocations.
  - Initial search text can be set from launch context.
  - Search filters `app-name` with `startsWith`.

Exact CLI invocations used:

```bash
# config path
aerospace config --config-path

# list windows (focused)
aerospace list-windows --json --workspace focused \
  --format "%{app-name} %{window-title} %{window-id} %{app-pid} %{workspace} %{app-bundle-id} %{monitor-name}"

# list windows (all)
aerospace list-windows --json --all \
  --format "%{app-name} %{window-title} %{window-id} %{app-pid} %{workspace} %{app-bundle-id} %{monitor-name}"

# focus window
aerospace focus --window-id <id>

# resolve app path
mdfind 'kMDItemCFBundleIdentifier="<bundleId>"'
```

Process details:
- All `spawnSync` calls use `encoding: "utf8"` and `timeout: 15000`.
- The CLI calls use a cached environment from `shell-env` to ensure PATH is correct.

Implications for Alfred:
- Alfred script filter should call `aerospace list-windows` with `--json` and parse it.
- You will need to map each window to Alfred results, and include a secondary action to focus a window.
- Consider an argument or setting to switch between focused/all.

## Deep Linking / External Automation (README)

- The extension supports Raycast deeplinks with `launchContext`.
- Example:
  - `raycast://extensions/limonkufu/aerospace/switchApps?arguments={"workspace":"all"}&context={"searchText":"AppName"}`
- This lets external tools trigger the app switcher with a pre-filtered search.

Implications for Alfred:
- You can implement equivalent behavior using Alfred workflow variables and Script Filter arguments (for example, pass a search text to pre-filter window list).

## Notable Behavioral Details and Edge Cases

- Shortcut execution uses AppleScript to simulate key events; it does not talk to AeroSpace directly.
- The extension assumes AeroSpace is installed and available on PATH.
- If AeroSpace is missing, `getConfig()` will fail when `aerospace` command cannot run or config path does not exist.
- Search in the app switcher is prefix-only on app name, not window title.
- The `showShortcuts` and menubar views use Raycast shortcut bindings, with `escape` remapped to `home` to avoid conflicts.
- Key name mappings are tailored for Raycast and AppleScript; they are not pulled from AeroSpace itself.
- `switchApps` uses `isLoading={windows.length === 0}`; if the CLI returns an empty list or JSON parsing fails, the UI can appear to load indefinitely.
- `showShortcuts` and `shortcutsMenubar` return no UI if config loading fails; the only feedback is the toast from `handleConfigError`.
- `mdfind` is called once per window to find app paths; results are not cached and can be slow with many windows.
- `mdfind` output is `stdout.trim()`; if multiple paths are returned, the raw multi-line string is used as the icon path.
- `executeShortcut` does not call `normalizeKey` for AppleScript execution. The keycode map expects names like `left_arrow`; if a binding uses `left`, the fallback `keystroke "left"` will type the word instead of sending an arrow key.

## Known Limitations (Derived from Current Code)

- Shortcut execution depends on macOS Accessibility permissions for AppleScript keystrokes.
- Key support is limited to what `mapKeyToKeyCode` recognizes; unmapped keys fall back to literal `keystroke`, which can produce incorrect results for named keys.
- Window search only matches prefix of `app-name`; window title is not used for filtering.
- Window listing appears to “load forever” if the CLI returns an empty list or invalid JSON, because loading state is tied to `windows.length === 0`.
- `mdfind` icon resolution is uncached and runs per window, which can be slow with many windows.
- Multiple `mdfind` results are not disambiguated; the raw multi-line output is used as the icon path.
- Config parsing expects `mode.*.binding`; any bindings outside that structure are ignored.

## Files of Interest (Exact Behavior, Step by Step)

These notes replace the need to keep the original source files in a new project.

### `src/showShortcuts.tsx`

- Calls `getConfig()` to parse the AeroSpace TOML config.
- If there is an error, calls `handleConfigError()` to show a failure toast and offer an install link.
- Calls `extractKeyboardShortcuts(config)` to build a list of shortcuts.
- Renders a Raycast List:
  - `navigationTitle`: `Keyboard Shortcuts`
  - `searchBarPlaceholder`: `Search your shortcuts`
  - `title`: normalized description derived from TOML binding value.
  - `subtitle`: the shortcut string (e.g., `alt-j`).
  - `accessories`: mode name.
- Each item uses the icon file `list-icon.png`.
- For each item:
  - Splits the shortcut on `-` to get modifiers + key.
  - Normalizes modifiers (`alt` -> `opt`) and special keys using `normalizeKey`.
  - If the key is `escape`, substitutes `home` (Raycast reserves `escape`).
  - Sets the Raycast `Action` keyboard shortcut to match the AeroSpace shortcut.
  - Adds an action that calls `executeShortcut(shortcut)` to simulate keystrokes.

### `src/shortcutsMenubar.tsx`

- Same config parsing and shortcut extraction as `showShortcuts.tsx`.
- Groups shortcuts by mode using `groupShortcutsByMode`.
- Creates a menubar extra with `menubar-icon.png` and tooltip `Your Shortcuts`.
- Adds a section for each mode.
- Each menu item displays:
  - Title: shortcut description.
  - Shortcut: mapped modifiers + key (same normalization as in list).
- The `shortcut` field is set so the menu item shows the key equivalent.
- Selecting a menu item triggers `executeShortcut(shortcut)`.

### `src/showConfig.tsx`

- Calls `getConfig()` to parse TOML and `getConfigPath()` to locate the file.
- If parsing fails: shows `Error: <message>` in the detail view.
- If parsing succeeds: renders TOML with `TOML.stringify` inside a markdown code block.
- If config is missing but no error was returned, shows `No configuration available.`.
- Uses `navigationTitle`: `Config File`.
- Adds an action that calls `open(configPath)` to open the file in the default editor.

### `src/switchApps.tsx`

- Reads preference `defaultWorkspace` and optional argument `workspace`.
- Chooses workspace: argument if provided, else preference.
- Initializes `searchText` from `launchContext.searchText` (for deeplinks).
- Uses cached state key `windows` (`useCachedState("windows", [])`) to persist results between runs.
- Computes `navigationTitle`:
  - Focused: `Windows in Workspace <workspace-id>`
  - All: `Windows in All Workspaces`
- Sets `searchBarPlaceholder`: `Search by app name or window title...`.
- On mount: calls `getWindows(workspace)` and stores in cached state.
- Groups windows by workspace for list sections; shows monitor name in section titles.
- Filters list by prefix match on `app-name` when user types.
- Each list item:
  - Title: `app-name`.
  - Subtitle: `window-title`.
  - Icon: file icon from `app-path`.
  - Action: `focusWindow(window-id)` which runs `aerospace focus --window-id`.

### `src/utils/config.tsx`

- `getConfigPath()`:
  - Runs `aerospace config --config-path` via `spawnSync`.
  - Expands `~` to home directory.
- `getConfig()`:
  - Calls `getConfigPath()`.
  - Reads file contents with `fs.readFileSync`.
  - Parses TOML via `@iarna/toml`.
  - Returns `{ config }` or `{ error }`.
- `handleConfigError()`:
  - Shows a Raycast toast with a failure state.
  - Adds a primary action to open the AeroSpace installation guide.

### `src/utils/shortcuts.tsx`

- `extractKeyboardShortcuts(config)`:
  - Iterates `config.mode.*.binding`.
  - Creates a Shortcut per binding:
    - `mode`: mode name.
    - `shortcut`: binding key string.
    - `description`: JSON-stringified binding value, quotes stripped, dash-in-words replaced with spaces.
  - Stores in a record keyed by `mode + key`.
- `groupShortcutsByMode(shortcuts)`:
  - Buckets shortcut objects by their `mode`.
- `executeShortcut(shortcut)`:
  - Splits the shortcut string into modifiers + key.
  - Maps modifiers to AppleScript strings (`command down`, `control down`, etc.).
  - Maps key to keycode if available; else uses `keystroke "x"`.
  - Runs AppleScript with `System Events` via `runAppleScript`.
  - Shows HUD message on success or failure.

### `src/utils/appSwitcher.tsx`

- `env()`:
  - Calls `shellEnvSync()` once and caches the environment (PATH included).
- `getAppPath(bundleId)`:
  - Runs `mdfind 'kMDItemCFBundleIdentifier="<bundleId>"'`.
  - Returns the first matching path (trimmed).
- `getWindows(workspace)`:
  - Builds args for `aerospace list-windows --json --format ...`.
  - Uses `--workspace focused` or `--all` based on input.
  - Parses JSON output.
  - Enriches each window with `app-path` via `getAppPath`.
- `focusWindow(windowId)`:
  - Runs `aerospace focus --window-id <id>`.
  - Then `popToRoot` and `closeMainWindow` to dismiss Raycast UI.

### `src/utils/keys.tsx`

- `normalizeKey(key)`:
  - Maps AeroSpace/Raycast key names to Raycast UI equivalents.
  - Example: `alt` -> `opt`, `esc` -> `escape`, arrows to `arrowLeft` etc.
- `mapKeyToKeyCode(key)`:
  - Maps key names to macOS keycodes for AppleScript `key code`.
  - Returns `null` when unknown, which triggers `keystroke`.

## Alfred Implementation Notes (Practical Parity)

To match feature parity in an Alfred workflow, you will likely need:
- A Script Filter that parses AeroSpace config and lists shortcuts (with mode grouping as subtitle or separate results).
- An action to execute shortcuts via AppleScript (or directly invoke `aerospace` if you choose to map commands).
- A Script Filter to list windows from `aerospace list-windows --json`, with a focused/all toggle.
- An action to focus a window via `aerospace focus --window-id`.
- A workflow keyword to show the config path and open the file.
- Optional pre-filtering via input arguments to approximate the Raycast deeplink `searchText`.
