cfanalytics 
-----------

Create a new environment to create the examples:

.. parsed-literal:: 

    $ conda create -n cfa_eg python=3.6
    $ source activate cfa_eg
    $ conda install -c matplotlib cartopy joblib netcdf4
    $ conda install spyder jupyter
    $ pip install motionless
    $ pip install git+https://github.com/fmaussion/salem.git
    $ pip install git+https://github.com/raybellwaves/cfanalytics

To generate/run these examples type `jupyter notebook`.
To reset the cell numbers type `Kernel > Restart` then `Cell > Run All`.