cfanalytics 
-----------

Create a new environment to create the examples
    $ conda create -n cfa_eg python=3.6
    $ source activate cfa_eg
    $ conda install -c matplotlib cartopy joblib netcdf4
    $ conda install spyder jupyter
    $ pip install motionless
    $ pip install git+https://github.com/fmaussion/salem.git
    $ pip install git+https://github.com/raybellwaves/cfanalytics

To generate/run these examples type `jupyter notebook`. Ensure you run this outside of a folder with `cfanalytics` as it will have conflicts in picking up the package.
I am generating these in `GitHub_folder_examples`
To reset the cell numbers type `Kernel > Restart` then `Cell > Run All`.