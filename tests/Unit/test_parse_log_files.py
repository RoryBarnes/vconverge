"""Unit tests for ftParseLogFiles."""

import os
import textwrap

import numpy as np
import pytest

from vconverge.vconverge import ftParseLogFiles


def fnWriteValidLog(sPath, fSurfWater):
    """Write a complete log with FINAL/BODY/SurfWaterMass lines."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent(f"""
            ---- INITIAL SYSTEM PROPERTIES ----
            ----- BODY: planet ----
            (SurfWaterMass) Surface water mass [TO]: 20.000000
            ---- FINAL SYSTEM PROPERTIES ----
            ----- BODY: planet ----
            (SurfWaterMass) Surface water mass [TO]: {fSurfWater:.6f}
        """).lstrip("\n"))


def fnWriteIncompleteLog(sPath):
    """Write a log without a FINAL section."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent("""
            ---- INITIAL SYSTEM PROPERTIES ----
            ----- BODY: planet ----
            (SurfWaterMass) Surface water mass [TO]: 20.000000
        """).lstrip("\n"))


def fnPrepareSimTree(sBaseDir, sLogName):
    """Build three subdirs: two with valid logs, one missing the FINAL section."""
    for iIndex, fValue in enumerate([0.5, 0.6]):
        sSubdir = os.path.join(sBaseDir, "trial_%d" % iIndex)
        os.makedirs(sSubdir)
        fnWriteValidLog(os.path.join(sSubdir, sLogName), fValue)
    sBadSubdir = os.path.join(sBaseDir, "trial_bad")
    os.makedirs(sBadSubdir)
    fnWriteIncompleteLog(os.path.join(sBadSubdir, sLogName))


def test_parse_log_files_counts_success_and_failure(tmp_path, capsys):
    """Two valid logs produce two successes; the incomplete log is counted as failed."""
    sBaseDir = tmp_path / "base"
    sBaseDir.mkdir()
    sLogName = "system.log"
    fnPrepareSimTree(str(sBaseDir), sLogName)
    daBody = np.array(["planet"])
    daVariable = np.array(["(SurfWaterMass)"])
    daFinit = np.array(["final"])
    listParams = ["planet,SurfWaterMass,final"]
    dictConverge = {listParams[0]: []}
    iSuccess, iFailed = ftParseLogFiles(
        str(sBaseDir), sLogName, daBody, daVariable, daFinit, listParams, dictConverge
    )
    assert iSuccess == 2
    assert iFailed == 1
    assert sorted(dictConverge[listParams[0]]) == [pytest.approx(0.5), pytest.approx(0.6)]
    sCaptured = capsys.readouterr().out
    assert "Skipping" in sCaptured


def test_parse_log_files_copies_to_destination(tmp_path):
    """When sDestDir is given, valid trial subdirs are copied there."""
    sBaseDir = tmp_path / "base"
    sBaseDir.mkdir()
    sDestDir = tmp_path / "dest"
    sDestDir.mkdir()
    sLogName = "system.log"
    sSubdir = sBaseDir / "trial_a"
    sSubdir.mkdir()
    fnWriteValidLog(str(sSubdir / sLogName), 0.42)
    daBody = np.array(["planet"])
    daVariable = np.array(["(SurfWaterMass)"])
    daFinit = np.array(["final"])
    listParams = ["planet,SurfWaterMass,final"]
    dictConverge = {listParams[0]: []}
    ftParseLogFiles(
        str(sBaseDir),
        sLogName,
        daBody,
        daVariable,
        daFinit,
        listParams,
        dictConverge,
        sDestDir=str(sDestDir),
    )
    assert (sDestDir / "trial_a" / sLogName).exists()
