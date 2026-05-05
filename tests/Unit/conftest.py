"""Shared fixtures and helpers for vconverge unit tests.

The plain functions defined here (e.g. fnPrepareTmpDirectory,
fnWriteVspaceInputFile) are imported directly by individual test
modules via `from .conftest import ...`.  The `@pytest.fixture`
helpers below are auto-injected by pytest when a test names them
as an argument.  Keeping both kinds in one file removes duplication
across the unit-test suite.
"""

import os
import textwrap

import pytest


def fnWriteText(sPath, sContent):
    """Write a text file with leading whitespace dedented."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent(sContent).lstrip("\n"))


def fnWriteVspaceInputFile(sPath, sContent):
    """Write a vspace.in file with dedented content."""
    fnWriteText(sPath, sContent)


def fnPrepareTmpDirectory(sChdirPath):
    """Ensure vconverge_tmp/ exists below sChdirPath before a write."""
    sTmp = os.path.join(sChdirPath, "vconverge_tmp")
    os.makedirs(sTmp, exist_ok=True)


@pytest.fixture
def fnWriter():
    """Expose fnWriteText to tests so they can build ad-hoc files."""
    return fnWriteText


@pytest.fixture
def sMinimalVcnv(tmp_path, fnWriter):
    """Write a minimal .vcnv file and return its path as a string."""
    sVspacePath = tmp_path / "vspace.in"
    fnWriter(sVspacePath, "sSrcFolder .\n")
    sVcnvPath = tmp_path / "vc.vcnv"
    fnWriter(
        sVcnvPath,
        f"""
        sVspaceFile {sVspacePath}
        iStepSize 5
        iMaxSteps 3
        sConvergenceMethod KS_pval
        fConvergenceCondition 0.05
        iNumberOfConvergences 2

        sObjectFile body.in
        saConverge final SurfWaterMass
        saConverge initial OxygenMass
        """,
    )
    return str(sVcnvPath)


@pytest.fixture
def sCompleteLog(tmp_path, fnWriter):
    """A vplanet-style log file with both INITIAL and FINAL sections."""
    sLogPath = tmp_path / "system.log"
    fnWriter(
        sLogPath,
        """
        -------- Log file system.log --------

        ---- INITIAL SYSTEM PROPERTIES ----

        ----- BODY: planet ----
        Module: AtmEsc
        (SurfWaterMass) Surface water mass [TO]: 20.000000
        (OxygenMass) Oxygen mass in the atmosphere [bars]: 0.000000

        ---- FINAL SYSTEM PROPERTIES ----

        ----- BODY: planet ----
        Module: AtmEsc
        (SurfWaterMass) Surface water mass [TO]: 0.044449
        (OxygenMass) Oxygen mass in the atmosphere [bars]: 1415.425798
        """,
    )
    return str(sLogPath)


@pytest.fixture
def sIncompleteLog(tmp_path, fnWriter):
    """A log file that is missing its FINAL section."""
    sLogPath = tmp_path / "incomplete.log"
    fnWriter(
        sLogPath,
        """
        -------- Log file --------

        ---- INITIAL SYSTEM PROPERTIES ----

        ----- BODY: planet ----
        (SurfWaterMass) Surface water mass [TO]: 20.000000
        """,
    )
    return str(sLogPath)
