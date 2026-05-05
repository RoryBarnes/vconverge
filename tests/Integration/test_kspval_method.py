"""Run vconverge with sConvergenceMethod KS_pval to exercise that branch."""

import json
import os
import textwrap

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


@require_tools
def test_kspval_method_runs_to_completion(tmp_path, monkeypatch, sBasicTestSourceDir):
    """A KS_pval run produces vconverge_results.txt with KS P-Values text."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sVcnv = tmp_path / "kspval.vcnv"
    sVcnv.write_text(textwrap.dedent("""
        sVspaceFile ./testvspace.in
        iStepSize 2
        iMaxSteps 1
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.01
        iNumberOfConvergences 1
        iSeed 7

        sObjectFile testplanet.in

        saConverge final SurfWaterMass
        saConverge final OxygenMass
    """).lstrip("\n"))
    monkeypatch.chdir(tmp_path)
    fnRunVconverge("kspval.vcnv")
    sResults = (tmp_path / "vconverge_results.txt").read_text()
    assert "KS P-Values" in sResults
