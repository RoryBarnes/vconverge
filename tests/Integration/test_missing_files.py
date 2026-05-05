"""Confirm vconverge raises a clear error when sObjectFile is missing."""

import os
import textwrap

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


@require_tools
def test_missing_object_file_raises(tmp_path, monkeypatch, sBasicTestSourceDir):
    """Pointing sObjectFile at a nonexistent body file aborts with IOError."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sBadVcnv = tmp_path / "bad.vcnv"
    sBadVcnv.write_text(textwrap.dedent("""
        sVspaceFile ./testvspace.in
        iStepSize 1
        iMaxSteps 1
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.5
        iNumberOfConvergences 1

        sObjectFile does_not_exist.in
        saConverge final SurfWaterMass
    """).lstrip("\n"))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(IOError, match="does_not_exist.in"):
        fnRunVconverge("bad.vcnv")


@require_tools
def test_missing_primary_file_raises(tmp_path, monkeypatch, sBasicTestSourceDir):
    """An sPrimaryFile that does not exist aborts with IOError."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sBadVspace = tmp_path / "bad_vspace.in"
    sBadVspace.write_text(textwrap.dedent("""
        sSrcFolder .
        sDestFolder Testing
        sTrialName BasicTest
        sSampleMode random
        iNumTrials 2

        sBodyFile testplanet.in
        sBodyFile star.in

        sPrimaryFile no_such_vpl.in
    """).lstrip("\n"))
    sBadVcnv = tmp_path / "bad.vcnv"
    sBadVcnv.write_text(textwrap.dedent("""
        sVspaceFile ./bad_vspace.in
        iStepSize 1
        iMaxSteps 1
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.5
        iNumberOfConvergences 1

        sObjectFile testplanet.in
        saConverge final SurfWaterMass
    """).lstrip("\n"))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(IOError, match="no_such_vpl.in"):
        fnRunVconverge("bad.vcnv")
