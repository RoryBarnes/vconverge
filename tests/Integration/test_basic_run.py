"""End-to-end integration test for the vconverge driver.

Runs the vconverge() Python entry point in-process so coverage of
vconverge.py is captured. The vspace and multiplanet binaries are
still invoked as subprocesses by the source code under test.
"""

import json
import os
import subprocess

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import (
    fnCleanRunArtifacts,
    fnStageInputFiles,
    require_tools,
)


@require_tools
def test_basic_run_completes_and_writes_outputs(tmp_path, monkeypatch, sBasicTestSourceDir):
    """vconverge BasicTest runs to MaxSteps and writes the expected files."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    monkeypatch.chdir(tmp_path)
    fnRunVconverge("testvconverge.in")
    assert (tmp_path / "vconverge_results.txt").exists()
    sJsonPath = tmp_path / "Testing" / "Converged_Param_Dictionary.json"
    assert sJsonPath.exists()
    with open(sJsonPath, "r") as fileHandle:
        sStored = json.load(fileHandle)
    dictParsed = json.loads(sStored)
    assert "planet,SurfWaterMass,final" in dictParsed
    assert "planet,OxygenMass,final" in dictParsed
    assert len(dictParsed["planet,SurfWaterMass,final"]) > 0


@require_tools
def test_basic_run_via_cli_entry_point(tmp_path, sBasicTestSourceDir):
    """vconverge invoked as a CLI subprocess exits 0 (smoke test for the entry point)."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    completed = subprocess.run(
        ["vconverge", "testvconverge.in"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "vconverge_results.txt").exists()
