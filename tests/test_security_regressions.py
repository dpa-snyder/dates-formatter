import ast
import importlib.util
import logging
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import openpyxl
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "src/date-formatter-gui.py",
    ROOT / "prod/date-formatter-gui.py",
    ROOT / "prod/date-formatter-single.py",
    ROOT / "prod/date-formatter-range.py",
]


def load_gui(path):
    spec = importlib.util.spec_from_file_location("security_gui", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_export_boundary(path):
    # Standalone scripts launch Tk at import. Execute their actual pure helpers
    # without launching a window or running a user-selected conversion.
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and node.name in {"save_dataframe", "load_dataframe", "strip_parenthetical_notes",
                          "WindowsOutputDirectory", "OutputDirectory"}
    ]
    namespace = {"pd": pd, "os": os, "stat": stat, "tempfile": tempfile}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class TestSecureExports(unittest.TestCase):
    def test_xlsx_strings_stay_literal_without_changing_numbers(self):
        df = pd.DataFrame({
            "=1+1": ["=2+2"],
            "Original_Date": ["=3+3"],
            "Unselected": ["001.001"],
            "Number": [42],
            "Boolean": [True],
        })
        for script in SCRIPTS:
            with self.subTest(script=script.name, parent=script.parent.name):
                boundary = load_export_boundary(script)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "output.xlsx"
                    boundary["save_dataframe"](df, path)
                    workbook = openpyxl.load_workbook(path, data_only=False)
                    try:
                        cells = workbook.active
                        self.assertEqual(cells["A1"].value, "=1+1")
                        self.assertEqual(cells["A1"].data_type, "s")
                        self.assertEqual(cells["A2"].value, "=2+2")
                        self.assertEqual(cells["A2"].data_type, "s")
                        self.assertEqual(cells["B2"].value, "=3+3")
                        self.assertEqual(cells["B2"].data_type, "s")
                        self.assertEqual(cells["C2"].value, "001.001")
                        self.assertEqual(cells["D2"].value, 42)
                        self.assertEqual(cells["D2"].data_type, "n")
                        self.assertIs(cells["E2"].value, True)
                    finally:
                        workbook.close()

    def test_symlink_output_is_refused_and_hardlink_is_not_followed(self):
        for script in SCRIPTS:
            boundary = load_export_boundary(script)
            for extension in (".csv", ".xlsx"):
                with self.subTest(script=str(script.relative_to(ROOT)), extension=extension):
                    with tempfile.TemporaryDirectory() as directory:
                        sentinel = Path(directory) / "sentinel"
                        sentinel.write_text("unchanged sentinel")
                        output = Path(directory) / ("output" + extension)
                        output.symlink_to(sentinel)
                        with self.assertRaises(ValueError):
                            boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
                        self.assertEqual(sentinel.read_text(), "unchanged sentinel")
                        output.unlink()
                        os.link(sentinel, output)
                        boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
                        self.assertEqual(sentinel.read_text(), "unchanged sentinel")
                        self.assertFalse(os.path.samefile(sentinel, output))

    @unittest.skipUnless(os.name == "posix", "Directory-handle replacement hook")
    def test_late_destination_symlink_cannot_redirect_write(self):
        boundary = load_export_boundary(SCRIPTS[0])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.csv"
            sentinel = Path(directory) / "sentinel"
            sentinel.write_text("unchanged sentinel")
            replace = os.replace

            def substitute_then_replace(source, target, **kwargs):
                os.symlink(str(sentinel), target, dir_fd=kwargs['dst_dir_fd'])
                replace(source, target, **kwargs)

            with patch.object(os, "replace", side_effect=substitute_then_replace):
                boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
            self.assertEqual(sentinel.read_text(), "unchanged sentinel")
            self.assertFalse(output.is_symlink())
            self.assertIn("1962", output.read_text())

    def test_write_failure_preserves_original_and_cleans_temp(self):
        boundary = load_export_boundary(SCRIPTS[0])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.csv"
            output.write_text("original bytes")

            def fail_after_partial_write(_df, stream, **_kwargs):
                stream.write("partial")
                raise OSError("injected serialization failure")

            with patch.object(pd.DataFrame, "to_csv", fail_after_partial_write):
                with self.assertRaises(OSError):
                    boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
            self.assertEqual(output.read_text(), "original bytes")
            self.assertEqual(list(Path(directory).iterdir()), [output])

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits")
    def test_overwrite_keeps_permissions_and_new_outputs_are_private(self):
        for script in SCRIPTS:
            boundary = load_export_boundary(script)
            for extension in (".csv", ".xlsx"):
                with self.subTest(script=str(script.relative_to(ROOT)), extension=extension):
                    with tempfile.TemporaryDirectory() as directory:
                        output = Path(directory) / ("output" + extension)
                        output.write_text("original")
                        output.chmod(0o600)
                        boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
                        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
                        output.unlink()
                        boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
                        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "posix", "Directory-handle publication")
    def test_post_validation_private_directory_swap_does_not_publish_substitute(self):
        for script in SCRIPTS:
            boundary = load_export_boundary(script)
            with self.subTest(script=str(script.relative_to(ROOT))):
                with tempfile.TemporaryDirectory() as directory:
                    parent = Path(directory)
                    output = parent / "output.csv"
                    replace = os.replace
                    moved = parent / "moved-private"
                    def swap_directory_then_publish(source, target, **kwargs):
                        private = next(parent.glob(".date-formatter-*"))
                        private.rename(moved)
                        private.mkdir()
                        (private / "output").write_text("attacker bytes")
                        replace(source, target, **kwargs)
                    with patch.object(os, "replace", side_effect=swap_directory_then_publish):
                        boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), output)
                    self.assertEqual(output.read_text(), "Date\n1962\n")
                    self.assertEqual(next(parent.glob(".date-formatter-*")).joinpath("output").read_text(),
                                     "attacker bytes")

    @unittest.skipUnless(os.name == "posix", "Directory identity and handles")
    def test_directory_substitution_after_load_is_refused(self):
        for script in SCRIPTS:
            boundary = load_export_boundary(script)
            with tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                selected, victim = parent / "selected", parent / "victim"
                selected.mkdir()
                victim.mkdir()
                path = selected / "output.csv"
                path.write_text("Date\n1962\n")
                df, identity = boundary["load_dataframe"](path)
                (victim / path.name).write_text("private sentinel")
                selected.rename(parent / "original")
                selected.symlink_to(victim, target_is_directory=True)
                with self.assertRaisesRegex(OSError, "selected directory changed"):
                    boundary["save_dataframe"](df, path, identity)
                self.assertEqual((victim / path.name).read_text(), "private sentinel")

    @unittest.skipUnless(os.name == "posix", "Directory-handle publication")
    def test_directory_swap_during_serialization_cannot_redirect_save(self):
        boundary = load_export_boundary(SCRIPTS[0])
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            selected, victim = parent / "selected", parent / "victim"
            selected.mkdir()
            victim.mkdir()
            path = selected / "output.csv"
            (victim / path.name).write_text("private sentinel")
            original_to_csv = pd.DataFrame.to_csv
            def swap_then_serialize(frame, stream, **options):
                selected.rename(parent / "original")
                selected.symlink_to(victim, target_is_directory=True)
                return original_to_csv(frame, stream, **options)
            with patch.object(pd.DataFrame, "to_csv", swap_then_serialize):
                boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), path)
            self.assertEqual((victim / path.name).read_text(), "private sentinel")
            self.assertEqual((parent / "original" / path.name).read_text(), "Date\n1962\n")

    @unittest.skipUnless(os.name == "posix", "POSIX owning group")
    def test_overwrite_preserves_restricted_group(self):
        groups = [group for group in os.getgroups() if group != os.getgid()]
        if not groups:
            self.skipTest("No supplementary group available")
        for script in SCRIPTS:
            boundary = load_export_boundary(script)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "output.csv"
                path.write_text("original")
                os.chown(path, os.getuid(), groups[0])
                path.chmod(0o640)
                boundary["save_dataframe"](pd.DataFrame({"Date": ["1962"]}), path)
                self.assertEqual(path.stat().st_gid, groups[0])
                self.assertEqual(path.stat().st_uid, os.getuid())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_gui_retry_and_cancel_contract(self):
        gui = load_gui(SCRIPTS[0])
        class ImmediateCallbacks:
            def after(self, _delay, callback, *args):
                callback(*args)
        df = pd.DataFrame({"Date": ["1962"]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.csv"
            real_save = gui.save_dataframe
            attempts = []

            def locked_then_save(frame, target, expected_directory=None):
                attempts.append(target)
                if len(attempts) == 1:
                    raise PermissionError("file in use")
                real_save(frame, target, expected_directory)

            with patch.object(gui, "save_dataframe", side_effect=locked_then_save):
                with patch.object(gui.messagebox, "askretrycancel", return_value=True):
                    gui.DateFormatterApp._save_with_retry(ImmediateCallbacks(), df, str(path))
            self.assertEqual(len(attempts), 2)
            self.assertIn("1962", path.read_text())
            with patch.object(gui, "save_dataframe", side_effect=PermissionError("file in use")):
                with patch.object(gui.messagebox, "askretrycancel", return_value=False):
                    with self.assertRaisesRegex(RuntimeError, "Save cancelled"):
                        gui.DateFormatterApp._save_with_retry(ImmediateCallbacks(), df, str(path))

    @unittest.skipUnless(os.name == "nt", "Native Windows handle publication")
    def test_windows_staged_handle_is_exclusive_and_directory_bound(self):
        boundary = load_export_boundary(SCRIPTS[0])
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            selected = parent / "selected"
            selected.mkdir()
            location = boundary["OutputDirectory"](selected / "output.csv")
            fd = None
            moved = parent / "original"
            swapped = False
            try:
                fd = location.windows.open_file("staged.tmp", create=True)
                os.write(fd, b"Date\n1962\n")
                with self.assertRaises(PermissionError):
                    (selected / "staged.tmp").unlink()
                try:
                    selected.rename(moved)
                except OSError:
                    pass  # Some Windows filesystems pin the ancestor while a child is open.
                else:
                    swapped = True
                    selected.mkdir()
                    (selected / "output.csv").write_text("private sentinel")
                location.windows.publish(fd, "output.csv")
            finally:
                if fd is not None:
                    os.close(fd)
                location.close()
            if swapped:
                self.assertEqual((selected / "output.csv").read_text(), "private sentinel")
            actual = moved if swapped else selected
            self.assertEqual((actual / "output.csv").read_text(), "Date\n1962\n")


class TestParenthesisRemoval(unittest.TestCase):
    def test_preserves_existing_short_input_semantics(self):
        cases = [
            "1962 (estimated)", "(a(b)c)", "1962 (unclosed",
            "1962\t(notes)\n1970", "before\n (estimated)1962",
            "(first\n(second)1962", "1962 (a)\r(b)", "(())", "plain text",
        ]
        for script in SCRIPTS:
            strip = load_export_boundary(script)["strip_parenthetical_notes"]
            for raw in cases:
                with self.subTest(script=script.name, raw=raw):
                    self.assertEqual(strip(raw), re.sub(r"\s*\(.*?\)", "", raw))

    def test_large_malformed_input_finishes_with_bounded_execution(self):
        code = """
import sys
sys.path.insert(0, 'tests')
from test_security_regressions import SCRIPTS, load_export_boundary
for script in SCRIPTS:
    strip = load_export_boundary(script)['strip_parenthetical_notes']
    raw = '(' * 200000
    assert strip(raw) == raw
    assert strip(raw + ')1962') == '1962'
"""
        subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True, timeout=10)


class TestPrivateLogging(unittest.TestCase):
    def tearDown(self):
        logger = logging.getLogger()
        for handler in list(logger.handlers):
            if getattr(handler, "_date_formatter", False):
                logger.removeHandler(handler)
                handler.close()

    def test_parser_import_does_not_open_a_log(self):
        for script in SCRIPTS[:2]:
            with patch("logging.handlers.RotatingFileHandler.__init__",
                       side_effect=AssertionError("import attempted log opening")):
                gui = load_gui(script)
            self.assertEqual(gui.LOG_PATH, "")

    def test_unavailable_or_unsafe_log_path_is_nonfatal(self):
        gui = load_gui(SCRIPTS[0])
        with patch.object(gui.os, "makedirs", side_effect=PermissionError("denied")):
            gui.configure_logging("unavailable")
        self.assertEqual(gui.LOG_PATH, "")
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            sentinel = directory / "sentinel"
            sentinel.write_text("unchanged sentinel")
            log_directory = directory / "logs"
            log_directory.mkdir()
            log_path = log_directory / "date-formatter.log"
            log_path.symlink_to(sentinel)
            gui.configure_logging(log_directory)
            self.assertEqual(gui.LOG_PATH, "")
            self.assertEqual(sentinel.read_text(), "unchanged sentinel")
            log_path.unlink()
            log_path.mkdir()
            gui.configure_logging(log_directory)
            self.assertEqual(gui.LOG_PATH, "")
            log_path.rmdir()
            if hasattr(os, "mkfifo"):
                os.mkfifo(log_path)
                gui.configure_logging(log_directory)
                self.assertEqual(gui.LOG_PATH, "")

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits")
    def test_rotation_keeps_private_permissions_and_one_handler(self):
        gui = load_gui(SCRIPTS[0])
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for _ in range(2):
                gui.configure_logging(directory)
            own_handlers = [h for h in logging.getLogger().handlers
                            if getattr(h, "_date_formatter", False)]
            self.assertEqual(len(own_handlers), 1)
            with patch.object(gui, "LOG_MAX_BYTES", 100):
                gui.configure_logging(directory)
            for _ in range(5):
                logging.info("rotation control " + "x" * 80)
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            for path in directory.glob("date-formatter.log*"):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertTrue((directory / "date-formatter.log.1").exists())

    def test_gui_development_and_deployment_copies_match(self):
        self.assertEqual(SCRIPTS[0].read_bytes(), SCRIPTS[1].read_bytes())


if __name__ == "__main__":
    unittest.main()
