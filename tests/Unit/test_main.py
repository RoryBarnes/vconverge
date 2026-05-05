"""Unit tests for the main() entry-point."""

import importlib
from unittest import mock

import pytest


vconvergeModule = importlib.import_module("vconverge.vconverge")


def test_main_no_args_exits_with_usage(capsys, monkeypatch):
    """When called with no arguments, main prints usage and exits 1."""
    monkeypatch.setattr(vconvergeModule.sys, "argv", ["vconverge"])
    with pytest.raises(SystemExit) as excinfo:
        vconvergeModule.main()
    assert excinfo.value.code == 1
    sCaptured = capsys.readouterr().out
    assert "Usage" in sCaptured


def test_main_dispatches_to_vconverge(monkeypatch):
    """When called with one argument, main forwards it to vconverge()."""
    monkeypatch.setattr(vconvergeModule.sys, "argv", ["vconverge", "foo.vcnv"])
    with mock.patch.object(vconvergeModule, "vconverge") as mockEntry:
        vconvergeModule.main()
        mockEntry.assert_called_once_with("foo.vcnv")
