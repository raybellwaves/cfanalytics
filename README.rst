cfanalytics: Downloading, analyzing and visualizing CrossFit data
=================================================================

.. image:: https://travis-ci.org/raybellwaves/cfanalytics.svg?branch=master
   :target: https://travis-ci.org/raybellwaves/cfanalytics
.. .. image:: https://ci.appveyor.com/api/projects/status/github/raybellwaves/cfanalytics?svg=true&passingText=passing&failingText=failing&pendingText=pending
..   :target: https://ci.appveyor.com/project/raybellwaves/cfanalytics
.. .. image:: https://coveralls.io/repos/github/raybellwaves/cfanalytics/badge.svg?branch=master
..   :target: https://coveralls.io/github/raybellwaves/cfanalytics?branch=master
.. image:: https://img.shields.io/pypi/v/cfanalytics.svg
   :target: https://pypi.python.org/pypi/cfanalytics/
   
**cfanalytics** is an open source project and Python package that aims to provide analyzes to 
CrossFit® workouts. The goal is to enhance data-driven performance of athletes.

Installing
----------

``conda install -c conda-forge cfanalytics``

As a precautionary note it has been developed entirely on Mac OSX using Python installed with `anaconda <https://anaconda.org/anaconda/python>`__. Therefore, use in Windows and Linux at your 
own peril.

As good practice I recommend installing in a new enviroment:

.. parsed-literal:: 
 
    $ conda create -n cfa python=3.6
    $ source activate cfa
    $ conda install -c conda-forge cfanalytics

You can type ``source deactivate`` when finished. You can also check which environments you have created by typing ``conda info --envs``. 
To remove an environment type ``conda remove --name cfa --all``.

Examples
--------

See examples `here <https://github.com/raybellwaves/cfanalytics/tree/master/Examples>`__.

Acknowledgements
----------------

- Thanks to posts on `r/crossfit <https://www.reddit.com/r/crossfit/>`__. e.g. `here <https://www.reddit.com/r/crossfit/comments/5uikq8/2017_open_data_analysis/>`__, I worked out how to download data from the `CrossFit® open <https://games.crossfit.com/leaderboard/open/2017?division=1&region=0&scaled=0&sort=0&occupation=0&page=1>`__. 
- ``Cfopendata`` is a very minor adaptation from `captamericadevs/CFOpenData <https://github.com/captamericadevs/CFOpenData>`__. Who smartly developed code to download CrossFit® open data using `aiohttp <https://github.com/aio-libs/aiohttp>`__. 

Documentation
-------------

The documentation is hosted at http://cfanalytics.readthedocs.io/

Disclaimer
----------

This project is not affiliated with CrossFit, Inc.

