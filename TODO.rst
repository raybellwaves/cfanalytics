cfanalytics 
-----------

TODO list
=========

Code
----
- Update ``Cfopendata`` example and create a ``Clean`` example. 
- Write documentation for online and eventually run the examples in the docs. 
- Refactor ``core/clean.py``.

Data
----
- Backfill data before 2017. Can then track an athlete's percentile over the years or a the maximum score/P50 for a repeated workout in various years.
- Download affliate list and work out how to convert address to lat-lon for spatial analysis.

Analysis/plotting
-----------------
- Create distribution plots of scores using `seaborn <https://seaborn.pydata.org/>`__. I'm guessing the results will look like a `Rayleigh <https://en.wikipedia.org/wiki/Rayleigh_distribution>`__ distribution.
- Create interactive plots of scores using `bokeh <https://bokeh.pydata.org/en/latest/>`__ / `holoviews <http://holoviews.org/>`__. Would be cool if could query for a person on the plot may not be possible.
- Create spatial plots using `cartopy <http://scitools.org.uk/cartopy/docs/latest/index.html>`__. Can group the data by region (possibly using `regionmask <http://regionmask.readthedocs.io/en/stable/index.html>`__).
- Create interactive spatial plots using `geoviews <http://geo.holoviews.org/>`__. This may allow you to zoom in on individual gyms. Or do some fancy shit and plot the data on Google Earth. 
- Check out ``xarray``'s `API <https://github.com/pydata/xarray/tree/0d69bf9dbf281f0f0f48ac2fadda61a82533aac3/xarray/plot>`__ (and `docs <http://xarray.pydata.org/en/stable/plotting.html>`__) for how to code the plots. Could create a ``cfplot.py`` and use it as ``Cfplot(df).distplot(column=‘18.1_score’)`` and ``Cfplot(df).regionplot(column=‘18.1_score’, how=‘p95’)``???
