"""Cover the 'produced no values' guard after the initial run."""

import textwrap

import pytest

from vconverge.vconverge import vconverge as fnRunVconverge

from .conftest import fnCleanRunArtifacts, fnStageInputFiles, require_tools


def fnWriteMisspelledVcnv(sPath, sVspaceRel):
    """Write a vconverge input whose saConverge parameter does not appear in any log."""
    sBody = """
        sVspaceFile {sVspaceRel}
        iStepSize 1
        iMaxSteps 1
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.5
        iNumberOfConvergences 1
        iSeed 7

        sObjectFile testplanet.in
        saConverge final NotARealParameter
    """.format(sVspaceRel=sVspaceRel)
    sPath.write_text(textwrap.dedent(sBody).lstrip("\n"))


@require_tools
def test_misspelled_converge_param_raises(tmp_path, monkeypatch, sBasicTestSourceDir):
    """When no log lines match any saConverge parameter, vconverge raises IOError."""
    fnStageInputFiles(sBasicTestSourceDir, str(tmp_path))
    fnCleanRunArtifacts(str(tmp_path))
    sBadVcnv = tmp_path / "bad.vcnv"
    fnWriteMisspelledVcnv(sBadVcnv, "./testvspace.in")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(IOError, match="produced no values"):
        fnRunVconverge("bad.vcnv")
