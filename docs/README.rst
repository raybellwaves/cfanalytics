cfanalytics 
-----------

Notes on generating the docs (in a new environment).

Install:

.. parsed-literal:: 

    $ conda install -c anaconda sphinx
    $ pip install sphinx-autobuild # as of 2/19/18 this can't be installed using conda (see https://github.com/conda-forge/sphinx-autobuild-feedstock/issues/3)
    $ conda install -c anaconda sphinx_rtd_theme
    $ conda install -c anaconda ipython 
    $ conda install -c anaconda pytest
    $ mkdir docs
    $ cd docs
    $ sphinx-quickstart
    $ make html # This will generate an index.rst and a conf.py
    $ sphinx-apidoc -o . ../cfanalytics ???
    $ sphinx-autobuild . _build/html # To update
    # sphinx-build -b html . _build/html # is what readthedocs runs
    

Push changes.

Sign up for readthedocs and import your package.

