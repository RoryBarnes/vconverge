"""Unit tests for create_tmp_vspin."""

import pytest

from vconverge.vconverge import create_tmp_vspin

from .conftest import fnPrepareTmpDirectory, fnWriteVspaceInputFile as fnWriteVspace


def test_create_tmp_vspin_legacy_keywords(tmp_path, monkeypatch):
    """Legacy keywords (destfolder, randsize) are rewritten with the right step index."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        srcfolder .
        destfolder MyDest
        samplemode random
        randsize 5
        trialname myTrial
        file body.in
    """)
    bUsesPriors = create_tmp_vspin(str(sVspace), 2, 7)
    assert bUsesPriors is False
    sOut = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text()
    assert "destfolder vconverge_tmp/Step_2" in sOut
    assert "randsize 7" in sOut
    assert "trialname Step2_myTrial" in sOut


def test_create_tmp_vspin_modern_keywords(tmp_path, monkeypatch):
    """Modern keywords (sDestFolder, iNumTrials) are rewritten with the right step index."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        sSrcFolder .
        sDestFolder MyDest
        sSampleMode random
        iNumTrials 5
        sTrialName trial
        sBodyFile body.in
    """)
    create_tmp_vspin(str(sVspace), 3, 9)
    sOut = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text()
    assert "sDestFolder vconverge_tmp/Step_3" in sOut
    assert "iNumTrials 9" in sOut
    assert "sTrialName Step3_trial" in sOut


def test_create_tmp_vspin_seeded_writes_iseed_first(tmp_path, monkeypatch):
    """When iBaseSeed is given, iSeed is the first line, offset by RunIndex."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        iSeed 1234
        sSrcFolder .
        sDestFolder MyDest
        sSampleMode random
        iNumTrials 5
        sTrialName trial
        sBodyFile body.in
    """)
    create_tmp_vspin(str(sVspace), 4, 8, iBaseSeed=100)
    listLines = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text().splitlines()
    assert listLines[0] == "iSeed 104"
    assert all("iSeed 1234" not in sLine for sLine in listLines[1:])


def test_create_tmp_vspin_unseeded_does_not_write_iseed(tmp_path, monkeypatch):
    """When iBaseSeed is None, no iSeed line is added at the top."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        sSrcFolder .
        sDestFolder MyDest
        sSampleMode random
        iNumTrials 5
        sTrialName trial
        sBodyFile body.in
    """)
    create_tmp_vspin(str(sVspace), 1, 4)
    sOut = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text()
    assert "iSeed" not in sOut


def test_create_tmp_vspin_predefined_priors_flag(tmp_path, monkeypatch):
    """A `[..., p, ...]` predefined-prior line flips the return flag and rewrites the path."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        sSrcFolder .
        sDestFolder MyDest
        sSampleMode random
        iNumTrials 5
        sTrialName trial
        sBodyFile body.in
        dMass [priors/mass.npy, b_mass, p, 1] mass_label
    """)
    bUsesPriors = create_tmp_vspin(str(sVspace), 1, 6)
    assert bUsesPriors is True
    sOut = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text()
    assert "vconverge_tmp/tmp_mass.npy" in sOut


def test_create_tmp_vspin_non_p_bracket_passes_through(tmp_path, monkeypatch):
    """A bracket line whose third value is not 'p' is written verbatim."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sVspace = tmp_path / "in.vspace"
    fnWriteVspace(sVspace, """
        sSrcFolder .
        sDestFolder MyDest
        sSampleMode random
        iNumTrials 3
        sTrialName trial
        sBodyFile body.in
        dMass [-1.0, 0.05, g, max0] b_mass
    """)
    bUsesPriors = create_tmp_vspin(str(sVspace), 1, 3)
    assert bUsesPriors is False
    sOut = (tmp_path / "vconverge_tmp" / "vspace_tmp.in").read_text()
    assert "dMass [-1.0, 0.05, g, max0] b_mass" in sOut
