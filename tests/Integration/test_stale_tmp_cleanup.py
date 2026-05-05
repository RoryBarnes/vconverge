"""Confirm vconverge cleans up stale vconverge_tmp/ and .vconverge_tmp/ dirs."""

import os

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


@require_tools
def test_stale_tmp_dirs_are_replaced(tmp_path, monkeypatch, sBasicTestSourceDir):
    """Pre-existing vconverge_tmp/ and .vconverge_tmp/ are wiped before a fresh run."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sStale = tmp_path / "vconverge_tmp"
    sStaleHidden = tmp_path / ".vconverge_tmp"
    sStale.mkdir()
    sStaleHidden.mkdir()
    (sStale / "stale_marker.txt").write_text("leftover")
    (sStaleHidden / "stale_marker.txt").write_text("leftover")
    monkeypatch.chdir(tmp_path)
    fnRunVconverge("testvconverge.in")
    # vconverge recreates vconverge_tmp/, so the stale marker inside must be gone.
    assert not (sStale / "stale_marker.txt").exists()
    # The .vconverge_tmp marker is wiped before the run; multiplanet may
    # later create its own checkpoint dir of the same name, but our marker
    # file from the prior run must not survive.
    assert not (sStaleHidden / "stale_marker.txt").exists()
