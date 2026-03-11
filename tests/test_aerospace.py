import sys
import textwrap
import tomllib
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow" / "scripts"))

from lib.aerospace import extract_shortcuts


CONFIG_TEXT = textwrap.dedent(
    """
    start-at-login = true

    [mode.main.binding]
    alt-c = 'exec-and-forget open -a ChatGPT'
    alt-b = ['balance-sizes', 'mode main']
    # alfred-name: Should Not Apply
    alt-i = 'workspace Inbox'
    alt-f = 'flatten-workspace-tree' # alfred-name: Flatten Tree
    alt-s = 'workspace Secret' # alfred-skip
    alt-q = '''
    exec-and-forget bash -lc "echo hidden"
    ''' # alfred-skip

    [mode."service-mode".binding]
    "alt-shift-h" = ['join-with left', 'mode main']
    alt-shift-f = '''exec-and-forget bash -lc '
    echo fix
    ' ''' # alfred-name: Fix Layout

    [mode.main]
    # alfred-name: Should not leak
    """
)


class ExtractShortcutsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = tomllib.loads(CONFIG_TEXT)

    def test_uses_inline_alfred_name_comments_for_display_names(self) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertEqual(entries[("main", "alt-f")]["description"], "Flatten Tree")
        self.assertEqual(
            entries[("service-mode", "alt-shift-f")]["description"], "Fix Layout"
        )

    def test_preserves_existing_fallback_description_without_inline_comment(
        self,
    ) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertEqual(entries[("main", "alt-b")]["description"], "balance-sizes")
        self.assertEqual(
            entries[("main", "alt-c")]["description"],
            "exec and forget open -a ChatGPT",
        )
        self.assertEqual(entries[("main", "alt-i")]["description"], "workspace Inbox")
        self.assertEqual(
            entries[("service-mode", "alt-shift-h")]["description"],
            "join-with left",
        )
        self.assertIn(
            "exec and forget open -a ChatGPT",
            entries[("main", "alt-c")]["command"],
        )

    def test_skips_bindings_marked_with_alfred_skip(self) -> None:
        shortcuts = extract_shortcuts(self.config, CONFIG_TEXT)
        entries = {
            (shortcut["mode"], shortcut["shortcut"]): shortcut for shortcut in shortcuts
        }

        self.assertNotIn(("main", "alt-s"), entries)
        self.assertNotIn(("main", "alt-q"), entries)


if __name__ == "__main__":
    unittest.main()
