"""Shared fixtures for vconverge unit tests.

These fixtures build small in-memory inputs (vconverge `.in` files,
vspace `.in` files, body files, vplanet log files) that the unit
tests below reuse. Keeping them here keeps each test file short.
"""

import os
import textwrap

import pytest


def fnWriteText(sPath, sContent):
    """Write a text file (helper used by many fixtures)."""
    with open(sPath, "w") as fileHandle:
        fileHandle.write(textwrap.dedent(sContent).lstrip("\n"))


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
