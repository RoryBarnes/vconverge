VCONVERGE Documentation
=======================
``VCONVERGE`` derives posterior distributions for ``VPLanet`` output parameters that
are not directly constrained by observational likelihoods. It performs successive
batches of ``VPLanet`` simulations, driven by ``vspace`` and ``multiplanet``, and
stops once the user-defined output distributions have converged within a specified
tolerance.

.. toctree::
   :maxdepth: 1

   quickstart
   examples
   GitHub <https://github.com/mgialluca/vconverge>

.. note::

    ``VCONVERGE`` complements `alabi <https://github.com/jbirky/alabi>`_:
    ``alabi`` infers posteriors over likelihood-constrained parameters, while
    ``vconverge`` produces posteriors over the remaining output quantities by
    forward simulation.
