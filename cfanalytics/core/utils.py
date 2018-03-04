import xarray as xr


def open_wods(year):
    """Information about the Open workouts for each year.
    See https://games.crossfit.com/workouts/open/2018/2
    
    Parameters
    ----------
    year : int
        Year to download crossfit data e.g. 2017.
        
    Returns
    -------
    open_wods : xr.Dataset
        Information about the open work out.
    """
    ds = xr.Dataset()
    _yr = str(year)[2:]
    
    if year == 2017:
        wodscompleted = 5
        units = ['time/reps', 'reps', 'time/reps', 'reps', 'time/reps']
        predictions = [True, False, True, False, True]
        dfheader = [_yr+'.1 Rank', _yr+'.1 Score', _yr+'.2 Rank',
                    _yr+'.2 Score', _yr+'.3 Rank', _yr+'.3 Score',
                    _yr+'.4 Rank', _yr+'.4 Score', _yr+'.5 Rank',
                    _yr+'.5 Score']
    else:
        wodscompleted = 3
        units = ['reps', 'time/reps', 'weight']        
        predictions = [False, True, False]
        dfheader = [_yr+'.1 Rank', _yr+'.1 Score', _yr+'.2 Rank',
                    _yr+'.2 Score', _yr+'.2a Rank', _yr+'.2a Score']   
    ds['units'] = units
    ds['predictions'] = predictions
    ds['dfheader'] = dfheader
    ds['wodscompleted'] = wodscompleted
    return ds