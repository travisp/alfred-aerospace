import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow" / "scripts"))

import focused_window
import set_layout
import workspace_overview


class LayoutActionTest(unittest.TestCase):
    def test_actions_target_the_window_shown_in_results(self) -> None:
        for current_layout, toggle in (("h_tiles", "floating"), ("floating", "tiling")):
            with self.subTest(current_layout=current_layout):
                window = {"window-id": 42, "window-layout": current_layout}
                output = io.StringIO()
                with (
                    patch("sys.argv", ["focused_window.py", "set layout"]),
                    patch.object(focused_window, "get_focused_window", return_value=window),
                    redirect_stdout(output),
                ):
                    focused_window.main()

                actions = json.loads(output.getvalue())["items"][1:]
                layouts = {"h_tiles", "v_tiles", "h_accordion", "v_accordion", toggle}
                layouts.discard(current_layout)
                self.assertEqual({action["autocomplete"] for action in actions}, layouts)
                for action in actions:
                    with patch("sys.argv", ["set_layout.py", action["arg"]]), patch(
                        "lib.aerospace._run_command"
                    ) as run:
                        set_layout.main()
                    run.assert_called_once_with(
                        ["aerospace", "layout", "--window-id", "42", action["autocomplete"]]
                    )


class WorkspaceOverviewTest(unittest.TestCase):
    def test_overview_and_detail_share_the_workspace_summary(self) -> None:
        windows = [
            {"workspace": "1", "app-name": name, "window-id": index}
            for index, name in enumerate(("Mail", "Editor", "Mail", "Safari", "Notes"), 1)
        ]
        workspaces = [
            {"workspace": "1", "monitor-name": "Internal", "workspace-is-focused": True},
            {"workspace": "2", "monitor-name": "External"},
        ]

        def results(query: str) -> list[dict]:
            output = io.StringIO()
            with (
                patch("sys.stdin", io.StringIO()),
                patch("sys.argv", ["workspace_overview.py", query]),
                patch.object(workspace_overview, "list_windows", return_value=windows),
                patch.object(workspace_overview, "list_workspaces", return_value=workspaces),
                redirect_stdout(output),
            ):
                workspace_overview.main()
            return json.loads(output.getvalue())["items"]

        summary = {
            "title": "Workspace 1 [focused]",
            "subtitle": "5 windows | focused | Internal | apps Mail, Editor, Safari +1",
            "valid": False,
        }
        self.assertIn({**summary, "autocomplete": "1 "}, results(""))
        self.assertEqual(results("1")[0], summary)
        filtered = results("1 editor")
        self.assertEqual(filtered[0]["subtitle"], "1 windows | focused | Internal | apps Editor")
        self.assertEqual([item["arg"] for item in filtered[1:]], ["2"])


if __name__ == "__main__":
    unittest.main()
