"""Unit tests for fnInjectSeedIntoVspaceFile."""

from vconverge.vconverge import fnInjectSeedIntoVspaceFile

from .conftest import fnWriteVspaceInputFile as fnWriteVspace


def flistReadAll(sPath):
    """Return the full contents of a text file as a list of lines."""
    with open(sPath, "r") as fileHandle:
        return fileHandle.readlines()


def test_inject_seed_prepends_seed_directive(tmp_path):
    """The output starts with `iSeed N` as the very first line."""
    sInPath = tmp_path / "in.vspace"
    sOutPath = tmp_path / "out.vspace"
    fnWriteVspace(sInPath, """
        sSrcFolder .
        sDestFolder dest
        sSampleMode random
        iNumTrials 2
        sTrialName t
        sBodyFile body.in
    """)
    fnInjectSeedIntoVspaceFile(str(sInPath), str(sOutPath), 17)
    listLines = flistReadAll(sOutPath)
    assert listLines[0] == "iSeed 17\n"


def test_inject_seed_strips_existing_seed_lines(tmp_path):
    """Pre-existing iSeed and seed lines are removed from the body."""
    sInPath = tmp_path / "in.vspace"
    sOutPath = tmp_path / "out.vspace"
    fnWriteVspace(sInPath, """
        iSeed 999
        seed 123
        sSrcFolder .
        sDestFolder dest
        sSampleMode random
        iNumTrials 2
        sTrialName t
        sBodyFile body.in
    """)
    fnInjectSeedIntoVspaceFile(str(sInPath), str(sOutPath), 5)
    sJoined = "".join(flistReadAll(sOutPath))
    assert sJoined.count("iSeed") == 1
    assert "iSeed 5" in sJoined
    assert "iSeed 999" not in sJoined
    assert "seed 123" not in sJoined


def test_inject_seed_preserves_body_block_verbatim(tmp_path):
    """Lines inside the file vpl.in block are preserved verbatim."""
    sInPath = tmp_path / "in.vspace"
    sOutPath = tmp_path / "out.vspace"
    fnWriteVspace(sInPath, """
        sSrcFolder .
        sDestFolder dest
        sSampleMode random
        iNumTrials 2
        sTrialName trial
        sBodyFile body.in
        sPrimaryFile vpl.in

        dMass [-1.0, 0.05, g, max0] b_mass
    """)
    fnInjectSeedIntoVspaceFile(str(sInPath), str(sOutPath), 42)
    sJoined = "".join(flistReadAll(sOutPath))
    assert "dMass [-1.0, 0.05, g, max0] b_mass" in sJoined
    assert "sPrimaryFile vpl.in" in sJoined


def test_inject_seed_blank_lines_preserved(tmp_path):
    """Blank lines from the input are kept in the output."""
    sInPath = tmp_path / "in.vspace"
    sOutPath = tmp_path / "out.vspace"
    fnWriteVspace(sInPath, """
        sSrcFolder .

        sDestFolder dest
    """)
    fnInjectSeedIntoVspaceFile(str(sInPath), str(sOutPath), 1)
    listLines = flistReadAll(sOutPath)
    assert any(sLine.strip() == "" for sLine in listLines)
