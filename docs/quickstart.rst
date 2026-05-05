QuickStart Guide
================

Install ``VCONVERGE`` from a local clone:

.. code-block:: bash

    git clone https://github.com/mgialluca/vconverge.git
    cd vconverge
    python -m pip install -e .

``VCONVERGE`` depends on ``vplanet``, ``vspace``, ``multiplanet``, and
``bigplanet``; ``pip`` will install these from PyPI automatically.

Run a convergence study by pointing ``vconverge`` at a ``.in`` configuration file:

.. code-block:: bash

    vconverge myStudy.in

The input file specifies the underlying ``vspace`` parameter sweep, the output
parameters to monitor, the convergence metric (e.g. KL divergence or
Kolmogorov-Smirnov), and the tolerance and step size for successive batches.
