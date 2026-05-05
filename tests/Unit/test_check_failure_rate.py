"""Unit tests for fnCheckFailureRate."""

import pytest

from vconverge.vconverge import fnCheckFailureRate


def test_zero_total_raises():
    """When success+failure==0 the function raises IOError."""
    with pytest.raises(IOError, match="No simulations"):
        fnCheckFailureRate(0, 0, "initial run")


def test_more_than_half_failed_raises():
    """When more than 50% of sims fail the function raises IOError."""
    with pytest.raises(IOError, match="More than 50%"):
        fnCheckFailureRate(2, 8, "step 1")


def test_exactly_half_failed_does_not_raise(capsys):
    """At exactly the 50% boundary the function only prints a summary."""
    fnCheckFailureRate(5, 5, "step 2")
    sCaptured = capsys.readouterr().out
    assert "step 2" in sCaptured
    assert "5 succeeded" in sCaptured


def test_low_failure_rate_prints_summary(capsys):
    """Below the 50% threshold the function prints a tally line."""
    fnCheckFailureRate(95, 5, "initial run")
    sCaptured = capsys.readouterr().out
    assert "95 succeeded" in sCaptured
    assert "5 failed" in sCaptured
