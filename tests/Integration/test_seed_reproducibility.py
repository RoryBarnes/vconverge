"""Verify that two vconverge runs with the same iSeed produce identical posteriors."""

import json
import os

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import (
    fnCleanRunArtifacts,
    fnStageInputFiles,
    require_tools,
)


def fdictRunInDirectory(sWorkingDir):
    """Run vconverge in-process inside sWorkingDir and return the converge dictionary."""
    sOriginalCwd = os.getcwd()
    try:
        os.chdir(sWorkingDir)
        fnRunVconverge("testvconverge.in")
    finally:
        os.chdir(sOriginalCwd)
    with open(os.path.join(sWorkingDir, "Testing", "Converged_Param_Dictionary.json"), "r") as f:
        return json.loads(json.load(f))


@require_tools
def test_same_seed_yields_identical_posteriors(tmp_path, sBasicTestSourceDir):
    """Same iSeed in two isolated dirs gives bit-identical converge dictionaries."""
    sFirstDir = tmp_path / "first"
    sSecondDir = tmp_path / "second"
    sFirstDir.mkdir()
    sSecondDir.mkdir()
    fnStageInputFiles(sBasicTestSourceDir, str(sFirstDir))
    fnStageInputFiles(sBasicTestSourceDir, str(sSecondDir))
    fnCleanRunArtifacts(str(sFirstDir))
    fnCleanRunArtifacts(str(sSecondDir))
    dictFirst = fdictRunInDirectory(str(sFirstDir))
    dictSecond = fdictRunInDirectory(str(sSecondDir))
    assert dictFirst.keys() == dictSecond.keys()
    for sKey in dictFirst:
        assert dictFirst[sKey] == pytest.approx(dictSecond[sKey], rel=0, abs=0)
