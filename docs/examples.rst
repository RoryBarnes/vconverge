Example Usage
=============

A complete worked example ships with the repository under ``Example/BasicTest``.
It contains a minimal ``vspace.in`` file, a ``vconverge.in`` file, and the
per-body ``VPLanet`` input files needed to reproduce a small convergence study.

To run the example:

.. code-block:: bash

    cd Example/BasicTest
    vconverge vconverge.in

The run will iteratively invoke ``vspace`` and ``multiplanet`` until the
monitored output distributions converge within the tolerance specified in
``vconverge.in``.
