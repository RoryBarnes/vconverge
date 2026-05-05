"""Run vconverge without iSeed to exercise the unseeded code path."""

import os
import textwrap

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


@require_tools
def test_unseeded_run_completes(tmp_path, monkeypatch, sBasicTestSourceDir):
    """A .vcnv with no iSeed line uses the (unseeded) vspace/multiplanet branch."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sVcnv = tmp_path / "noseed.vcnv"
    sVcnv.write_text(textwrap.dedent("""
        sVspaceFile ./testvspace.in
        iStepSize 2
        iMaxSteps 1
        sConvergenceMethod KS_statistic
        fConvergenceCondition 0.5
        iNumberOfConvergences 1

        sObjectFile testplanet.in

        saConverge final SurfWaterMass
    """).lstrip("\n"))
    monkeypatch.chdir(tmp_path)
    fnRunVconverge("noseed.vcnv")
    assert (tmp_path / "vconverge_results.txt").exists()
    assert (tmp_path / "Testing" / "Converged_Param_Dictionary.json").exists()
