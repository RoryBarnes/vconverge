"""Unit tests for the small log-file helper functions."""

import os

import numpy as np
import pytest

from vconverge.vconverge import (
    fbCheckLogFileComplete,
    fiMatchBodyAndFinitIndex,
    flistReadValidLogFile,
)


def test_fb_check_log_file_complete_true(sCompleteLog):
    """A log containing a FINAL section returns True."""
    assert fbCheckLogFileComplete(sCompleteLog) is True


def test_fb_check_log_file_complete_false(sIncompleteLog):
    """A log without a FINAL section returns False."""
    assert fbCheckLogFileComplete(sIncompleteLog) is False


def test_flist_read_valid_log_file_returns_lines(sCompleteLog):
    """A complete log returns its lines as a list."""
    listLines = flistReadValidLogFile(sCompleteLog)
    assert isinstance(listLines, list)
    assert any("FINAL" in sLine for sLine in listLines)


def test_flist_read_valid_log_file_incomplete_raises(sIncompleteLog):
    """An incomplete log raises IOError mentioning the FINAL section."""
    with pytest.raises(IOError, match="FINAL"):
        flistReadValidLogFile(sIncompleteLog)


def test_flist_read_valid_log_file_missing_raises(tmp_path):
    """A nonexistent log file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        flistReadValidLogFile(str(tmp_path / "does_not_exist.log"))


def test_fi_match_body_and_finit_index_match():
    """When the requested body and finit appear at the same array slot, the index is returned."""
    daBody = np.array(["planet", "planet", "star"])
    daFinit = np.array(["final", "initial", "final"])
    daIndex = np.array([0, 1, 2])
    iResult = fiMatchBodyAndFinitIndex(daBody, daFinit, "planet", "final", daIndex)
    assert iResult == 0


def test_fi_match_body_and_finit_index_no_body_match():
    """If the body name is absent at the candidate indices, None is returned."""
    daBody = np.array(["planet", "star"])
    daFinit = np.array(["final", "final"])
    daIndex = np.array([0, 1])
    iResult = fiMatchBodyAndFinitIndex(daBody, daFinit, "moon", "final", daIndex)
    assert iResult is None


def test_fi_match_body_and_finit_index_no_finit_match():
    """If the finit qualifier never appears at the candidate indices, None is returned."""
    daBody = np.array(["planet", "planet"])
    daFinit = np.array(["initial", "initial"])
    daIndex = np.array([0, 1])
    iResult = fiMatchBodyAndFinitIndex(daBody, daFinit, "planet", "final", daIndex)
    assert iResult is None


def test_fi_match_body_and_finit_index_picks_aligned_pair():
    """Multiple body and finit matches resolve to the slot where both align."""
    daBody = np.array(["planet", "planet", "planet"])
    daFinit = np.array(["initial", "final", "initial"])
    daIndex = np.array([0, 1, 2])
    iResult = fiMatchBodyAndFinitIndex(daBody, daFinit, "planet", "final", daIndex)
    assert iResult == 1


def test_fi_match_body_and_finit_index_unaligned_returns_none():
    """When body and finit each appear but never at the same slot, None is returned."""
    daBody = np.array(["planet", "star"])
    daFinit = np.array(["initial", "final"])
    daIndex = np.array([0, 1])
    iResult = fiMatchBodyAndFinitIndex(daBody, daFinit, "planet", "final", daIndex)
    assert iResult is None
