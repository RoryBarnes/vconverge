"""Unit tests for extract_info_vcnv and extract_info_vsp."""

import os
import textwrap

import pytest

from vconverge.vconverge import extract_info_vcnv, extract_info_vsp


def fnBuildVcnv(sPath, sContent):
    """Write a .vcnv file with dedented content."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent(sContent).lstrip("\n"))


def fnBuildVsp(sPath, sContent):
    """Write a vspace.in file with dedented content."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent(sContent).lstrip("\n"))


def test_extract_info_vcnv_full_block(tmp_path):
    """Every keyword is parsed and lists of params build correctly."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile myvspace.in
        iStepSize 7
        iMaxSteps 4
        sConvergenceMethod KS_statistic
        fConvergenceCondition 0.0125
        iNumberOfConvergences 3
        iSeed 42

        sObjectFile planet.in
        saConverge final SurfWaterMass
        saConverge initial OxygenMass

        sObjectFile star.in
        saConverge final Luminosity
    """)
    tResult = extract_info_vcnv(str(sVcnv))
    sVsp, iStep, iMax, sMethod, fCond, iConvs, listParams, iSeed = tResult
    assert sVsp == "myvspace.in"
    assert iStep == 7
    assert iMax == 4
    assert sMethod == "KS_statistic"
    assert fCond == pytest.approx(0.0125)
    assert iConvs == 3
    assert iSeed == 42
    assert listParams[0] == ["planet.in", "SurfWaterMass,final", "OxygenMass,initial"]
    assert listParams[1] == ["star.in", "Luminosity,final"]


def test_extract_info_vcnv_seed_synonym(tmp_path):
    """The 'seed' synonym is accepted in place of 'iSeed'."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile vspace.in
        iStepSize 1
        iMaxSteps 1
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.1
        iNumberOfConvergences 1
        seed 13
        sObjectFile body.in
        saConverge final WaterMass
    """)
    _, _, _, _, _, _, _, iSeed = extract_info_vcnv(str(sVcnv))
    assert iSeed == 13


def test_extract_info_vcnv_non_integer_seed_raises(tmp_path):
    """Non-integer iSeed values raise IOError."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile vspace.in
        iStepSize 1
        iMaxSteps 1
        fConvergenceCondition 0.1
        iNumberOfConvergences 1
        iSeed 3.14
        sObjectFile body.in
        saConverge final WaterMass
    """)
    with pytest.raises(IOError, match="iSeed"):
        extract_info_vcnv(str(sVcnv))


def test_extract_info_vcnv_saconverge_wrong_arg_count(tmp_path):
    """saConverge with too few/many tokens raises IOError."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile vspace.in
        iStepSize 1
        iMaxSteps 1
        fConvergenceCondition 0.1
        iNumberOfConvergences 1
        sObjectFile body.in
        saConverge final SurfWaterMass extraToken
    """)
    with pytest.raises(IOError, match="saConverge"):
        extract_info_vcnv(str(sVcnv))


def test_extract_info_vcnv_saconverge_bad_qualifier(tmp_path):
    """saConverge qualifier other than initial/final raises IOError."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile vspace.in
        iStepSize 1
        iMaxSteps 1
        fConvergenceCondition 0.1
        iNumberOfConvergences 1
        sObjectFile body.in
        saConverge median SurfWaterMass
    """)
    with pytest.raises(IOError, match="initial/final"):
        extract_info_vcnv(str(sVcnv))


def test_extract_info_vcnv_saconverge_without_object_raises(tmp_path):
    """saConverge before any sObjectFile raises IOError."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """
        sVspaceFile vspace.in
        iStepSize 1
        iMaxSteps 1
        fConvergenceCondition 0.1
        iNumberOfConvergences 1
        saConverge final SurfWaterMass
    """)
    with pytest.raises(IOError, match="specify the body"):
        extract_info_vcnv(str(sVcnv))


def test_extract_info_vcnv_blank_lines_ignored(tmp_path):
    """Blank lines in the input file are silently ignored."""
    sVcnv = tmp_path / "vc.vcnv"
    fnBuildVcnv(sVcnv, """

        sVspaceFile vspace.in

        iStepSize 2
        iMaxSteps 2
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.1
        iNumberOfConvergences 1


        sObjectFile body.in
        saConverge final WaterMass

    """)
    _, _, _, _, _, _, listParams, _ = extract_info_vcnv(str(sVcnv))
    assert listParams == [["body.in", "WaterMass,final"]]


def test_extract_info_vsp_legacy_keywords(tmp_path):
    """Legacy keywords (srcfolder/destfolder/randsize/file/trialname) parse."""
    sVsp = tmp_path / "vspace.in"
    fnBuildVsp(sVsp, """
        srcfolder mysrc
        destfolder mydest
        samplemode random
        randsize 11
        trialname myTrial
        file body.in
    """)
    sSrc, sDest, sTrial, sPrime, iSize = extract_info_vsp(str(sVsp))
    assert sSrc == "mysrc"
    assert sDest == "mydest"
    assert sTrial == "myTrial"
    assert sPrime == "vpl.in"
    assert iSize == 11


def test_extract_info_vsp_modern_keywords(tmp_path):
    """Modern keywords (sSrcFolder/sDestFolder/...) parse and respect sPrimaryFile."""
    sVsp = tmp_path / "vspace.in"
    fnBuildVsp(sVsp, """
        sSrcFolder src2
        sDestFolder dest2
        sSampleMode random
        iNumTrials 4
        sTrialName trial2
        sBodyFile body.in
        sPrimaryFile vpl_custom.in
    """)
    sSrc, sDest, sTrial, sPrime, iSize = extract_info_vsp(str(sVsp))
    assert sSrc == "src2"
    assert sDest == "dest2"
    assert sTrial == "trial2"
    assert sPrime == "vpl_custom.in"
    assert iSize == 4


def test_extract_info_vsp_dot_srcfolder_uses_cwd(tmp_path, monkeypatch):
    """srcfolder '.' is expanded to the current working directory."""
    monkeypatch.chdir(tmp_path)
    sVsp = tmp_path / "vspace.in"
    fnBuildVsp(sVsp, """
        sSrcFolder .
        sDestFolder dest
        sSampleMode random
        iNumTrials 2
        sTrialName t
        sBodyFile body.in
    """)
    sSrc, _, _, _, _ = extract_info_vsp(str(sVsp))
    assert sSrc == os.getcwd()


def test_extract_info_vsp_non_random_mode_raises(tmp_path):
    """A non-random sample mode raises IOError."""
    sVsp = tmp_path / "vspace.in"
    fnBuildVsp(sVsp, """
        sSrcFolder .
        sDestFolder d
        sSampleMode grid
        iNumTrials 2
        sTrialName t
        sBodyFile body.in
    """)
    with pytest.raises(IOError, match="random"):
        extract_info_vsp(str(sVsp))


def test_extract_info_vsp_blank_lines_ignored(tmp_path):
    """Blank lines do not break parsing."""
    sVsp = tmp_path / "vspace.in"
    fnBuildVsp(sVsp, """

        sSrcFolder src

        sDestFolder dest
        sSampleMode random
        iNumTrials 3
        sTrialName t
        sBodyFile body.in

    """)
    _, sDest, _, _, iSize = extract_info_vsp(str(sVsp))
    assert sDest == "dest"
    assert iSize == 3
