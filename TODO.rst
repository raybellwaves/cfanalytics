cfanalytics 
-----------

TODO list
=========

Code
----
- De-bug ``Cfopendata`` to see why it fails on certain pages.
- Work out why ``asyncio`` fails in ``ipython``.
- Write documentation for online and eventually run the examples in the docs.
- Write a ``nathletes`` utils for number of athelets and those who didn't enter a score.

Data
----
- Backfill data before 2017. Can then track an athlete's percentile over the years or a the maximum score/P50 for a repeated workout in various years.

Analysis/plotting
-----------------
- Create distribution plots of scores using `seaborn <https://seaborn.pydata.org/>`__ as ``Cfplot(df).distplot(column=‘18.1_score’)``. I'm guessing the results will look like a `Rayleigh <https://en.wikipedia.org/wiki/Rayleigh_distribution>`__ distribution.
- Create interactive plots of scores using `bokeh <https://bokeh.pydata.org/en/latest/>`__ / `holoviews <http://holoviews.org/>`__. Would be cool if could query for a person on the plot may not be possible.
- Create u/alexenos's `plot <https://www.reddit.com/r/crossfit/comments/88l9up/regional_competitiveness_for_qualifying_athletes/>`__.