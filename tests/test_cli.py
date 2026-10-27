"""Tests for the extended-wer-normalizer command-line interface."""

import io
import os
import subprocess
import sys

import pytest

from extended_wer_normalizer.cli import main


class _TtyStdin:
    """Stand-in for an interactive terminal: no piped input, must not be read."""

    def isatty(self) -> bool:
        return True

    def read(self, *args: object) -> str:
        raise AssertionError("stdin must not be read in this mode")

    def __iter__(self):
        raise AssertionError("stdin must not be iterated in this mode")


@pytest.fixture
def tty_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _TtyStdin())


def test_positional_text(tty_stdin, capsys):
    assert main(["Call 0176 or email info@example.com"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "call 0 1 7 6 or email info at example dot com\n"
    assert captured.err == ""


def test_positional_text_with_language(tty_stdin, capsys):
    assert main(["Hr. Müller, am 1. Januar", "--language", "de"]) == 0
    assert capsys.readouterr().out == "herr müller am erste januar\n"


def test_stdin_line_by_line(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("Call 0176\nUm, yes yes yes yes\n\n"))
    assert main([]) == 0
    assert capsys.readouterr().out == "call 0 1 7 6\nyes\n\n"


def test_stdin_without_trailing_newline(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("Call 0176"))
    assert main([]) == 0
    assert capsys.readouterr().out == "call 0 1 7 6"


def test_file_input(tty_stdin, tmp_path, capsys):
    path = tmp_path / "transcripts.txt"
    path.write_text("Call 0176\nDr. Smith\n", encoding="utf-8")
    assert main(["--file", str(path)]) == 0
    assert capsys.readouterr().out == "call 0 1 7 6\ndoctor smith\n"


def test_conflicting_inputs_are_usage_error(tty_stdin, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["some text", "--file", "transcripts.txt"])
    assert excinfo.value.code == 2
    assert "only one" in capsys.readouterr().err


def test_explicit_input_wins_over_piped_stdin(monkeypatch, capsys):
    """TEXT + piped stdin is not a conflict: the explicit argument is used."""
    monkeypatch.setattr(sys, "stdin", io.StringIO("piped input\n"))
    assert main(["Call 0176"]) == 0
    assert capsys.readouterr().out == "call 0 1 7 6\n"


def test_no_input_is_usage_error(tty_stdin, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_describe_needs_no_input(tty_stdin, capsys):
    assert main(["--describe"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "NormalizeEmails"
    assert "ToLowerCase" in lines
    assert "SplitHyphenatedWords" in lines
    assert lines[-1] == "CollapseRepetitions"


def test_describe_german_differs_from_english(tty_stdin, capsys):
    assert main(["--describe", "-l", "de"]) == 0
    de_lines = capsys.readouterr().out.splitlines()
    assert "ExpandCommonEnglishContractions" not in de_lines
    assert "ExpandFrenchElisions" not in de_lines


def test_list_languages(tty_stdin, capsys):
    assert main(["--list-languages"]) == 0
    out = capsys.readouterr().out
    for code in ("de", "en", "fr"):
        assert code in out.splitlines()
    assert "falls back" in out


def test_list_languages_ignores_language_flag(tty_stdin, capsys):
    """--list-languages normalizes nothing, so an unknown -l is not reported."""
    assert main(["--list-languages", "-l", "xx"]) == 0
    assert capsys.readouterr().err == ""


def test_pipeline_built_once_per_run(monkeypatch, capsys):
    """Custom --max-repeats builds a one-off pipeline, but only once per run."""
    from extended_wer_normalizer import cli

    calls = []
    real_get_pipeline = cli.get_pipeline

    def counting_get_pipeline(*args, **kwargs):
        calls.append(args)
        return real_get_pipeline(*args, **kwargs)

    monkeypatch.setattr(cli, "get_pipeline", counting_get_pipeline)
    monkeypatch.setattr(sys, "stdin", io.StringIO("no no no\nyes yes yes\nok\n"))
    assert main(["--max-repeats", "1", "-l", "xx"]) == 0
    assert capsys.readouterr().out == "no\nyes\nok\n"
    assert len(calls) == 1


def test_stdin_decoded_as_utf8_regardless_of_locale():
    """Piped bytes are read as UTF-8 even when the platform default differs."""
    result = subprocess.run(
        [sys.executable, "-m", "extended_wer_normalizer", "-l", "de"],
        input="Hr. Müller, ähm\n".encode(),
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.decode("utf-8") == "herr müller\n"


def test_unknown_language_falls_back_with_notice(tty_stdin, capsys):
    assert main(["¡Hola, mundo!", "-l", "es"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "hola mundo\n"
    assert "'es'" in captured.err
    assert "fallback" in captured.err


def test_max_repeats_passthrough(tty_stdin, capsys):
    assert main(["no no no", "--max-repeats", "1"]) == 0
    assert capsys.readouterr().out == "no\n"


def test_max_repeats_rejects_zero(tty_stdin, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["no no no", "--max-repeats", "0"])
    assert excinfo.value.code == 2
    assert "--max-repeats" in capsys.readouterr().err


def test_missing_file_is_runtime_error(tty_stdin, capsys):
    assert main(["--file", "/nonexistent/transcripts.txt"]) == 1
    assert capsys.readouterr().err != ""


def test_python_module_invocation():
    result = subprocess.run(
        [sys.executable, "-m", "extended_wer_normalizer", "Call 0176"],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "call 0 1 7 6\n"
