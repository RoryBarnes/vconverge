"""Run vconverge with permissive thresholds so the loop converges before MaxSteps."""

import textwrap

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


@require_tools
def test_loop_exits_before_max_steps(tmp_path, monkeypatch, sBasicTestSourceDir):
    """A KS_pval threshold of 0 always passes, so the loop exits at step 1."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sVcnv = tmp_path / "early.vcnv"
    sVcnv.write_text(textwrap.dedent("""
        sVspaceFile ./testvspace.in
        iStepSize 2
        iMaxSteps 5
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.0
        iNumberOfConvergences 1
        iSeed 11

        sObjectFile testplanet.in

        saConverge final SurfWaterMass
    """).lstrip("\n"))
    monkeypatch.chdir(tmp_path)
    fnRunVconverge("early.vcnv")
    sResults = (tmp_path / "vconverge_results.txt").read_text()
    assert "vconverge run sucessful" in sResults
