"""Unit tests for create_tmp_prior_files."""

import json
import os
import textwrap

import numpy as np
import pytest
from astropy.io import ascii
from astropy.table import Table

from vconverge.vconverge import create_tmp_prior_files


def fnPrepareTmpDirectory(sChdirPath):
    """Make sure vconverge_tmp/ exists before the function writes to it."""
    sTmp = os.path.join(sChdirPath, "vconverge_tmp")
    if not os.path.isdir(sTmp):
        os.makedirs(sTmp)


def fnWritePriorIndiciesJson(sPath, dictPriors):
    """The source double-wraps the JSON: json.load then json.loads."""
    with open(sPath, "w") as fileHandle:
        json.dump(json.dumps(dictPriors), fileHandle)


def fnSaveNpyPrior(sPath, daRows):
    """Persist a 2D numpy prior file."""
    np.save(sPath, daRows)


def fnSaveTxtPrior(sPath, daRows):
    """Persist a 2-column txt prior file via astropy.ascii."""
    table = Table(rows=daRows, names=("a", "b"))
    ascii.write(table, sPath, format="fixed_width", delimiter=" ", overwrite=True)


def test_create_tmp_prior_files_npy_run_index_one(tmp_path, monkeypatch):
    """RunIndex==1 writes deleted-row .npy to vconverge_tmp/tmp_<name>."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sPriorPath = tmp_path / "mass_prior.npy"
    daRows = np.arange(20).reshape(10, 2).astype(float)
    fnSaveNpyPrior(str(sPriorPath), daRows)
    sJsonPath = tmp_path / "myTrialPriorIndicies.json"
    fnWritePriorIndiciesJson(str(sJsonPath), {str(sPriorPath): [0, 1, 2]})
    create_tmp_prior_files(1, "myTrial", str(tmp_path))
    daResult = np.load(tmp_path / "vconverge_tmp" / "tmp_mass_prior.npy")
    assert daResult.shape == (7, 2)
    assert np.array_equal(daResult, daRows[3:])


def test_create_tmp_prior_files_npy_run_index_greater_than_one(tmp_path, monkeypatch):
    """RunIndex>1 reads from Step_<n-1>/Step<n-1>_<trial>PriorIndicies.json and writes to vconverge_tmp/<name> (no tmp_ prefix)."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sPriorPath = tmp_path / "ecc_prior.npy"
    daRows = np.arange(12).reshape(6, 2).astype(float)
    fnSaveNpyPrior(str(sPriorPath), daRows)
    sStepDir = tmp_path / "Step_1"
    sStepDir.mkdir()
    sJsonPath = sStepDir / "Step1_myTrialPriorIndicies.json"
    fnWritePriorIndiciesJson(str(sJsonPath), {str(sPriorPath): [4, 5]})
    create_tmp_prior_files(2, "myTrial", str(tmp_path))
    daResult = np.load(tmp_path / "vconverge_tmp" / "ecc_prior.npy")
    assert daResult.shape == (4, 2)
    assert np.array_equal(daResult, daRows[:4])


def test_create_tmp_prior_files_txt_run_index_one(tmp_path, monkeypatch):
    """RunIndex==1 with a .txt prior writes a tmp_<name> txt with rows removed."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sPriorPath = tmp_path / "mass.txt"
    daRows = [(float(i), float(i + 1)) for i in range(5)]
    fnSaveTxtPrior(str(sPriorPath), daRows)
    sJsonPath = tmp_path / "trialPriorIndicies.json"
    fnWritePriorIndiciesJson(str(sJsonPath), {str(sPriorPath): [0, 4]})
    create_tmp_prior_files(1, "trial", str(tmp_path))
    sResultPath = tmp_path / "vconverge_tmp" / "tmp_mass.txt"
    assert sResultPath.exists()
    tableResult = ascii.read(str(sResultPath))
    assert len(tableResult) == 3


def test_create_tmp_prior_files_txt_run_index_greater_than_one(tmp_path, monkeypatch):
    """RunIndex>1 with a .txt prior writes vconverge_tmp/<name> (no tmp_ prefix)."""
    monkeypatch.chdir(tmp_path)
    fnPrepareTmpDirectory(str(tmp_path))
    sPriorPath = tmp_path / "ecc.txt"
    daRows = [(float(i), float(i * 2)) for i in range(6)]
    fnSaveTxtPrior(str(sPriorPath), daRows)
    sStepDir = tmp_path / "Step_2"
    sStepDir.mkdir()
    sJsonPath = sStepDir / "Step2_trialPriorIndicies.json"
    fnWritePriorIndiciesJson(str(sJsonPath), {str(sPriorPath): [1, 3]})
    create_tmp_prior_files(3, "trial", str(tmp_path))
    sResultPath = tmp_path / "vconverge_tmp" / "ecc.txt"
    assert sResultPath.exists()
    tableResult = ascii.read(str(sResultPath))
    assert len(tableResult) == 4
