"""Shared helpers and skip conditions for vconverge integration tests."""

import os
import shutil

import pytest


def fbToolsAvailable():
    """Return True if vplanet, vspace, multiplanet, and vconverge are on PATH."""
    return all(
        shutil.which(sName) is not None
        for sName in ("vplanet", "vspace", "multiplanet", "vconverge")
    )


# Tests that need the real binaries are skipped automatically when the
# binaries are not on PATH (e.g., on a stripped-down CI matrix).
require_tools = pytest.mark.skipif(
    not fbToolsAvailable(),
    reason="vplanet/vspace/multiplanet/vconverge must be on PATH",
)


def fnCleanRunArtifacts(sRunDirectory):
    """Remove artifacts produced by a previous vconverge run inside sRunDirectory."""
    listTargets = [
        "Testing",
        "vconverge_tmp",
        ".vconverge_tmp",
        "vconverge_results.txt",
    ]
    for sTarget in listTargets:
        sFullPath = os.path.join(sRunDirectory, sTarget)
        if os.path.isdir(sFullPath):
            shutil.rmtree(sFullPath)
        elif os.path.isfile(sFullPath):
            os.remove(sFullPath)


def fnStageInputFiles(sSourceDirectory, sDestinationDirectory):
    """Copy the four input files vconverge needs into a fresh working directory."""
    listInputs = ("vpl.in", "star.in", "testplanet.in", "testvspace.in", "testvconverge.in")
    for sName in listInputs:
        shutil.copy(os.path.join(sSourceDirectory, sName), sDestinationDirectory)


@pytest.fixture
def sBasicTestSourceDir():
    """Return the absolute path to the canonical BasicTest input fixtures."""
    return os.path.join(os.path.dirname(__file__), "BasicTest")
