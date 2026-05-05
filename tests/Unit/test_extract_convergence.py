"""Unit tests for fnExtractConvergenceValues."""

import textwrap

import numpy as np
import pytest

from vconverge.vconverge import fnExtractConvergenceValues


def flistBuildLog(sLogString):
    """Return readlines() output from a dedented multi-line string."""
    sClean = textwrap.dedent(sLogString).lstrip("\n")
    return [sLine + "\n" for sLine in sClean.split("\n")]


def test_extract_final_and_initial_values_for_one_body():
    """Both INITIAL and FINAL values are pushed onto the right dict keys."""
    listLines = flistBuildLog("""
        ---- INITIAL SYSTEM PROPERTIES ----
        ----- BODY: planet ----
        (SurfWaterMass) Surface water mass [TO]: 20.000000
        (OxygenMass) Oxygen mass [bars]: 0.000000
        ---- FINAL SYSTEM PROPERTIES ----
        ----- BODY: planet ----
        (SurfWaterMass) Surface water mass [TO]: 0.044449
        (OxygenMass) Oxygen mass [bars]: 1415.425798
    """)
    daBody = np.array(["planet", "planet", "planet", "planet"])
    daVariable = np.array(["(SurfWaterMass)", "(OxygenMass)", "(SurfWaterMass)", "(OxygenMass)"])
    daFinit = np.array(["final", "final", "initial", "initial"])
    listParams = [
        "planet,SurfWaterMass,final",
        "planet,OxygenMass,final",
        "planet,SurfWaterMass,initial",
        "planet,OxygenMass,initial",
    ]
    dictConverge = {sKey: [] for sKey in listParams}
    fnExtractConvergenceValues(listLines, daBody, daVariable, daFinit, listParams, dictConverge)
    assert dictConverge["planet,SurfWaterMass,final"] == [pytest.approx(0.044449)]
    assert dictConverge["planet,OxygenMass,final"] == [pytest.approx(1415.425798)]
    assert dictConverge["planet,SurfWaterMass,initial"] == [pytest.approx(20.0)]
    assert dictConverge["planet,OxygenMass,initial"] == [pytest.approx(0.0)]


def test_extract_skips_short_lines_and_unmatched_variables():
    """Lines with <=2 tokens and variables not in daVariable are ignored."""
    listLines = flistBuildLog("""
        ---- FINAL SYSTEM PROPERTIES ----
        short
        ----- BODY: planet ----
        (SurfWaterMass) Surface water mass [TO]: 0.5
        (NotTracked) Something else: 1.0
    """)
    daBody = np.array(["planet"])
    daVariable = np.array(["(SurfWaterMass)"])
    daFinit = np.array(["final"])
    listParams = ["planet,SurfWaterMass,final"]
    dictConverge = {"planet,SurfWaterMass,final": []}
    fnExtractConvergenceValues(listLines, daBody, daVariable, daFinit, listParams, dictConverge)
    assert dictConverge["planet,SurfWaterMass,final"] == [pytest.approx(0.5)]


def test_extract_does_not_mismatch_other_body():
    """A variable seen under a different body name is not credited to this body."""
    listLines = flistBuildLog("""
        ---- FINAL SYSTEM PROPERTIES ----
        ----- BODY: star ----
        (SurfWaterMass) Surface water mass [TO]: 99.0
    """)
    daBody = np.array(["planet"])
    daVariable = np.array(["(SurfWaterMass)"])
    daFinit = np.array(["final"])
    listParams = ["planet,SurfWaterMass,final"]
    dictConverge = {"planet,SurfWaterMass,final": []}
    fnExtractConvergenceValues(listLines, daBody, daVariable, daFinit, listParams, dictConverge)
    assert dictConverge["planet,SurfWaterMass,final"] == []
