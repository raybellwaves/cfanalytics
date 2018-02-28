cfanalytics 
-----------

TODO list
=========

Code
----
- In ``cfanalytics/core/cfopendata.py`` drop the ``batchpages`` input and calculate it in the code based on number of pages e.g. npages < 10 : batachpages = 2; npages >= 10 and npages < 100 : batachpages = 10; npages >= 100 : batchpages = 30.

Data
----
- Backfill data before 2017. Can then track an athlete's percentile over the years or a the maximum score/P50 for a repeated workout in various years.
- Download affliate list and work out how to convert address to lat-lon for spatial analysis.

Analysis/plotting
-----------------
- Create distribution plots of scores using seaborn `seaborn <https://seaborn.pydata.org/>`__. I'm guessing the results will look like a `Rayleigh <https://en.wikipedia.org/wiki/Rayleigh_distribution>`__ distribution.
- Create interactive plots of scores using `bokeh <https://bokeh.pydata.org/en/latest/>`__ / `holoviews <http://holoviews.org/>`__.
- Create spatial plots using `cartopy <http://scitools.org.uk/cartopy/docs/latest/index.html>`__.